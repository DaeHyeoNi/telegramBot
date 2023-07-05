import json
import logging
import time
from datetime import datetime
from typing import Optional

from lxml import html
from telegram import Update
from telegram.ext import ContextTypes

import commands.stock.stock_data as stock_data
from commands.request_wrapper import RequestWrapper
from commands.stock.common import KoreanMarketType

df_code = stock_data.create()


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


async def get_usstock_info(
    update: Update, context: ContextTypes.DEFAULT_TYPE, ticker: Optional[str]
):
    if ticker is None:
        ticker = str(context.args[0]).upper()
    logging.info(f">>> 미국 주식정보 {ticker}")

    url = "https://finance.yahoo.com/quote/" + ticker + "/"
    request_wrapper = RequestWrapper()
    response = request_wrapper.get(url)
    data = response.text
    element = html.fromstring(data)

    try:
        company_name = element.xpath(
            '//*[@id="quote-header-info"]/div[2]/div[1]/div[1]/h1'
        )[0].text
        current_price = element.xpath(
            '//*[@id="quote-header-info"]/div[3]/div[1]/div[1]/fin-streamer[1]'
        )[0].text
        current_updown = element.xpath(
            '//*[@id="quote-header-info"]/div[3]/div[1]/div[1]/fin-streamer[2]/span'
        )[0].text
        current_percent = element.xpath(
            '//*[@id="quote-header-info"]/div[3]/div[1]/div[1]/fin-streamer[3]/span'
        )[0].text

        try:
            is_after_market = (
                "After"
                in element.xpath(
                    '//*[@id="quote-header-info"]/div[3]/div[1]/div[2]/span[2]/span'
                )[0].text
            )
            market_label = "애프터장" if is_after_market else "프리장"

            pre_price = element.xpath(
                '//*[@id="quote-header-info"]/div[3]/div[1]/div[2]/fin-streamer[2]'
            )[0].text
            pre_updown = element.xpath(
                '//*[@id="quote-header-info"]/div[3]/div[1]/div[2]/span[1]/fin-streamer[1]/span'
            )[0].text
            pre_percent = element.xpath(
                '//*[@id="quote-header-info"]/div[3]/div[1]/div[2]/span[1]/fin-streamer[2]/span'
            )[0].text

            message = f"[{company_name}]\n종가: {current_price} {current_updown} {current_percent}\n{market_label}: {pre_price} {pre_updown} {pre_percent}"
        except Exception:
            # 본장
            message = f"[{company_name}]\n현재가: {current_price} {current_updown} {current_percent}"
    except Exception as e:
        logging.error(e)
        message = "종목 정보를 찾지 못했습니다."

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
