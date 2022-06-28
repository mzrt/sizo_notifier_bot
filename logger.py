import logging
from logging.handlers import RotatingFileHandler
import os
from dotenv import dotenv_values
from config import config, devMode

level = logging.DEBUG if devMode else logging.INFO
logFile = config['LOG_FILENAME_BOT']
logFileParser=config['LOG_FILENAME_PARSER']
logFileSelenium=config['LOG_FILENAME_SELENIUM']
logFileInitDb=config['LOG_FILENAME_INITDB']

log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')

def getLogger(fileName, loggerLevel, loggerName):
    my_handler = RotatingFileHandler(fileName, mode='a', maxBytes=5*1024*1024,
                                    backupCount=2, encoding='utf-8', delay=0)
    my_handler.setFormatter(log_formatter)
    my_handler.setLevel(loggerLevel)

    logger_bot = logging.getLogger(loggerName)
    logger_bot.setLevel(logging.DEBUG)

    logger_bot.addHandler(my_handler)
    return logger_bot

def getlogger_bot(): return getLogger(logFile, logging.DEBUG, 'bot')
def getlogger_parser(): return getLogger(logFileParser, logging.INFO, 'parser')
def getlogger_selenium(): return getLogger(logFileSelenium, logging.INFO, 'selenium')
def getlogger_initDb(): return getLogger(logFileInitDb, logging.INFO, 'initDb')
