from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from jietng import APIError

from ..i18n import interaction_lang
from .account import register_account_commands
from .records import register_record_commands
from .songs import register_song_commands
from .support import display_error

if TYPE_CHECKING:
    from ..bot import JiETNGDiscordBot


logger = logging.getLogger("jietng_discord_bot")


def register_commands(bot: JiETNGDiscordBot) -> None:
    register_error_handler(bot)
    register_account_commands(bot)
    register_record_commands(bot)
    register_song_commands(bot)


def register_error_handler(bot: JiETNGDiscordBot) -> None:
    @bot.tree.error
    async def on_app_command_error(
        interaction: discord.Interaction,
        error: app_commands.AppCommandError,
    ) -> None:
        lang = interaction_lang(interaction)
        if isinstance(error, app_commands.CommandInvokeError):
            original = error.original
            if isinstance(original, APIError):
                content = display_error(original, lang)
            else:
                logger.error(
                    "Command failed",
                    exc_info=(type(original), original, original.__traceback__),
                )
                content = str(original)
        else:
            content = str(error)

        if interaction.response.is_done():
            await interaction.followup.send(content, ephemeral=True)
        else:
            await interaction.response.send_message(content, ephemeral=True)
