from telegram import Update
from telegram.ext import ContextTypes
import git


async def version(update: Update, context: ContextTypes.DEFAULT_TYPE):
    repo = git.Repo(search_parent_directories=True)

    sha = repo.head.object.hexsha
    commit_message = repo.head.object.summary
    commit_author = repo.head.object.author.name
    await update.message.reply_text(f"{sha}\n{commit_message} by {commit_author}")
