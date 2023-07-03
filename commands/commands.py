import logging
import re
from typing import List

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, ContextTypes
from telegram.ext import CommandHandler as _CommandHandler


class CommandHandler:
    def __init__(self, app: Application, config):
        self.app = app
        self.config = config
        self.except_commands: List[str] = []
        self.help_list: List[str] = []

        if self.config["telegram"]["except_commands"]:
            self.except_commands = self.config["telegram"]["except_commands"].split(",")

    def create_help_message(self, command: str, description: str):
        return f"/{command} : {description}"

    def set_command(self, command: str, func, helps: List[str] = None):
        if command not in self.except_commands:
            logging.info(f"Setting command: {command}")
            self.app.add_handler(_CommandHandler(command, func))
            if helps:
                assert isinstance(helps, list), "helps must be list"
                self.help_list.extend(helps)


class SimpleCommands:
    async def _help(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, help_list: List[str]
    ):
        escaped_help_list = [re.escape(item) for item in help_list]
        text = "\n".join(escaped_help_list)
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN_V2)

    async def _ping(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("pong")
