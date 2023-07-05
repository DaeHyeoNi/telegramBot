import configparser
import logging
import os

from telegram.ext import Application, ApplicationBuilder


def build_application() -> Application:
    config = get_configuration()

    try:
        token = config["telegram"]["token"]
        if token:
            return ApplicationBuilder().token(token).build()
        else:
            raise KeyError
    except Exception as e:
        if os.path.exists("config.ini"):
            logging.error("Token is not set in config.ini")
        logging.error(e)


def create_config_file():
    DEFAULT_CONFIG = {
        "telegram": {
            "token": "",
            "except_commands": "",
            "logging_level": "INFO",
        }
    }

    if not os.path.exists("config.ini"):
        config = configparser.ConfigParser()
        config.read_dict(DEFAULT_CONFIG)
        with open("config.ini", "w", encoding="utf-8") as configfile:
            config.write(configfile)


def get_configuration():
    if not os.path.exists("config.ini"):
        logging.error("config.ini does not exist. Creating config.ini...")
        create_config_file()
        exit()

    config = configparser.ConfigParser()
    config.read("config.ini", encoding="utf-8")
    return config
