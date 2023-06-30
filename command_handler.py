import logging
import re
from functools import partial
from typing import List

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, ContextTypes
from telegram.ext import CommandHandler as _CommandHandler

from commands import fear_and_greed_index
from commands.stock import currency, korean_market_point, stock
from commands.stock.common import Country


ADD_HELP_BLANK_LINE = ""


class CommandHandler:
    def __init__(self, app: Application, config):
        self.app = app
        self.config = config
        self.except_commands: List[str] = []
        self.help_list: List[str] = []

    def set_command(self, command: str, func, helps: List[str] = None):
        if command not in self.except_commands:
            logging.info(f"Setting command: {command}")
            self.app.add_handler(_CommandHandler(command, func))
            if helps:
                assert isinstance(helps, list), "helps must be list"
                self.help_list.extend(helps)

    def create_help_message(self, command: str, description: str):
        return f"/{command} : {description}"

    def run(self):
        if self.config["telegram"]["except_commands"]:
            self.except_commands = self.config["telegram"]["except_commands"].split(",")

        simple_commands = SimpleCommands()

        self.set_command(
            "help", partial(simple_commands._help, help_list=self.help_list)
        )
        self.set_command(
            "ping",
            simple_commands._ping,
            [self.create_help_message("ping", "상태 체크"), ADD_HELP_BLANK_LINE],
        )

        self.set_command(
            "kospi",
            stock.get_kospi_info,
            [
                self.create_help_message("kospi", "코스피 지수"),
                self.create_help_message("kospi (종목명)", "종목 정보"),
            ],
        )
        self.set_command("kosdaq", korean_market_point.get_kosdaq_point)

        self.set_command(
            "us",
            stock.get_usstock_info,
            [
                self.create_help_message(
                    "us (ticker)", "미국 주식 정보 (alias: us, ustock, nasdaq)"
                )
            ],
        )
        self.set_command("usstock", stock.get_usstock_info)
        self.set_command("nasdaq", stock.get_usstock_info)

        self.set_command("usd", partial(currency.get_currency_data, code=Country.USA), [self.create_help_message("usd", "미국 환율")])
        self.set_command("jpy", partial(currency.get_currency_data, code=Country.JAPAN), [self.create_help_message("jpy", "일본 환율")])

        self.set_command("fg", fear_and_greed_index)


class SimpleCommands:
    async def _help(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, help_list: List[str]
    ):
        escaped_help_list = [re.escape(item) for item in help_list]
        text = "\n".join(escaped_help_list)
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN_V2)

    async def _ping(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("pong")
