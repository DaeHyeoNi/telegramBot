import json
import logging

from telegram import Update
from telegram.ext import ContextTypes

from commands.request_wrapper import RequestWrapper

from .common import KoreanMarketEnum, KoreanMarketPoint


def get_korea_market_point_data(type: KoreanMarketEnum) -> KoreanMarketPoint:
    url = f"https://m.stock.naver.com/api/index/{type.value}/basic"
    request_wrapper = RequestWrapper()
    response = request_wrapper.get(url)
    resp = json.loads(response.text)

    data = KoreanMarketPoint(
        closePrice=resp["closePrice"],
        fluctuationsRatio=resp["fluctuationsRatio"] + "%",
        compareToPreviousClosePrice=resp["compareToPreviousClosePrice"],
    )

    return data


async def get_kospi_point(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(">>> 코스피포인트")
    text = get_korean_market_point(KoreanMarketEnum.KOSPI)
    await update.message.reply_text(text)


async def get_kosdaq_point(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(">>> 코스닥포인트")
    text = get_korean_market_point(KoreanMarketEnum.KOSDAQ)
    await update.message.reply_text(text)


def get_korean_market_point(type: KoreanMarketEnum):
    data = get_korea_market_point_data(type)
    text = f"현재: {data.closePrice} ({data.fluctuationsRatio}, {data.compareToPreviousClosePrice})"
    return text
