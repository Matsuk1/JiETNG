from __future__ import annotations

import asyncio
import logging
import re
from io import BytesIO
from typing import Literal, Optional

import discord
from discord import app_commands
from discord.ext import commands
from jietng import (
    APIError,
    AsyncjietngClient,
    AuthenticationError,
    NotFoundError,
    PermissionDeniedError,
    QueueFullError,
    RateLimitedError,
    ValidationError,
)

from .config import BotConfig, load_config
from .i18n import BotTranslator, COMMAND_TRANSLATIONS, interaction_lang, tr
from .storage import LinkStore


logger = logging.getLogger("jietng_discord_bot")

ServerVersion = Literal["jp", "intl"]
ExportFormat = Literal["json", "xml"]
FilterMode = Literal["uncleared", "unplayed", "cleared"]
AchievementLevel = Literal["11", "11+", "12", "12+", "13", "13+", "14", "14+", "15"]
AchievementRank = Literal[
    "s", "s+", "ss", "ss+", "sss", "sss+", "fc", "fc+", "ap", "ap+", "fdx", "fdx+",
]


def _ls(key: str) -> app_commands.locale_str:
    return app_commands.locale_str(COMMAND_TRANSLATIONS[key]["en"], key=key)


def _discord_default_user_id(discord_user_id: int) -> str:
    return f"discord_{discord_user_id}"


class JiETNGDiscordBot(commands.Bot):
    def __init__(self, config: BotConfig):
        intents = discord.Intents.default()
        super().__init__(command_prefix=commands.when_mentioned, intents=intents)
        self.config = config
        self.links = LinkStore(config.db_path)
        self.jietng = AsyncjietngClient(
            token=config.jietng_token,
            base_url=config.jietng_base_url,
            extra_headers={"X-App-Name": "jietng-discord-bot"},
        )

    async def setup_hook(self) -> None:
        await self.tree.set_translator(BotTranslator())
        register_commands(self)
        if self.config.guild_id:
            guild = discord.Object(id=self.config.guild_id)
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            logger.info("Synced %s guild commands to %s", len(synced), self.config.guild_id)
        else:
            synced = await self.tree.sync()
            logger.info("Synced %s global commands", len(synced))

    async def close(self) -> None:
        await self.jietng.close()
        await super().close()

    async def on_ready(self) -> None:
        assert self.user is not None
        logger.info("Logged in as %s (%s)", self.user, self.user.id)


def _display_error(exc: APIError, lang: str = "zh") -> str:
    message = exc.message or exc.error or str(exc)
    if isinstance(exc, AuthenticationError):
        return tr(lang, "api_token_invalid")
    if isinstance(exc, PermissionDeniedError):
        return tr(lang, "permission_denied")
    if isinstance(exc, NotFoundError):
        return tr(lang, "not_found", message=message)
    if isinstance(exc, ValidationError):
        return tr(lang, "bad_params", message=message)
    if isinstance(exc, RateLimitedError):
        return tr(lang, "rate_limited")
    if isinstance(exc, QueueFullError):
        return tr(lang, "queue_full")
    if exc.status_code == 409:
        return tr(lang, "already_bound")
    return tr(lang, "api_error", message=message)


def _resolve_user_id(bot: JiETNGDiscordBot, interaction: discord.Interaction, user_id: Optional[str]) -> str:
    lang = interaction_lang(interaction)
    linked = bot.links.get_link(interaction.user.id)
    if user_id:
        target = user_id.strip()
        if linked == target:
            return target
        if linked:
            raise app_commands.AppCommandError(tr(lang, "self_only"))
        raise app_commands.AppCommandError(tr(lang, "need_link"))
    if linked:
        return linked
    raise app_commands.AppCommandError(tr(lang, "need_link"))


def _png_file(data: bytes, filename: str) -> discord.File:
    return discord.File(BytesIO(data), filename=filename)


def _data_file(data: bytes, filename: str) -> discord.File:
    return discord.File(BytesIO(data), filename=filename)


def _safe_filename_part(value: str) -> str:
    value = re.sub(r"[^\w.+-]+", "_", value.strip())
    return value.strip("._") or "file"


def _profile_summary(payload: dict, lang: str) -> str:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    personal = data.get("personal_info") or {}
    name = payload.get("nickname") or personal.get("name") or personal.get("userName") or "(unknown)"
    rating = personal.get("rating") or personal.get("playerRating") or "?"
    version = data.get("version") or "?"
    updated_at = data.get("updated_at") or data.get("last_sync") or data.get("last_update") or "?"
    return "\n".join([
        f"{tr(lang, 'profile_user_id')}：`{payload.get('user_id', '?')}`",
        f"{tr(lang, 'profile_name')}：`{name}`",
        f"{tr(lang, 'profile_rating')}：`{rating}`",
        f"{tr(lang, 'profile_version')}：`{version}`",
        f"{tr(lang, 'profile_updated')}：`{updated_at}`",
    ])


def _has_bound_account(payload: dict) -> bool:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    personal = data.get("personal_info")
    return isinstance(personal, dict) and bool(personal)


def _song_search_summary(payload: dict, lang: str) -> str:
    songs = payload.get("songs") or []
    if not songs:
        return tr(lang, "no_song")
    lines = []
    for song in songs:
        title = song.get("title") or "(untitled)"
        song_id = song.get("id") or "?"
        song_type = song.get("type") or "?"
        version = song.get("version") or "?"
        lines.append(f"`{song_id}`  **{title}**  `{song_type}` `{version}`")
    return "\n".join(lines)


def _button_label(text: str, fallback: str = "Select") -> str:
    text = (text or fallback).strip()
    return text if len(text) <= 80 else text[:77] + "..."


def _url_view(label: str, url: object) -> discord.ui.View:
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label=label, url=str(url)))
    return view


class SongChoiceButton(discord.ui.Button):
    def __init__(
        self,
        bot: JiETNGDiscordBot,
        song: dict,
        *,
        mode: str,
        owner_id: Optional[int],
        user_id: Optional[str] = None,
        row: Optional[int] = None,
    ):
        title = song.get("title") or song.get("id") or "Song"
        super().__init__(
            label=_button_label(title),
            style=discord.ButtonStyle.secondary,
            row=row,
        )
        self.bot = bot
        self.song = song
        self.mode = mode
        self.owner_id = owner_id
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction) -> None:
        lang = interaction_lang(interaction)
        is_private = self.mode == "record"
        if self.owner_id is not None and interaction.user.id != self.owner_id:
            await interaction.response.send_message(tr(lang, "button_not_for_you"), ephemeral=True)
            return

        await interaction.response.defer(thinking=True, ephemeral=is_private)
        song_id = str(self.song.get("id") or "").strip()
        if not song_id:
            await interaction.followup.send(tr(lang, "missing_song_id"), ephemeral=True)
            return

        try:
            if self.mode == "record":
                if not self.user_id:
                    await interaction.followup.send(tr(lang, "missing_user_id"), ephemeral=True)
                    return
                image = await self.bot.jietng.images.user_song(self.user_id, song_id)
                filename = f"jietng-{_safe_filename_part(self.user_id)}-song-{_safe_filename_part(song_id)}.png"
            else:
                image = await self.bot.jietng.songs.info(song_id)
                filename = f"jietng-song-{_safe_filename_part(song_id)}.png"
        except APIError as exc:
            await interaction.followup.send(_display_error(exc, lang), ephemeral=True)
            return

        await interaction.followup.send(file=_png_file(image, filename), ephemeral=is_private)


class SongChoiceView(discord.ui.View):
    def __init__(
        self,
        bot: JiETNGDiscordBot,
        songs: list,
        *,
        mode: str,
        owner_id: Optional[int],
        user_id: Optional[str] = None,
    ):
        super().__init__(timeout=180)
        for index, song in enumerate(songs[:10]):
            self.add_item(
                SongChoiceButton(
                    bot,
                    song,
                    mode=mode,
                    owner_id=owner_id,
                    user_id=user_id,
                    row=index // 5,
                )
            )


def _requester_name(interaction: discord.Interaction) -> str:
    user = interaction.user
    display_name = getattr(user, "display_name", None) or getattr(user, "global_name", None)
    return f"Discord: {display_name or user.name} ({user.id})"


def _must_not_have_link(bot: JiETNGDiscordBot, interaction: discord.Interaction, user_id: str) -> None:
    lang = interaction_lang(interaction)
    record = bot.links.get_record(interaction.user.id)
    if not record:
        return
    if record.mode == "bind":
        raise app_commands.AppCommandError(tr(lang, "already_has_discord_bind", linked=record.jietng_user_id))
    if record.jietng_user_id != user_id:
        raise app_commands.AppCommandError(tr(lang, "already_has_external_link", linked=record.jietng_user_id))


async def _watch_binding_completion(
    bot: JiETNGDiscordBot,
    interaction: discord.Interaction,
    user_id: str,
    *,
    timeout: float = 180.0,
    interval: float = 5.0,
) -> None:
    deadline = asyncio.get_running_loop().time() + timeout
    while asyncio.get_running_loop().time() < deadline:
        await asyncio.sleep(interval)
        try:
            payload = await bot.jietng.users.get(user_id)
        except APIError as exc:
            logger.debug("Binding watch skipped: user_id=%s error=%s", user_id, exc)
            continue
        if not _has_bound_account(payload):
            continue

        try:
            await interaction.followup.send(
                tr(interaction_lang(interaction), "binding_done", user_id=user_id),
                ephemeral=True,
            )
        except Exception:
            logger.debug("Binding completion followup failed: user_id=%s", user_id, exc_info=True)
        return


def _start_binding_watch(bot: JiETNGDiscordBot, interaction: discord.Interaction, user_id: str) -> None:
    task = asyncio.create_task(_watch_binding_completion(bot, interaction, user_id))

    def _log_failure(done: asyncio.Task) -> None:
        try:
            done.result()
        except Exception:
            logger.exception("Binding watch task failed: user_id=%s", user_id)

    task.add_done_callback(_log_failure)


async def _send_record_image(
    bot: JiETNGDiscordBot,
    interaction: discord.Interaction,
    record_command: str,
    command: Optional[str] = None,
) -> None:
    await interaction.response.defer(thinking=True)
    resolved = _resolve_user_id(bot, interaction, None)
    api_command = record_command
    if command and command.strip():
        api_command = f"{record_command} {command.strip()}"
    image = await bot.jietng.images.records(resolved, command=api_command)
    await interaction.followup.send(
        file=_png_file(image, f"jietng-{_safe_filename_part(resolved)}-{record_command}.png"),
    )


def register_commands(bot: JiETNGDiscordBot) -> None:
    @bot.tree.error
    async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
        lang = interaction_lang(interaction)
        if isinstance(error, app_commands.CommandInvokeError):
            original = error.original
            if isinstance(original, APIError):
                content = _display_error(original, lang)
            else:
                logger.exception("Command failed", exc_info=original)
                content = str(original)
        else:
            content = str(error)

        if interaction.response.is_done():
            await interaction.followup.send(content, ephemeral=True)
        else:
            await interaction.response.send_message(content, ephemeral=True)

    @bot.tree.command(name="link", description=_ls("cmd.link.desc"))
    @app_commands.describe(user_id=_ls("param.user_id"))
    async def link(interaction: discord.Interaction, user_id: str) -> None:
        lang = interaction_lang(interaction)
        user_id = user_id.strip()
        _must_not_have_link(bot, interaction, user_id)
        current_link = bot.links.get_link(interaction.user.id)
        requester_name = _requester_name(interaction)

        try:
            payload = await bot.jietng.permissions.request(user_id, requester_name=requester_name)
        except ValidationError as exc:
            if exc.error == "Permission already granted":
                if current_link == user_id:
                    await interaction.response.send_message(
                        tr(lang, "linked_ready", user_id=user_id),
                        ephemeral=True,
                    )
                    return
                await interaction.response.send_message(
                    tr(lang, "global_permission_not_linked"),
                    ephemeral=True,
                )
                return
            if exc.error == "Request already sent":
                if current_link == user_id:
                    await interaction.response.send_message(
                        tr(lang, "request_pending_linked", user_id=user_id),
                        ephemeral=True,
                    )
                    return
                await interaction.response.send_message(
                    tr(lang, "request_pending_not_linked"),
                    ephemeral=True,
                )
                return
            raise

        bot.links.set_link(interaction.user.id, user_id)
        request_id = payload.get("request_id", "?")
        await interaction.response.send_message(
            tr(lang, "permission_requested", user_id=user_id, request_id=request_id),
            ephemeral=True,
        )

    @bot.tree.command(name="unlink", description=_ls("cmd.unlink.desc"))
    async def unlink(interaction: discord.Interaction) -> None:
        lang = interaction_lang(interaction)
        record = bot.links.get_record(interaction.user.id)
        if not record:
            await interaction.response.send_message(tr(lang, "not_linked"), ephemeral=True)
            return
        if record.mode != "link":
            await interaction.response.send_message(
                tr(lang, "unlink_requires_link_mode", user_id=record.jietng_user_id),
                ephemeral=True,
            )
            return

        revoke_error = None
        try:
            await bot.jietng.permissions.revoke_self(record.jietng_user_id)
        except APIError as exc:
            revoke_error = exc.message or exc.error or str(exc)

        bot.links.delete_link(interaction.user.id)
        message = (
            tr(lang, "unlinked")
            if revoke_error is None
            else tr(lang, "unlinked_local_only", message=revoke_error)
        )
        await interaction.response.send_message(message, ephemeral=True)

    @bot.tree.command(name="bind", description=_ls("cmd.bind.desc"))
    async def bind(interaction: discord.Interaction) -> None:
        lang = interaction_lang(interaction)
        record = bot.links.get_record(interaction.user.id)
        if record and record.mode == "link":
            await interaction.response.send_message(
                tr(lang, "bind_requires_no_link_mode", user_id=record.jietng_user_id),
                ephemeral=True,
            )
            return
        if record:
            payload = await bot.jietng.users.get_rebind_url(record.jietng_user_id)
            url = payload.get("rebind_url") or payload.get("url") or payload
            await interaction.response.send_message(
                tr(lang, "has_discord_bind", user_id=record.jietng_user_id),
                view=_url_view(tr(lang, "open_bind"), url),
                ephemeral=True,
            )
            return

        user_id = _discord_default_user_id(interaction.user.id)
        nickname = getattr(interaction.user, "display_name", None) or interaction.user.name
        try:
            payload = await bot.jietng.users.create(user_id=user_id, nickname=nickname)
        except APIError as exc:
            if exc.status_code == 409:
                raise app_commands.AppCommandError(
                    tr(lang, "default_user_conflict")
                ) from exc
            raise

        bot.links.set_link(interaction.user.id, user_id, mode="bind")
        url = payload.get("bind_url") or payload.get("url") or payload
        await interaction.response.send_message(
            tr(lang, "created_bind", user_id=user_id),
            view=_url_view(tr(lang, "open_bind"), url),
            ephemeral=True,
        )
        _start_binding_watch(bot, interaction, user_id)

    @bot.tree.command(name="unbind", description=_ls("cmd.unbind.desc"))
    async def unbind(interaction: discord.Interaction) -> None:
        lang = interaction_lang(interaction)
        record = bot.links.get_record(interaction.user.id)
        if not record:
            await interaction.response.send_message(tr(lang, "not_linked"), ephemeral=True)
            return
        if record.mode != "bind":
            await interaction.response.send_message(
                tr(lang, "unbind_requires_bind_mode", user_id=record.jietng_user_id),
                ephemeral=True,
            )
            return

        try:
            await bot.jietng.users.delete(record.jietng_user_id)
        except NotFoundError:
            bot.links.delete_link(interaction.user.id)
            await interaction.response.send_message(
                tr(lang, "unbound_local_only", user_id=record.jietng_user_id),
                ephemeral=True,
            )
            return

        bot.links.delete_link(interaction.user.id)
        await interaction.response.send_message(
            tr(lang, "unbound", user_id=record.jietng_user_id),
            ephemeral=True,
        )

    @bot.tree.command(name="profile", description=_ls("cmd.profile.desc"))
    async def profile(interaction: discord.Interaction) -> None:
        lang = interaction_lang(interaction)
        resolved = _resolve_user_id(bot, interaction, None)
        payload = await bot.jietng.users.get(resolved)
        await interaction.response.send_message(_profile_summary(payload, lang), ephemeral=True)

    @bot.tree.command(name="sync", description=_ls("cmd.sync.desc"))
    async def sync(interaction: discord.Interaction) -> None:
        lang = interaction_lang(interaction)
        await interaction.response.defer(thinking=True, ephemeral=True)
        resolved = _resolve_user_id(bot, interaction, None)
        final_event = None
        async for event in bot.jietng.users.sync_stream(resolved):
            final_event = event

        status = (final_event or {}).get("event", "failed")
        if status == "completed":
            text = tr(lang, "sync_done")
        else:
            message = (final_event or {}).get("message") or status
            text = tr(lang, "sync_result", result=message)
        await interaction.followup.send(text, ephemeral=True)

    @bot.tree.command(name="b50", description=_ls("cmd.b50.desc"))
    @app_commands.describe(command=_ls("param.command"))
    async def b50(interaction: discord.Interaction, command: Optional[str] = None) -> None:
        await _send_record_image(bot, interaction, "b50", command)

    @bot.tree.command(name="b40", description=_ls("cmd.b40.desc"))
    @app_commands.describe(command=_ls("param.command"))
    async def b40(interaction: discord.Interaction, command: Optional[str] = None) -> None:
        await _send_record_image(bot, interaction, "b40", command)

    @bot.tree.command(name="b35", description=_ls("cmd.b35.desc"))
    @app_commands.describe(command=_ls("param.command"))
    async def b35(interaction: discord.Interaction, command: Optional[str] = None) -> None:
        await _send_record_image(bot, interaction, "b35", command)

    @bot.tree.command(name="b15", description=_ls("cmd.b15.desc"))
    @app_commands.describe(command=_ls("param.command"))
    async def b15(interaction: discord.Interaction, command: Optional[str] = None) -> None:
        await _send_record_image(bot, interaction, "b15", command)

    @bot.tree.command(name="ab35", description=_ls("cmd.ab35.desc"))
    @app_commands.describe(command=_ls("param.command"))
    async def ab35(interaction: discord.Interaction, command: Optional[str] = None) -> None:
        await _send_record_image(bot, interaction, "ab35", command)

    @bot.tree.command(name="ab50", description=_ls("cmd.ab50.desc"))
    @app_commands.describe(command=_ls("param.command"))
    async def ab50(interaction: discord.Interaction, command: Optional[str] = None) -> None:
        await _send_record_image(bot, interaction, "ab50", command)

    @bot.tree.command(name="ap50", description=_ls("cmd.ap50.desc"))
    @app_commands.describe(command=_ls("param.command"))
    async def ap50(interaction: discord.Interaction, command: Optional[str] = None) -> None:
        await _send_record_image(bot, interaction, "ap50", command)

    @bot.tree.command(name="fdx50", description=_ls("cmd.fdx50.desc"))
    @app_commands.describe(command=_ls("param.command"))
    async def fdx50(interaction: discord.Interaction, command: Optional[str] = None) -> None:
        await _send_record_image(bot, interaction, "fdx50", command)

    @bot.tree.command(name="r50", description=_ls("cmd.r50.desc"))
    @app_commands.describe(command=_ls("param.command"))
    async def r50(interaction: discord.Interaction, command: Optional[str] = None) -> None:
        await _send_record_image(bot, interaction, "r50", command)

    @bot.tree.command(name="idlb50", description=_ls("cmd.idlb50.desc"))
    @app_commands.describe(command=_ls("param.command"))
    async def idlb50(interaction: discord.Interaction, command: Optional[str] = None) -> None:
        await _send_record_image(bot, interaction, "idlb50", command)

    @bot.tree.command(name="unknown", description=_ls("cmd.unknown.desc"))
    @app_commands.describe(command=_ls("param.command"))
    async def unknown(interaction: discord.Interaction, command: Optional[str] = None) -> None:
        await _send_record_image(bot, interaction, "unknown", command)

    @bot.tree.command(name="achievement", description=_ls("cmd.achievement.desc"))
    @app_commands.describe(
        level=_ls("param.level"),
        rank=_ls("param.rank"),
        filter_mode=_ls("param.filter_mode"),
    )
    async def achievement(
        interaction: discord.Interaction,
        level: AchievementLevel,
        rank: Optional[AchievementRank] = None,
        filter_mode: Optional[FilterMode] = None,
    ) -> None:
        await interaction.response.defer(thinking=True)
        resolved = _resolve_user_id(bot, interaction, None)
        image = await bot.jietng.images.achievement(
            resolved,
            level=level,
            rank=rank,
            filter_mode=filter_mode,
        )
        suffix = rank or "list"
        await interaction.followup.send(
            file=_png_file(
                image,
                f"jietng-{_safe_filename_part(resolved)}-lv{_safe_filename_part(level)}-{_safe_filename_part(suffix)}.png",
            ),
        )

    @bot.tree.command(name="plate", description=_ls("cmd.plate.desc"))
    @app_commands.describe(title=_ls("param.title"), filter_mode=_ls("param.filter_mode"))
    async def plate(
        interaction: discord.Interaction,
        title: str,
        filter_mode: Optional[FilterMode] = None,
    ) -> None:
        await interaction.response.defer(thinking=True)
        resolved = _resolve_user_id(bot, interaction, None)
        title = title.strip()
        image = await bot.jietng.images.plate(resolved, title=title, filter_mode=filter_mode)
        await interaction.followup.send(
            file=_png_file(
                image,
                f"jietng-{_safe_filename_part(resolved)}-plate-{_safe_filename_part(title)}.png",
            ),
        )

    @bot.tree.command(name="song", description=_ls("cmd.song.desc"))
    @app_commands.describe(query=_ls("param.query"), ver=_ls("param.ver"))
    async def song(interaction: discord.Interaction, query: str, ver: ServerVersion = "jp") -> None:
        lang = interaction_lang(interaction)
        payload = await bot.jietng.songs.search(query.strip(), ver=ver, max_results=6)
        songs = payload.get("songs") or []
        if len(songs) != 1:
            view = SongChoiceView(
                bot,
                songs,
                mode="song",
                owner_id=None,
            ) if songs else None
            await interaction.response.send_message(
                _song_search_summary(payload, lang),
                view=view,
                ephemeral=False,
            )
            return

        await interaction.response.defer(thinking=True)
        song_id = str(songs[0].get("id") or "").strip()
        if not song_id:
            await interaction.followup.send(tr(lang, "missing_song_id"), ephemeral=True)
            return
        image = await bot.jietng.songs.info(song_id)
        await interaction.followup.send(
            file=_png_file(image, f"jietng-song-{_safe_filename_part(song_id)}.png"),
        )

    @bot.tree.command(name="record", description=_ls("cmd.record.desc"))
    @app_commands.describe(query=_ls("param.query"), ver=_ls("param.ver"))
    async def record(
        interaction: discord.Interaction,
        query: str,
        ver: ServerVersion = "jp",
    ) -> None:
        lang = interaction_lang(interaction)
        payload = await bot.jietng.songs.search(query.strip(), ver=ver, max_results=6)
        songs = payload.get("songs") or []
        resolved = _resolve_user_id(bot, interaction, None)
        if len(songs) != 1:
            view = SongChoiceView(
                bot,
                songs,
                mode="record",
                owner_id=interaction.user.id,
                user_id=resolved,
            ) if songs else None
            await interaction.response.send_message(
                _song_search_summary(payload, lang),
                view=view,
                ephemeral=True,
            )
            return

        await interaction.response.defer(thinking=True)
        song_id = str(songs[0].get("id") or "").strip()
        if not song_id:
            await interaction.followup.send(tr(lang, "missing_song_id"), ephemeral=True)
            return
        image = await bot.jietng.images.user_song(resolved, song_id)
        await interaction.followup.send(
            file=_png_file(
                image,
                f"jietng-{_safe_filename_part(resolved)}-song-{_safe_filename_part(song_id)}.png",
            ),
        )

    @bot.tree.command(name="export", description=_ls("cmd.export.desc"))
    @app_commands.describe(format=_ls("param.format"))
    async def export(
        interaction: discord.Interaction,
        format: ExportFormat = "json",
    ) -> None:
        lang = interaction_lang(interaction)
        await interaction.response.defer(thinking=True, ephemeral=True)
        resolved = _resolve_user_id(bot, interaction, None)
        content, filename = await bot.jietng.exports.download(resolved, fmt=format)
        filename = filename or f"jietng-{_safe_filename_part(resolved)}-records.{format}"
        await interaction.followup.send(
            tr(lang, "export_done"),
            file=_data_file(content, filename),
            ephemeral=True,
        )

    @bot.tree.command(name="settings", description=_ls("cmd.settings.desc"))
    async def settings(interaction: discord.Interaction) -> None:
        lang = interaction_lang(interaction)
        resolved = _resolve_user_id(bot, interaction, None)
        payload = await bot.jietng.users.get_settings_url(resolved)
        url = payload.get("url") or payload.get("settings_url") or payload
        await interaction.response.send_message(
            tr(lang, "open_settings_prompt"),
            view=_url_view(tr(lang, "open_settings"), url),
            ephemeral=True,
        )

    @bot.tree.command(name="rebind", description=_ls("cmd.rebind.desc"))
    async def rebind(interaction: discord.Interaction) -> None:
        lang = interaction_lang(interaction)
        resolved = _resolve_user_id(bot, interaction, None)
        payload = await bot.jietng.users.get_rebind_url(resolved)
        url = payload.get("url") or payload.get("rebind_url") or payload
        await interaction.response.send_message(
            tr(lang, "open_rebind_prompt"),
            view=_url_view(tr(lang, "open_rebind"), url),
            ephemeral=True,
        )


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    config = load_config()
    bot = JiETNGDiscordBot(config)
    asyncio.run(bot.start(config.discord_token))
