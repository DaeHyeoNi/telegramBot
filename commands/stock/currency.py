import time
from typing import Tuple

from telegram import Update
from telegram.ext import ContextTypes
from commands.request_wrapper import RequestWrapper

from commands.stock.common import Country


class Currency:
    FOREX_API_ENDPOINT = (
        "https://quotation-api-cdn.dunamu.com/v1/forex/recent?codes=FRX.KRW"
    )
    FOREX_CHART_ENDPOINT = "https://ssl.pstatic.net/imgfinance/chart/marketindex/area/month3/FX_{}KRW.png?ver={}"

    def fetch(self, code: Country) -> Tuple[float, str, int]:
        url = self.FOREX_API_ENDPOINT + code.value
        request_wrapper = RequestWrapper()
        response = request_wrapper.get(url)
        data = response.json()[0]
        return data["basePrice"], data["currencyName"], data["currencyUnit"]

    def create_photo_url(self, code: Country) -> str:
        return self.FOREX_CHART_ENDPOINT.format(code.value, int(time.time()))


async def get_currency_data(
    update: Update, context: ContextTypes.DEFAULT_TYPE, /, code: Country
):
    currency = Currency()
    base_price, currency_name, currency_unit = currency.fetch(code)

    if len(context.args) == 0:
        chat_message = f"{currency_unit}{currency_name}: {base_price}"
    else:
        amount = float(context.args[0])
        converted_price = amount / currency_unit * float(base_price)
        chat_message = f"{amount}{currency_name}: {converted_price:.2f}"

    chat_message += "원"
    await context.bot.send_photo(
        chat_id=update.message.chat_id,
        photo=currency.create_photo_url(code),
        caption=chat_message,
    )
