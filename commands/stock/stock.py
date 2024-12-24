import json
import logging
import time
from concurrent.futures import ALL_COMPLETED, ThreadPoolExecutor, wait
from datetime import datetime
from typing import Optional, Union, Dict

import requests
from telegram import Update
from telegram.ext import ContextTypes

import commands.stock.stock_data as stock_data
from commands.request_wrapper import RequestWrapper
from commands.stock.common import KoreanMarketType
from commands.stock.enums import ChartType
from commands.stock.robinhood import RobinHood

df_code = stock_data.create()

rh = RobinHood()
rh.load_data()


class MarketDataFetcher:
    """시장 데이터를 가져오는 유틸리티 클래스"""

    @staticmethod
    def fetch_korean_stock(code: str) -> Dict:
        """한국 주식 데이터를 가져옵니다."""
        url = f"https://polling.finance.naver.com/api/realtime/domestic/stock/{code}"
        request_wrapper = RequestWrapper()
        response = request_wrapper.get(url)
        return json.loads(response.text)["datas"][0]

    @staticmethod
    def fetch_korean_market(market_type: KoreanMarketType) -> Dict:
        """한국 시장 지수를 가져옵니다."""
        url = f"https://m.stock.naver.com/api/index/{market_type.value}/basic"
        request_wrapper = RequestWrapper()
        response = request_wrapper.get(url)
        return json.loads(response.text)

    @staticmethod
    def fetch_us_stock(ticker: str, flat: bool = False) -> tuple[str, str]:
        """미국 주식 데이터를 가져옵니다."""
        ticker = ticker.upper()
        data = rh.get_data(ticker)

        if not data:
            return "", "종목 정보를 찾지 못했습니다."

        return MarketDataFetcher._parse_us_stock_data(data, ticker, flat)

    @staticmethod
    def _parse_us_stock_data(
        data: Dict, ticker: str, flat: bool = False
    ) -> tuple[str, str]:
        """미국 주식 데이터를 파싱합니다."""
        company_name = f"{data['chart_section']['header'][0]['text']} ({ticker})"
        display = data["chart_section"]["default_display"]
        quote = data["chart_section"]["quote"]

        trade_price = float(quote["last_trade_price"])

        messages = []
        for value_type in ["secondary_value", "tertiary_value"]:
            if value := display.get(value_type):
                desc = MarketDataFetcher._translate_market_desc(
                    value["description"]["value"]
                )
                if desc != "현재가":
                    trade_price = float(quote["last_extended_hours_trade_price"])
                val = value["main"]["value"]
                messages.append(f"{desc}: {trade_price} {val}")

        message = " ".join(messages) if flat else "\n".join(messages)
        return company_name, message

    @staticmethod
    def _translate_market_desc(value: str) -> str:
        """마켓 설명을 번역합니다."""
        translations = {
            "Overnight": "데이마켓",
            "Pre-market": "프리장",
            "Today": "현재가",
            "After-hours": "시간외",
        }
        return translations.get(value, value)


def get_stock_code(args: str) -> Optional[str]:
    """주식 종목 코드를 검색합니다."""
    if args[0].isnumeric():
        return args[0]

    try:
        stock_name = (
            " ".join(args[:-1]) if args[-1] in ["일봉", "주봉"] else " ".join(args)
        )
        code = str(df_code[stock_name][0])
        logging.info(f">>> 코스피 종목 이름으로 {code} 반환")
        return code
    except:
        return None


async def get_kospi_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """코스피 정보를 조회합니다."""
    if not context.args:
        return await get_korea_market_point(
            update, context, type=KoreanMarketType.KOSPI
        )

    logging.info(f">>> 코스피 종목 정보 {context.args}")

    code = get_stock_code(context.args)
    if code is None:
        return await context.bot.send_message(
            chat_id=update.message.chat_id, text="종목 정보를 찾지 못했습니다."
        )

    data = MarketDataFetcher.fetch_korean_stock(code)
    caption = format_korean_stock_message(data)

    photo_url = get_chart_photo_url(code, context.args[-1])
    if context.args[-1] == "주봉":
        caption += "\n주봉 차트입니다."

    for retry_count in range(3):
        try:
            return await context.bot.send_photo(
                chat_id=update.message.chat_id, photo=photo_url, caption=caption
            )
        except Exception:
            logging.error(f">>> 코스피 종목 정보 에러 {retry_count}회 재시도")
            time.sleep(1)
            continue


def format_korean_stock_message(data: Dict) -> str:
    """한국 주식 메시지를 포맷팅합니다."""
    return (
        f"종목명: {data['stockName']} / "
        f"현재: {data['closePrice']} "
        f"({float(data['fluctuationsRatio']):.2f}%)"
    )


def get_chart_photo_url(code: str, chart_type: str) -> str:
    """차트 이미지 URL을 생성합니다."""
    base_url = "https://ssl.pstatic.net/imgfinance/chart/item/area/"
    timeframe = "week/" if chart_type == "주봉" else "day/"
    return f"{base_url}{timeframe}{code}.png?ver={str(int(time.time()))}"


async def get_korea_market_point(
    update: Update, context: ContextTypes.DEFAULT_TYPE, type: KoreanMarketType
):
    """한국 시장 지수를 조회합니다."""
    resp = MarketDataFetcher.fetch_korean_market(type)

    await context.bot.send_message(
        chat_id=update.message.chat_id,
        text=f'{type.name} 지수: {resp["closePrice"]} ({resp["compareToPreviousClosePrice"]} {resp["fluctuationsRatio"]}%)',
    )


async def get_usstock_info(
    update: Update, context: ContextTypes.DEFAULT_TYPE, ticker: Optional[str] = None
):
    """미국 주식 정보를 조회합니다."""
    if ticker is None:
        if len(context.args) > 1:
            if not (context.args[1] in [chart_type.value for chart_type in ChartType]):
                await get_usstock_info_multiple(update, context)
                return
        ticker = str(context.args[0]).upper()

    logging.info(f">>> 미국 주식정보 {ticker}")

    try:
        chart_type = (
            ChartType.REALTIME
            if len(context.args) <= 1
            else ChartType(str(context.args[1]))
        )
    except Exception:
        message = f"잘못된 차트 타입입니다.\n가능한 값: {', '.join([str(chart_type.value) for chart_type in ChartType])}"
        await context.bot.send_message(chat_id=update.message.chat_id, text=message)
        return

    company_name, stock_data = MarketDataFetcher.fetch_us_stock(ticker)
    photo = fetch_usstock_chart_photo(ticker, chart_type)

    message = format_us_stock_message(company_name, stock_data, chart_type)

    if photo:
        await context.bot.send_photo(
            chat_id=update.message.chat_id, photo=photo, caption=message
        )
    else:
        await context.bot.send_message(chat_id=update.message.chat_id, text=message)


def format_us_stock_message(
    company_name: str, stock_data: str, chart_type: ChartType
) -> str:
    """미국 주식 메시지를 포맷팅합니다."""
    message = f"[{company_name}]" if company_name else ""
    if chart_type != ChartType.REALTIME:
        message += f" {chart_type.value} {stock_data}"
    else:
        message += f"\n{stock_data}"
    return message


def _validate_chart_image(image: bytes) -> bool:
    """차트 이미지가 유효한지 검증합니다."""
    global market_close_image
    try:
        return market_close_image == image
    except NameError:
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
    """미국 주식 차트 이미지를 가져옵니다."""
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


async def get_usstock_info_multiple(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """여러 미국 주식 정보를 조회합니다."""
    tickers = context.args
    logging.info(f">>> 미국 주식정보 (multiple) {tickers}")

    message = ""
    with ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(MarketDataFetcher.fetch_us_stock, ticker, True): ticker
            for ticker in tickers
        }

        done, not_done = wait(futures.keys(), return_when=ALL_COMPLETED)

        for future in futures.keys():
            company_name, stock_data = future.result()
            message += f"{company_name}\n{stock_data}\n\n"

    await context.bot.send_message(chat_id=update.message.chat_id, text=message)


async def fear_and_greed_index(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """공포탐욕지수를 조회합니다."""
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
    """비트코인 가격을 조회합니다."""
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
    """월스트리트베츠 센티먼트를 조회합니다."""

    def sentiment_to_emoji(sentiment: str) -> str:
        return {"Bullish": "🚀", "Bearish": "📉"}.get(sentiment, "🤷‍♂️")

    try:
        url = "https://tradestie.com/api/v1/apps/reddit"
        request_wrapper = RequestWrapper()
        response = request_wrapper.get(url)
        response.raise_for_status()
        data = response.json()[:10]

        message = "댓글이 많은 순서\n" + "\n".join(
            f"{i+1}. {d['ticker']} {sentiment_to_emoji(d['sentiment'])} ({d['sentiment_score']})"
            for i, d in enumerate(data)
        )

        await update.message.reply_text(message)
    except Exception:
        await update.message.reply_text("데이터를 가져오는데 실패했습니다.")
