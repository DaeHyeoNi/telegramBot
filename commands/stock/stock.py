import json
import logging
import time
from concurrent.futures import ALL_COMPLETED, ThreadPoolExecutor, wait
from datetime import datetime
from typing import Optional, Tuple, Union

import requests
from telegram import Update
from telegram.ext import ContextTypes

from commands.stock.robinhood import RobinHood
import commands.stock.stock_data as stock_data
from commands.request_wrapper import RequestWrapper
from commands.stock.common import KoreanMarketType
from commands.stock.enums import ChartType

df_code = stock_data.create()

rh = RobinHood()
rh.load_data()


def get_stock_code(args: str):
    code = ""
    if args[0].isnumeric():
        code = args[0]
    else:
        try:
            stock_name = (
                " ".join(args[:-1]) if args[-1] in ["일봉", "주봉"] else " ".join(args)
            )
            code = str(df_code[stock_name][0])
            logging.info(">>> 코스피 종목 이름으로 " + code + " 반환")
        except:
            code = None
    return code


async def get_kospi_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await get_korea_market_point(
            update, context, type=KoreanMarketType.KOSPI
        )

    logging.info(">>> 코스피 종목 정보" + str(context.args))

    code = get_stock_code(context.args)
    if code is None:
        return await context.bot.send_message(
            chat_id=update.message.chat_id, text="종목 정보를 찾지 못했습니다."
        )

    url = "https://polling.finance.naver.com/api/realtime/domestic/stock/" + code
    request_wrapper = RequestWrapper()
    response = request_wrapper.get(url)
    data = json.loads(response.text)

    stock_name = data["datas"][0]["stockName"]
    close_price = data["datas"][0]["closePrice"]
    fluctuations_ratio = float(data["datas"][0]["fluctuationsRatio"])
    caption = f"종목명: {stock_name} / 현재: {close_price} ({fluctuations_ratio:.2f}%)"

    photo_type = context.args[-1]
    chart_photo_endpoint = "https://ssl.pstatic.net/imgfinance/chart/item/area/"
    if photo_type == "주봉":
        chart_photo_endpoint += "week/"
        caption += "\n주봉 차트입니다."
    else:
        chart_photo_endpoint += "day/"

    for retry_count in range(3):
        try:
            photo_url = f"{chart_photo_endpoint}{code}.png?ver={str(int(time.time()))}"
            return await context.bot.send_photo(
                chat_id=update.message.chat_id, photo=photo_url, caption=caption
            )
        except Exception:
            logging.error(f">>> 코스피 종목 정보 에러 {retry_count}회 재시도")
            time.sleep(1)
            continue


async def get_korea_market_point(
    update: Update, context: ContextTypes.DEFAULT_TYPE, type: KoreanMarketType
):
    url = f"https://m.stock.naver.com/api/index/{type.value}/basic"
    request_wrapper = RequestWrapper()
    response = request_wrapper.get(url)
    resp = json.loads(response.text)

    await context.bot.send_message(
        chat_id=update.message.chat_id,
        text=f'{type.name} 지수: {resp["closePrice"]} ({resp["compareToPreviousClosePrice"]} {resp["fluctuationsRatio"]}%)',
    )


def translate_market_desc(value):
    if value == "Overnight":
        return "데이마켓"
    elif value == "Pre-market":
        return "프리장"
    elif value == "Today":
        return "현재가"
    elif value == "After-hours":
        return "시간외"
    return value


def fetch_usstock_data(ticker: str, flat: bool = False) -> Tuple[str, str]:
    ticker = ticker.upper()
    data = rh.get_data(ticker)

    if not data:
        return "", "종목 정보를 찾지 못했습니다."

    company_name = f"{data['chart_section']['header'][0]['text']} ({ticker})"

    _display = data["chart_section"]["default_display"]

    primary_value = _display["primary_value"]["value"]
    trade_price = float(data["chart_section"]["quote"]["last_trade_price"])

    if data["chart_section"]["quote"]["last_extended_hours_trade_price"] is not None:
        trade_price = float(
            data["chart_section"]["quote"]["last_extended_hours_trade_price"]
        )

    previous_close_price = float(data["chart_section"]["quote"]["previous_close"])

    if secondary_value := _display.get("secondary_value"):
        secondary_value, secondary_value_desc = _display["secondary_value"]["main"][
            "value"
        ], translate_market_desc(_display["secondary_value"]["description"]["value"])
    if tertiary_value := _display.get("tertiary_value"):
        tertiary_value, tertiary_value_desc = _display["tertiary_value"]["main"][
            "value"
        ], translate_market_desc(_display["tertiary_value"]["description"]["value"])

    message = f"정규장: {trade_price}"
    if secondary_value:
        message = f"{secondary_value_desc}: {trade_price} {secondary_value}"
    if tertiary_value:
        message = f"{tertiary_value_desc}: {trade_price} {tertiary_value}"

    if flat:
        message = message.replace("\n", " ")

    return company_name, message


def _validate_chart_image(image: bytes) -> bool:
    # caching in memory (global variable)
    global market_close_image
    try:
        return market_close_image == image
    except NameError:
        # file read only once
        import os

        current_path = os.path.dirname(os.path.abspath(__file__))
        market_close_path = os.path.join(current_path, "market_close.png")
        if os.path.exists(market_close_path):
            with open(market_close_path, "rb") as f:
                market_close_image = f.read()
                return market_close_image == image

    raise Exception("chart image validation failed")


def fetch_usstock_chart_photo(
    ticker: str, chart_type: ChartType
) -> Optional[Union[bytes, bool]]:
    try:
        chart_types_mapper = {
            ChartType.REALTIME: ("d", "stock"),
            ChartType.MONTH_1: ("m", "stock"),
            ChartType.MONTH_3: ("m3", "stock"),
            ChartType.YEAR: ("y", "stock"),
            ChartType.YERR_3: ("y3", "stock"),
            ChartType.YEAR_10: ("y10", "stock"),
            ChartType.DAY: ("d", "candle"),
            ChartType.WEEK: ("w", "candle"),
            ChartType.MONTHLY: ("m", "candle"),
        }[chart_type]
    except KeyError:
        return False

    url = f"https://t1.daumcdn.net/finance/chart/us/{chart_types_mapper[1]}/{chart_types_mapper[0]}/{ticker}.png?timestamp={str(int(time.time()))}"
    res = requests.get(url)
    if res.status_code != 200:
        return None

    if _validate_chart_image(res.content):
        return None

    return res.content


async def get_usstock_info(
    update: Update, context: ContextTypes.DEFAULT_TYPE, ticker: Optional[str] = None
):
    if ticker is None:
        if len(context.args) > 1:
            if not (context.args[1] in [chart_type.value for chart_type in ChartType]):
                await get_usstock_info_multiple(update, context)
                return
        ticker = str(context.args[0]).upper()

    logging.info(f">>> 미국 주식정보 {ticker}")

    try:
        if len(context.args) <= 1:
            chart_type = ChartType.REALTIME
        else:
            chart_type = ChartType(str(context.args[1]))
    except Exception:
        message = f"잘못된 차트 타입입니다.\n가능한 값: {', '.join([str(chart_type.value) for chart_type in ChartType])}"
        await context.bot.send_message(chat_id=update.message.chat_id, text=message)
        return

    company_name, stock_data = fetch_usstock_data(ticker)
    photo = fetch_usstock_chart_photo(ticker, chart_type)

    message = f"[{company_name}]" if company_name else ""
    if photo and chart_type != ChartType.REALTIME:
        message += f" {chart_type.value} {stock_data}"
    else:
        message += f"\n{stock_data}"

    if photo:
        await context.bot.send_photo(
            chat_id=update.message.chat_id, photo=photo, caption=message
        )
    else:
        await context.bot.send_message(chat_id=update.message.chat_id, text=message)


async def get_usstock_info_multiple(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tickers = context.args
    logging.info(f">>> 미국 주식정보 (multiple) {tickers}")

    message = ""
    with ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(fetch_usstock_data, ticker, True): ticker
            for ticker in tickers
        }

        done, not_done = wait(futures.keys(), return_when=ALL_COMPLETED)

        for future in futures.keys():
            company_name, stock_data = future.result()
            message += f"{company_name}\n{stock_data}\n\n"

    await context.bot.send_message(chat_id=update.message.chat_id, text=message)


async def fear_and_greed_index(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        url = f'https://production.dataviz.cnn.io/index/fearandgreed/graphdata/{datetime.now().strftime("%Y-%m-%d")}'
        request_wrapper = RequestWrapper()
        response = request_wrapper.get(url)
        response.raise_for_status()
        data = response.json()
        score = round(data["fear_and_greed"]["score"], 1)
        rating = data["fear_and_greed"]["rating"]
        await update.message.reply_text(f"현재 fear & greed Index\n{score} {rating}\n")
    except Exception:
        await update.message.reply_text("데이터를 가져오는데 실패했습니다.")


async def btc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = "https://api.upbit.com/v1/ticker?markets=KRW-BTC"
    request_wrapper = RequestWrapper()
    response = request_wrapper.get(url)
    data = response.json()
    trade_price = int(data[0]["trade_price"])
    signed_change_rate = data[0]["signed_change_rate"] * 100
    signed_change_price = int(data[0]["signed_change_price"])
    await update.message.reply_text(
        f"[업비트] 현재가: {trade_price:,}원 ({signed_change_rate:.2f}% {signed_change_price:,})"
    )


async def wallstreetbets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    def sentiment_to_emoji(sentiment: str) -> str:
        if sentiment == "Bullish":
            return "🚀"
        elif sentiment == "Bearish":
            return "📉"
        else:
            return "🤷‍♂️"

    try:
        url = "https://tradestie.com/api/v1/apps/reddit"
        request_wrapper = RequestWrapper()
        response = request_wrapper.get(url)
        response.raise_for_status()
        data = response.json()
        message = ""
        # for loop to get top 10 stocks (from dict[arr])
        for i, d in enumerate(data):
            if i == 10:
                break
            message += f"{i+1}. {d['ticker']} {sentiment_to_emoji(d['sentiment'])} ({d['sentiment_score']})\n"
        await update.message.reply_text(f"댓글이 많은 순서\n{message}")
    except Exception:
        await update.message.reply_text("데이터를 가져오는데 실패했습니다.")
