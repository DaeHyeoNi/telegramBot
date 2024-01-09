import random

from telegram import Update
from telegram.ext import ContextTypes


async def choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choices = context.args
    if len(choices) < 2:
        await update.message.reply_text("2개 이상의 선택지를 입력해주세요.")
        return
    
    result = random.choice(choices)
    await update.message.reply_text(result)
