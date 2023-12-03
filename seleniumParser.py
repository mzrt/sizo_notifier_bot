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

# Create a request interceptor
def interceptor(request):
    #del request.headers['Referer']  # Delete the header first
    del request.headers['sec-ch-ua']  # Delete the header firs
    request.headers['sec-ch-ua'] = '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"'
    del request.headers['sec-ch-ua-mobile']  # Delete the header firs
    request.headers['sec-ch-ua-mobile'] = '?0'
    del request.headers['sec-ch-ua-platform']  # Delete the header firs
    request.headers['sec-ch-ua-platform'] = '"Windows"'

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

from schedule import every, repeat, run_pending
loginAttemptsMax = 10
loginAttemptsQty = 0
prevUrlIdx = -1
currentUrlIdx = 0
data = {}
sizoSite = not re.match('https://f-vizit.ru/.*', urls[0] if len(urls) else '')
sizoLoginUrl = 'https://f-okno.ru/login'
vizitLoginUrl = 'https://f-vizit.ru/login'
authorized = False

def check_auth():
    authorized = None
    if browser.find_element(By.CSS_SELECTOR, 'ul#auth'):
        logging.debug(f'3.')
        try:
            element = WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.ID, "login_form"))
            )
            authorized = False
        finally:
            None
    elif browser.find_element(By.CSS_SELECTOR, 'li#clientzone_logout'):
        authorized = True
    return authorized

def wait_captcha():
        WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.XPATH, '//input[@id="g-recaptcha-response"][@value]')))
        captcha = browser.find_element(By.XPATH, '//input[@id="g-recaptcha-response"]')
        print('captcha element', captcha, 'captcha value', captcha.get_attribute('value'))

def login_form_post(form_css_selector, login_input_xpath, auth_button_xpath):    
    if check_auth() == False and browser.find_element(By.CSS_SELECTOR, form_css_selector):
        logging.debug(f'3.')
        wait_captcha()
        login = browser.find_element(By.XPATH, login_input_xpath)
        login.send_keys(authlogin + Keys.TAB + authpass)
        authButton = browser.find_element(By.XPATH, auth_button_xpath)
        authButton.click()

def login():
    if sizoSite:
        login_form_post('form#login_form', '//div/input[@name="login"]', '//div/a[@onclick]')
    else:
        login_form_post('form#login_form', '//div/input[@name="email"]', '//div[@class="pre_submit"]/a')


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
            onclickRun: a.href && a.href.split('&ss=').length < 2 && a.onclick && a.onclick(),
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
    global loginAttemptsMax
    global loginAttemptsQty
    if not urls : return
    if prevUrlIdx != currentUrlIdx or browser.current_url != urls[currentUrlIdx]:
        logging.info(f'1. prevUrlIdx {prevUrlIdx} currentUrlIdx {currentUrlIdx}')
        try:
            if authorized:
                browser.get(urls[currentUrlIdx])
            else:
                loginAttemptsQty += 1
                if sizoSite and (browser.current_url != sizoLoginUrl or loginAttemptsQty>loginAttemptsMax):
                    loginAttemptsQty = 0
                    browser.get(sizoLoginUrl)
                elif not sizoSite and (browser.current_url != vizitLoginUrl or loginAttemptsQty>loginAttemptsMax):
                    loginAttemptsQty = 0
                    browser.get(vizitLoginUrl)
        except WebDriverException:
            browser.close()
            exit()
    prevUrlIdx = currentUrlIdx
    logging.debug(f'2. prevUrlIdx {prevUrlIdx} currentUrlIdx {currentUrlIdx}')
    login()
    logging.debug(f'4.')
    if browser.find_elements_by_css_selector('li#clientzone_logout'):
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
        if browser.find_elements_by_css_selector('li#clientzone_logout'):
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
