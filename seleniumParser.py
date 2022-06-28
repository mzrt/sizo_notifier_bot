import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Local imports
from logger import getlogger_selenium as getlogging
from config import config

logging = getlogging()
#urls = config['URLS']
authlogin = config['AUTH_LOGIN']
authpass = config['AUTH_PASS']
dataFileName = config['SELENIUM_DATA_JSON_FILENAME']

browser = webdriver.Firefox()
urls = [
    'https://fsin-okno.ru/base/spbilo/sizo1kresty?order_type=2',
    'https://fsin-okno.ru/base/moscow/matrosska',
    'https://fsin-okno.ru/base/moscow/matrosska?order_type=2',
    'https://fsin-okno.ru/base/novosibirsk/si1novosib'
]

scriptDays = """
return Array.from(document.querySelectorAll('div#graphic_container > a')).map( a=> a.href.replace(
    /^.*&date=(\d{4})-(\d\d)-(\d\d).*$/g,
    '$3.$2.$1'
))
"""

logging.info(f'config {json.dumps(config, indent=4)}')

from schedule import every, repeat, run_pending
import time
prevUrlIdx = -1
currentUrlIdx = 0
data = {}

@repeat(every(int(config['REQUEST_SECONDS_INTERVAL'])).seconds)
def job():
    global prevUrlIdx
    global currentUrlIdx
    global data
    global urls
    global scriptDays
    canGetData = False
    if prevUrlIdx != currentUrlIdx:
        logging.info(f'1. prevUrlIdx {prevUrlIdx} currentUrlIdx {currentUrlIdx}')
        browser.get(urls[currentUrlIdx])
    prevUrlIdx = currentUrlIdx
    logging.debug(f'2. prevUrlIdx {prevUrlIdx} currentUrlIdx {currentUrlIdx}')
    if browser.find_elements_by_css_selector('form#login_form'):
        logging.debug(f'3.')
        login = browser.find_element(By.XPATH, '//div/input[@name="login"]')
        login.send_keys(authlogin + Keys.TAB + authpass)
        authButton = browser.find_element(By.XPATH, '//div/a[@onclick]')
        authButton.click()
    logging.debug(f'4.')
    if browser.find_elements_by_css_selector('div#graphic_container'):
        logging.debug(f'5.')
        canGetData = True
    else:
        logging.debug(f'6.')
        element = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.ID, "graphic_container"))
        )
        if browser.find_elements_by_css_selector('div#graphic_container'):
            logging.debug(f'7.')
            canGetData = True
    if canGetData:
        logging.debug(f'8.')
        days = browser.execute_script(scriptDays)
        logging.debug(f'8. days {days}')
        data[urls[currentUrlIdx]] = days
        currentUrlIdx = (currentUrlIdx+1)%len(urls)
        logging.info(f'{dataFileName}: {json.dumps(data)}')
        with open(dataFileName, 'w') as output_file:
            json.dump(data, output_file, ensure_ascii=False, indent=4)

while True:
    logging.debug(f'0.')
    run_pending()
    time.sleep(1)
