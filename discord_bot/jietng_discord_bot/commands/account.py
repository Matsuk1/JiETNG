from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import app_commands
from jietng import APIError, NotFoundError, ValidationError

from ..i18n import interaction_lang, tr
from .support import (
    ensure_link_available,
    localized_description,
    profile_summary,
    requester_name,
    resolve_user_id,
    start_binding_watch,
    url_view,
)

if TYPE_CHECKING:
    from ..bot import JiETNGDiscordBot


def register_account_commands(bot: JiETNGDiscordBot) -> None:
    @bot.tree.command(name="link", description=localized_description("cmd.link.desc"))
    @app_commands.describe(user_id=localized_description("param.user_id"))
    async def link(interaction: discord.Interaction, user_id: str) -> None:
        lang = interaction_lang(interaction)
        user_id = user_id.strip()
        ensure_link_available(bot, interaction, user_id)
        current_link = bot.links.get_link(interaction.user.id)

        try:
            payload = await bot.jietng.permissions.request(
                user_id,
                requester_name=requester_name(interaction),
            )
        except ValidationError as exc:
            response_key = _permission_request_error_key(exc, current_link == user_id)
            if response_key is None:
                raise
            await interaction.response.send_message(
                tr(lang, response_key, user_id=user_id),
                ephemeral=True,
            )
            return

        bot.links.set_link(interaction.user.id, user_id)
        await interaction.response.send_message(
            tr(
                lang,
                "permission_requested",
                user_id=user_id,
                request_id=payload.get("request_id", "?"),
            ),
            ephemeral=True,
        )

    @bot.tree.command(name="unlink", description=localized_description("cmd.unlink.desc"))
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

    @bot.tree.command(name="bind", description=localized_description("cmd.bind.desc"))
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
            await interaction.response.send_message(
                tr(lang, "has_discord_bind", user_id=record.jietng_user_id),
                view=url_view(tr(lang, "open_bind"), _response_url(payload, "rebind_url")),
                ephemeral=True,
            )
            return

        user_id = f"discord_{interaction.user.id}"
        nickname = getattr(interaction.user, "display_name", None) or interaction.user.name
        try:
            payload = await bot.jietng.users.create(user_id=user_id, nickname=nickname)
        except APIError as exc:
            if exc.status_code == 409:
                raise app_commands.AppCommandError(tr(lang, "default_user_conflict")) from exc
            raise

        bot.links.set_link(interaction.user.id, user_id, mode="bind")
        await interaction.response.send_message(
            tr(lang, "created_bind", user_id=user_id),
            view=url_view(tr(lang, "open_bind"), _response_url(payload, "bind_url")),
            ephemeral=True,
        )
        start_binding_watch(bot, interaction, user_id)

    @bot.tree.command(name="unbind", description=localized_description("cmd.unbind.desc"))
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
            response_key = "unbound_local_only"
        else:
            response_key = "unbound"

        bot.links.delete_link(interaction.user.id)
        await interaction.response.send_message(
            tr(lang, response_key, user_id=record.jietng_user_id),
            ephemeral=True,
        )

    @bot.tree.command(name="profile", description=localized_description("cmd.profile.desc"))
    async def profile(interaction: discord.Interaction) -> None:
        lang = interaction_lang(interaction)
        payload = await bot.jietng.users.get(resolve_user_id(bot, interaction))
        await interaction.response.send_message(profile_summary(payload, lang), ephemeral=True)

    @bot.tree.command(name="sync", description=localized_description("cmd.sync.desc"))
    async def sync(interaction: discord.Interaction) -> None:
        lang = interaction_lang(interaction)
        await interaction.response.defer(thinking=True, ephemeral=True)
        final_event = None
        async for event in bot.jietng.users.sync_stream(resolve_user_id(bot, interaction)):
            final_event = event

        status = (final_event or {}).get("event", "failed")
        text = (
            tr(lang, "sync_done")
            if status == "completed"
            else tr(lang, "sync_result", result=(final_event or {}).get("message") or status)
        )
        await interaction.followup.send(text, ephemeral=True)

    @bot.tree.command(name="settings", description=localized_description("cmd.settings.desc"))
    async def settings(interaction: discord.Interaction) -> None:
        lang = interaction_lang(interaction)
        payload = await bot.jietng.users.get_settings_url(resolve_user_id(bot, interaction))
        await interaction.response.send_message(
            tr(lang, "open_settings_prompt"),
            view=url_view(tr(lang, "open_settings"), _response_url(payload, "settings_url")),
            ephemeral=True,
        )

    @bot.tree.command(name="rebind", description=localized_description("cmd.rebind.desc"))
    async def rebind(interaction: discord.Interaction) -> None:
        lang = interaction_lang(interaction)
        payload = await bot.jietng.users.get_rebind_url(resolve_user_id(bot, interaction))
        await interaction.response.send_message(
            tr(lang, "open_rebind_prompt"),
            view=url_view(tr(lang, "open_rebind"), _response_url(payload, "rebind_url")),
            ephemeral=True,
        )


def _permission_request_error_key(exc: ValidationError, is_current_link: bool) -> str | None:
    if exc.error == "Permission already granted":
        return "linked_ready" if is_current_link else "global_permission_not_linked"
    if exc.error == "Request already sent":
        return "request_pending_linked" if is_current_link else "request_pending_not_linked"
    return None


def _response_url(payload: object, preferred_key: str) -> object:
    if isinstance(payload, dict):
        return payload.get(preferred_key) or payload.get("url") or payload
    return payload
