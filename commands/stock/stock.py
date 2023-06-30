import json
import logging
import time

from lxml import html
from commands.request_wrapper import RequestWrapper

import commands.stock.stock_data as stock_data
from commands.stock.korean_market_point import get_kospi_point

df_code = stock_data.create()


def get_stock_code(args):
    code = ""
    if args[0].isnumeric():
        code = args[0]
    else:
        try:
            stock_name = " ".join(args[:-1]) if args[-1] == "주봉" else " ".join(args)
            code = str(df_code[stock_name][0])
            logging.info(">>> 코스피 종목 이름으로 " + code + " 반환")
        except:
            code = None
    return code


async def get_kospi_info(update, context):
    if len(context.args) == 0:
        await get_kospi_point(update, context)
        return

    logging.info(">>> 코스피 종목 정보" + str(context.args))

    code = get_stock_code(context.args)
    if code is None:
        await context.bot.send_message(
            chat_id=update.message.chat_id, text="종목 정보를 찾지 못했습니다."
        )
        return

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
            await context.bot.send_photo(
                chat_id=update.message.chat_id, photo=photo_url, caption=caption
            )
        except Exception:
            logging.error(f">>> 코스피 종목 정보 에러 {retry_count}회 재시도")
            time.sleep(1)
            continue
        break


async def get_usstock_info(update, context):
    logging.info(">>> 미국 주식정보" + str(context.args))
    ticker = "^IXIC" if len(context.args) == 0 else str(context.args[0]).upper()
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

        message = f"[{company_name}]\n현재가: {current_price} {current_updown} {current_percent}\n{market_label}: {pre_price} {pre_updown} {pre_percent}"
    except:
        message = "종목 정보를 찾지 못했습니다."

    await context.bot.send_message(chat_id=update.message.chat_id, text=message)
