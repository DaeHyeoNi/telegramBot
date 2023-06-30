import logging

from command_handler import CommandHandler
from config import build_application, get_configuration

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    if app := build_application():
        command_handler = CommandHandler(app, get_configuration())
        command_handler.run()

    app.run_polling()
