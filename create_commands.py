from functools import partial
from typing import Dict

from commands.commands import CommandHandler
from commands.ping import ping
from commands.stock import currency, stock
from commands.stock.common import Country, KoreanMarketType

commands: Dict[str, Dict] = {
    "ping": {"func": ping, "help": ["/ping: 상태 체크"]},
    "kospi": {
        "func": stock.get_kospi_info,
        "help": ["\n/kospi: 코스피 지수", "/kospi (종목명): 종목 정보"],
    },
    "kosdaq": {
        "func": partial(stock.get_korea_market_point, type=KoreanMarketType.KOSDAQ),
        "help": ["/kosdaq: 코스닥 지수"],
    },
    "us": {
        "func": stock.get_usstock_info,
        "help": ["\n/us (ticker): 미국 주식 정보"],
        "alias": ["usstock"],
    },
    "nasdaq": {
        "func": partial(stock.get_usstock_info, ticker="^IXIC"),
        "help": ["\n/nasdaq: 나스닥 지수"],
    },
    "dow": {
        "func": partial(stock.get_usstock_info, ticker="^DJI"),
        "help": ["/dow: 다우 지수"],
    },
    "sp": {
        "func": partial(stock.get_usstock_info, ticker="^GSPC"),
        "help": ["/sp: S&P 500 지수"],
    },
    "vix": {
        "func": partial(stock.get_usstock_info, ticker="^VIX"),
        "help": ["/vix: VIX 지수"],
    },
    "gold": {
        "func": partial(stock.get_usstock_info, ticker="GC=F"),
        "help": ["/gold: 금값"],
    },
    "btc": {
        "func": partial(stock.get_usstock_info, ticker="BTC-USD"),
        "help": ["/btc: 비트코인"],
    },
    "fg": {"func": stock.fear_and_greed_index, "help": ["\n/fg: Fear and Greed Index"]},
    "usd": {
        "func": partial(currency.get_currency_data, code=Country.USA),
        "help": ["\n/usd: 미국 환율"],
    },
    "jpy": {
        "func": partial(currency.get_currency_data, code=Country.JAPAN),
        "help": ["/jpy: 일본 환율"],
    },
}


def create_commands(command_handler: CommandHandler):
    command_handler.set_command("help", command_handler.help)

    for command, command_info in commands.items():
        command_handler.set_command(
            command, command_info["func"], help_text=command_info["help"]
        )
        if command_info.get("alias"):
            for alias in command_info["alias"]:
                command_handler.set_command(alias, command_info["func"])
