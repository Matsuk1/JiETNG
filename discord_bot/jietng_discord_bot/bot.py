from __future__ import annotations

import asyncio
import logging

import discord
from discord.ext import commands
from jietng import AsyncjietngClient

from .commands import register_commands
from .config import BotConfig, load_config
from .i18n import BotTranslator
from .storage import LinkStore


logger = logging.getLogger("jietng_discord_bot")


class JiETNGDiscordBot(commands.Bot):
    def __init__(self, config: BotConfig):
        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=discord.Intents.default(),
        )
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
            logger.info(
                "Synced %s guild commands to %s",
                len(synced),
                self.config.guild_id,
            )
            return

        synced = await self.tree.sync()
        logger.info("Synced %s global commands", len(synced))

    async def close(self) -> None:
        await self.jietng.close()
        await super().close()

    async def on_ready(self) -> None:
        assert self.user is not None
        logger.info("Logged in as %s (%s)", self.user, self.user.id)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    config = load_config()
    bot = JiETNGDiscordBot(config)
    asyncio.run(bot.start(config.discord_token))
