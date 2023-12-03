import json, os, re
#from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from seleniumwire import webdriver  # Import from seleniumwire

# Local imports
from logger import getlogger_selenium as getlogging
from config import config

logging = getlogging()
#urls = config['URLS']
authlogin = config['AUTH_LOGIN']
authpass = config['AUTH_PASS']
dataFileName = config['SELENIUM_DATA_JSON_FILENAME']

browser = webdriver.Firefox()
# Create a request interceptor
def interceptor(request):
    #del request.headers['Referer']  # Delete the header first
    del request.headers['sec-ch-ua']  # Delete the header firs
    request.headers['sec-ch-ua'] = '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"'
    del request.headers['sec-ch-ua-mobile']  # Delete the header firs
    request.headers['sec-ch-ua-mobile'] = '?0'
    del request.headers['sec-ch-ua-platform']  # Delete the header firs
    request.headers['sec-ch-ua-platform'] = '"Windows"'

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

if sizoSite:
    browser.get(sizoLoginUrl)
else:
    browser.get(vizitLoginUrl)
login()
browser.close()