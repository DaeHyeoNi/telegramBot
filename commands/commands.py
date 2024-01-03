import logging
from typing import List

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application
from telegram.ext import CommandHandler as _CommandHandler
from telegram.ext import ContextTypes


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

    def set_command(self, command: str, func, /, help_text: List[str] = None):
        if command not in self.except_commands:
            logging.info(f"Setting command: {command}")
            self.app.add_handler(_CommandHandler(command, func))
            if help_text:
                assert isinstance(help_text, list), "helps must be list"
                self.help_list.extend(help_text)

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        escaped_help_list = [
            item.replace("(", "\\(").replace(")", "\\)").replace("=", "\\=")
            for item in self.help_list
        ]
        text = "\n".join(escaped_help_list)
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN_V2)
