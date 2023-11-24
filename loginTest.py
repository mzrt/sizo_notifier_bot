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
loginAttemptsMax = 10
loginAttemptsQty = 0
prevUrlIdx = -1
currentUrlIdx = 0
data = {}
sizoSite = not re.match('https://fsin-vizit.ru/.*', urls[0] if len(urls) else '')
sizoLoginUrl = 'https://f-okno.ru/login'
vizitLoginUrl = 'https://fsin-vizit.ru/login'
authorized = False
def wait_captcha():
        WebDriverWait(browser, 10).until(EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR,"iframe[name^='a-'][src^='https://www.google.com/recaptcha/api2/anchor?']")))
        WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.XPATH, '//input[@id="recaptcha-token"][@value]')))
        browser.switch_to.default_content()
        WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.XPATH, '//input[@id="g-recaptcha-response"][@value]')))
        captcha = browser.find_element(By.XPATH, '//input[@id="g-recaptcha-response"]')
        print('captcha element', captcha, 'catcha value', captcha.get_attribute('value'))

def login_form_post(form_css_selector, login_input_xpath, auth_button_xpath):
    if browser.find_elements_by_css_selector(form_css_selector):
        logging.debug(f'3.')
        wait_captcha()
        login = browser.find_element(By.XPATH, login_input_xpath)
        login.send_keys(authlogin + Keys.TAB + authpass)
        authButton = browser.find_element(By.XPATH, auth_button_xpath)
        authButton.click()

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
    login_form_post('form#login_form', '//div/input[@name="email"]', '//div[@class="pre_submit"]/a')

def login():
    if sizoSite:
        login_form_post('form#login_form', '//div/input[@name="login"]', '//div/a[@onclick]')
    else:
        login_vizit()

browser.get(sizoLoginUrl)
login()
browser.close()