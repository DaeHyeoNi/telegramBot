from functools import partial
import logging
from commands.commands import CommandHandler, SimpleCommands
from commands.stock import currency, korean_market_point, stock
from commands.stock.common import Country
from commands.stock.fear_and_greed_index import fear_and_greed_index

from config import build_application, get_configuration


ADD_HELP_BLANK_LINE = ""

def _create_commands():
    command_handler = CommandHandler(app, get_configuration())
    simple_commands = SimpleCommands()

    command_handler.set_command(
        "help", partial(simple_commands._help, help_list=command_handler.help_list)
    )
    command_handler.set_command(
        "ping",
        simple_commands._ping,
        [command_handler.create_help_message("ping", "상태 체크"), ADD_HELP_BLANK_LINE],
    )

    command_handler.set_command(
        "kospi",
        stock.get_kospi_info,
        [
            command_handler.create_help_message("kospi", "코스피 지수"),
            command_handler.create_help_message("kospi (종목명)", "종목 정보"),
        ],
    )
    command_handler.set_command("kosdaq", korean_market_point.get_kosdaq_point)

    command_handler.set_command(
        "us",
        stock.get_usstock_info,
        [
            command_handler.create_help_message(
                "us (ticker)", "미국 주식 정보 (alias: us, ustock, nasdaq)"
            )
        ],
    )
    command_handler.set_command("usstock", stock.get_usstock_info)
    command_handler.set_command("nasdaq", stock.get_usstock_info)

    command_handler.set_command(
        "usd",
        partial(currency.get_currency_data, code=Country.USA),
        [command_handler.create_help_message("usd", "미국 환율")],
    )
    command_handler.set_command(
        "jpy",
        partial(currency.get_currency_data, code=Country.JAPAN),
        [command_handler.create_help_message("jpy", "일본 환율")],
    )

    command_handler.set_command(
        "fg",
        fear_and_greed_index,
        [command_handler.create_help_message("fg", "Fear and Greed Index")],
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    if app := build_application():
        _create_commands()

    app.run_polling()
