from datetime import datetime
import requests
from telegram import Update
from telegram.ext import ContextTypes

from commands.request_wrapper import RequestWrapper


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
    except requests.exceptions.RequestException:
        await update.message.reply_text("데이터를 가져오는데 실패했습니다.")
