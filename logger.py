import logging
from logging.handlers import RotatingFileHandler
import os
from dotenv import dotenv_values
from config import config, devMode

level = logging.DEBUG if devMode else logging.INFO
logFile = config['LOG_FILENAME_BOT']
logFileParser=config['LOG_FILENAME_PARSER']
logFileSelenium=config['LOG_FILENAME_PARSER']

log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')

my_handler_bot = RotatingFileHandler(logFile, mode='a', maxBytes=5*1024*1024,
                                 backupCount=2, encoding='utf-8', delay=0)
my_handler_bot.setFormatter(log_formatter)
my_handler_bot.setLevel(level)

logger_bot = logging.getLogger('bot')
logger_bot.setLevel(logging.DEBUG)

logger_bot.addHandler(my_handler_bot)


my_handler_parser = RotatingFileHandler(logFileParser, mode='a', maxBytes=5*1024*1024,
                                 backupCount=2, encoding='utf-8', delay=0)
my_handler_parser.setFormatter(log_formatter)
my_handler_parser.setLevel(level)

logger_parser = logging.getLogger('parser')
logger_parser.setLevel(logging.INFO)

logger_parser.addHandler(my_handler_parser)

my_handler_selenium = RotatingFileHandler(logFileSelenium, mode='a', maxBytes=5*1024*1024,
                                 backupCount=2, encoding='utf-8', delay=0)
my_handler_selenium.setFormatter(log_formatter)
my_handler_selenium.setLevel(level)

logger_selenium = logging.getLogger('selenium')
logger_selenium.setLevel(logging.INFO)

logger_selenium.addHandler(my_handler_selenium)
