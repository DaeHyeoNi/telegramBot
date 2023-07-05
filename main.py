import logging
from functools import partial

from commands.commands import CommandHandler, SimpleCommands
from commands.stock import currency, stock
from commands.stock.common import Country, KoreanMarketType
from config import build_application, get_configuration

ADD_HELP_BLANK_LINE = ""


def create_commands(command_handler: CommandHandler):
    simple_commands = SimpleCommands()

    command_handler.set_command(
        "help", partial(simple_commands._help, help_list=command_handler.help_list)
    )
    command_handler.set_command(
        "ping",
        simple_commands._ping,
        help_text=[
            command_handler.create_help_message("ping", "상태 체크"),
            ADD_HELP_BLANK_LINE,
        ],
    )

    command_handler.set_command(
        "kospi",
        stock.get_kospi_info,
        help_text=[
            "== 한국 시장 ==",
            command_handler.create_help_message("kospi", "코스피 지수"),
            command_handler.create_help_message("kospi (종목명)", "종목 정보"),
        ],
    )
    command_handler.set_command(
        "kosdaq",
        partial(stock.get_korea_market_point, type=KoreanMarketType.KOSDAQ),
        help_text=[command_handler.create_help_message("kosdaq", "코스닥 지수")],
    )

    command_handler.set_command(
        "us",
        stock.get_usstock_info,
        help_text=[
            ADD_HELP_BLANK_LINE,
            "== 미국 시장 ==",
            command_handler.create_help_message("us (ticker)", "미국 주식 정보"),
        ],
    )
    command_handler.set_command("usstock", stock.get_usstock_info)
    command_handler.set_command(
        "nasdaq",
        partial(stock.get_usstock_info, ticker="^IXIC"),
        help_text=[
            ADD_HELP_BLANK_LINE,
            command_handler.create_help_message("nasdaq", "나스닥 지수"),
        ],
    )
    command_handler.set_command(
        "dow",
        partial(stock.get_usstock_info, ticker="^DJI"),
        help_text=[command_handler.create_help_message("dow", "다우 지수")],
    )
    command_handler.set_command(
        "sp",
        partial(stock.get_usstock_info, ticker="^GSPC"),
        help_text=[command_handler.create_help_message("sp", "S&P 500 지수")],
    )
    command_handler.set_command(
        "vix",
        partial(stock.get_usstock_info, ticker="^VIX"),
        help_text=[command_handler.create_help_message("vix", "VIX 지수")],
    )
    command_handler.set_command(
        "gold",
        partial(stock.get_usstock_info, ticker="GC=F"),
        help_text=[command_handler.create_help_message("gold", "금값")],
    )
    command_handler.set_command(
        "btc",
        partial(stock.get_usstock_info, ticker="BTC-USD"),
        help_text=[command_handler.create_help_message("btc", "비트코인")],
    )
    command_handler.set_command(
        "fg",
        stock.fear_and_greed_index,
        help_text=[command_handler.create_help_message("fg", "Fear and Greed Index")],
    )

    command_handler.set_command(
        "usd",
        partial(currency.get_currency_data, code=Country.USA),
        help_text=[
            ADD_HELP_BLANK_LINE,
            "== 환율 ==",
            command_handler.create_help_message("usd", "미국 환율"),
        ],
    )
    command_handler.set_command(
        "jpy",
        partial(currency.get_currency_data, code=Country.JAPAN),
        help_text=[command_handler.create_help_message("jpy", "일본 환율")],
    )


if __name__ == "__main__":
    config = get_configuration()
    logging_level = config["telegram"].get("logging_level", "INFO")
    logging.basicConfig(level=logging._nameToLevel[logging_level])

    if app := build_application():
        command_handler = CommandHandler(app, config)
        create_commands(command_handler)

    app.run_polling()
