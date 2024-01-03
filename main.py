import logging

from commands.commands import CommandHandler
from config import build_application, get_configuration
from create_commands import create_commands

if __name__ == "__main__":
    config = get_configuration()
    logging_level = config["telegram"].get("logging_level", "INFO")
    logging.basicConfig(level=logging._nameToLevel[logging_level])

    if app := build_application():
        command_handler = CommandHandler(app, config)
        create_commands(command_handler)

    app.run_polling()
