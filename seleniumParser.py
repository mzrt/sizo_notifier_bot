import json, os, re
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
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
urls = []
urlsFilename = config['PARSE_URLS_FILENAME']
if(urlsFilename and os.path.isfile(urlsFilename)):
    with open(urlsFilename, 'r') as input_file:
        urlsLoaded = json.load(input_file)
        if urlsLoaded and len(urlsLoaded):
            logging.info(f'5.')
            urls = urlsLoaded

logging.info(f'config {json.dumps(config, indent=4)}')
import time
def wait_for(condition_function):
    start_time = time.time()
    while time.time() < start_time + 3:
        if condition_function():
            return True
        else:
            time.sleep(0.1)
    raise Exception(
        'Timeout waiting for {}'.format(condition_function.__name__)
    )
class wait_for_page_load(object):
    def __init__(self, browser):
        self.browser = browser
    def __enter__(self):
        self.old_page = self.browser.find_element_by_tag_name('html')
    def page_has_loaded(self):
        new_page = self.browser.find_element_by_tag_name('html')
        return new_page.id != self.old_page.id
    def __exit__(self, *_):
        wait_for(self.page_has_loaded)

from schedule import every, repeat, run_pending
prevUrlIdx = -1
currentUrlIdx = 0
data = {}
sizoSite = not re.match('https://fsin-vizit.ru/.*', urls[0] if len(urls) else '')
authorized = False
def login_vizit():
    if browser.find_elements_by_css_selector('form#not_auth_table'):
        logging.debug(f'3.')
        loginUrl = browser.find_element(By.XPATH, '//h1/a[@onclick]')
        loginUrl.click()
        try:
            element = WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.ID, "login_form"))
            )
        finally:
            None
    browser.implicitly_wait(3)
    if browser.find_elements_by_css_selector('form#login_form'):
        logging.debug(f'7.')
        login = browser.find_element(By.XPATH, '//div/input[@name="email"]')
        login.send_keys(authlogin + Keys.TAB + authpass)
        authButton = browser.find_element(By.XPATH, '//div[@class="pre_submit"]/a')
        authButton.click()


def login_sizo():
    if browser.find_elements_by_css_selector('form#login_form'):
        logging.debug(f'3.')
        login = browser.find_element(By.XPATH, '//div/input[@name="login"]')
        login.send_keys(authlogin + Keys.TAB + authpass)
        authButton = browser.find_element(By.XPATH, '//div/a[@onclick]')
        authButton.click()

def login():
    if sizoSite:
        login_sizo()
    else:
        login_vizit()


@repeat(every(int(config['REQUEST_SECONDS_INTERVAL'])).seconds)
def job():
    global prevUrlIdx
    global currentUrlIdx
    global data
    global urls
    scriptDays = """
    return Array.from(
        document.querySelectorAll('div#graphic_container > a')
    ).filter(
        elem => !elem.querySelectorAll('div.busy').length
    ).map(
        a=> ({
            onclickRun: a.onclick && a.onclick(),
            url: a.href,
            places: a.href.replace(
                /^.*&t=(\d+).*$/g,
                '$1'
            ),
            day: a.href.replace(
                /^.*&date=(\d{4})-(\d\d)-(\d\d).*$/g,
                '$3.$2.$1'
            )})
        )
    """

    scriptDaysVizit = """
    return Array.from(document.querySelectorAll('div#graphic_container > form')).map(
        a=> ({
            url: null,
            places: null,
            day: a.id.replace(
                /^.*(\d{4})-(\d\d)-(\d\d).*$/g,
                '$3.$2.$1'
            )
        })
    )
    """

    global authorized
    if not urls : return
    if prevUrlIdx != currentUrlIdx:
        logging.info(f'1. prevUrlIdx {prevUrlIdx} currentUrlIdx {currentUrlIdx}')
        try:
            browser.get(urls[currentUrlIdx])
        except WebDriverException:
            browser.close()
            exit()
    prevUrlIdx = currentUrlIdx
    logging.debug(f'2. prevUrlIdx {prevUrlIdx} currentUrlIdx {currentUrlIdx}')
    login()
    logging.debug(f'4.')
    if browser.find_elements_by_css_selector('div#graphic_container'):
        logging.debug(f'5.')
        authorized = True
    else:
        logging.debug(f'6.')
        try:
            element = WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.ID, "graphic_container"))
            )
        except TimeoutException:
            None
        finally:
            None
        if browser.find_elements_by_css_selector('div#graphic_container'):
            logging.debug(f'7.')
            authorized = True
    if authorized:
        logging.debug(f'8.')
        days = browser.execute_script(scriptDays if sizoSite else scriptDaysVizit)
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
