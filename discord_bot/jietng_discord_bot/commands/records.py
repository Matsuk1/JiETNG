from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import discord
from discord import app_commands

from ..i18n import interaction_lang, tr
from .support import (
    AchievementLevel,
    AchievementRank,
    ExportFormat,
    FilterMode,
    attachment,
    localized_description,
    resolve_user_id,
    safe_filename_part,
)

if TYPE_CHECKING:
    from ..bot import JiETNGDiscordBot


RECORD_COMMANDS = (
    "b50",
    "b40",
    "b35",
    "b15",
    "ab35",
    "ab50",
    "ap50",
    "fdx50",
    "r50",
    "idlb50",
    "unknown",
)


def register_record_commands(bot: JiETNGDiscordBot) -> None:
    for command_name in RECORD_COMMANDS:
        _register_record_image_command(bot, command_name)

    @bot.tree.command(
        name="achievement",
        description=localized_description("cmd.achievement.desc"),
    )
    @app_commands.describe(
        level=localized_description("param.level"),
        rank=localized_description("param.rank"),
        filter_mode=localized_description("param.filter_mode"),
    )
    async def achievement(
        interaction: discord.Interaction,
        level: AchievementLevel,
        rank: Optional[AchievementRank] = None,
        filter_mode: Optional[FilterMode] = None,
    ) -> None:
        await interaction.response.defer(thinking=True)
        user_id = resolve_user_id(bot, interaction)
        image = await bot.jietng.images.achievement(
            user_id,
            level=level,
            rank=rank,
            filter_mode=filter_mode,
        )
        suffix = rank or "list"
        filename = (
            f"jietng-{safe_filename_part(user_id)}-"
            f"lv{safe_filename_part(level)}-{safe_filename_part(suffix)}.png"
        )
        await interaction.followup.send(file=attachment(image, filename))

    @bot.tree.command(name="plate", description=localized_description("cmd.plate.desc"))
    @app_commands.describe(
        title=localized_description("param.title"),
        filter_mode=localized_description("param.filter_mode"),
    )
    async def plate(
        interaction: discord.Interaction,
        title: str,
        filter_mode: Optional[FilterMode] = None,
    ) -> None:
        await interaction.response.defer(thinking=True)
        user_id = resolve_user_id(bot, interaction)
        title = title.strip()
        image = await bot.jietng.images.plate(
            user_id,
            title=title,
            filter_mode=filter_mode,
        )
        filename = (
            f"jietng-{safe_filename_part(user_id)}-"
            f"plate-{safe_filename_part(title)}.png"
        )
        await interaction.followup.send(file=attachment(image, filename))

    @bot.tree.command(name="export", description=localized_description("cmd.export.desc"))
    @app_commands.describe(format=localized_description("param.format"))
    async def export_records(
        interaction: discord.Interaction,
        format: ExportFormat = "json",
    ) -> None:
        lang = interaction_lang(interaction)
        await interaction.response.defer(thinking=True, ephemeral=True)
        user_id = resolve_user_id(bot, interaction)
        content, filename = await bot.jietng.exports.download(user_id, fmt=format)
        filename = filename or f"jietng-{safe_filename_part(user_id)}-records.{format}"
        await interaction.followup.send(
            tr(lang, "export_done"),
            file=attachment(content, filename),
            ephemeral=True,
        )


def _register_record_image_command(
    bot: JiETNGDiscordBot,
    command_name: str,
) -> None:
    async def send_record_image(
        interaction: discord.Interaction,
        command: Optional[str] = None,
    ) -> None:
        await interaction.response.defer(thinking=True)
        user_id = resolve_user_id(bot, interaction)
        api_command = command_name
        if command and command.strip():
            api_command = f"{command_name} {command.strip()}"
        image = await bot.jietng.images.records(user_id, command=api_command)
        filename = f"jietng-{safe_filename_part(user_id)}-{command_name}.png"
        await interaction.followup.send(file=attachment(image, filename))

    send_record_image.__name__ = command_name
    described_callback = app_commands.describe(
        command=localized_description("param.command")
    )(send_record_image)
    bot.tree.command(
        name=command_name,
        description=localized_description(f"cmd.{command_name}.desc"),
    )(described_callback)
