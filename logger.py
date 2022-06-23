import logging
from logging.handlers import RotatingFileHandler
import os
from dotenv import dotenv_values
from config import config, devMode

level = logging.DEBUG if devMode else logging.INFO
logFile = config['LOG_FILENAME_BOT']
logFileRequest=config['LOG_FILENAME_PARSER']

log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')

my_handler_bot = RotatingFileHandler(logFile, mode='a', maxBytes=5*1024*1024,
                                 backupCount=2, encoding='utf-8', delay=0)
my_handler_bot.setFormatter(log_formatter)
my_handler_bot.setLevel(level)

my_handler_parser = RotatingFileHandler(logFileRequest, mode='a', maxBytes=5*1024*1024,
                                 backupCount=2, encoding='utf-8', delay=0)
my_handler_parser.setFormatter(log_formatter)
my_handler_parser.setLevel(level)

app_log_bot = logging.getLogger('bot')
app_log_bot.setLevel(logging.DEBUG)

app_log_bot.addHandler(my_handler_bot)

app_log_parser = logging.getLogger('parser')
app_log_parser.setLevel(logging.INFO)

app_log_parser.addHandler(my_handler_parser)
