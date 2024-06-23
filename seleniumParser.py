import json, os, re
#from seleniumwire import webdriver  # Import from seleniumwire
from selenium import webdriver  # Import from seleniumwire
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Local imports
from logger import getlogger_selenium as getlogging
from config import config
from utils.email import getResetPassworCodeWithConfig
getResetPassworCode = getResetPassworCodeWithConfig(config)

logging = getlogging()
#urls = config['URLS']
authlogin = config['AUTH_LOGIN']
authpass = config['AUTH_PASS']
dataFileName = config['SELENIUM_DATA_JSON_FILENAME']
useChrome = config['USE_CHROME'] == 'true'
def get_browser(useChrome):
    retVal = None
    if useChrome:
        options = webdriver.ChromeOptions()
        #options.add_argument('headless')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--remote-debugging-port=9222')
        retVal = webdriver.Chrome(options=options)
    else:
        retVal = webdriver.Firefox()
    return retVal
browser = get_browser(useChrome=useChrome)
def interceptor(request):
    del request.headers['sec-ch-ua']
    request.headers['sec-ch-ua'] = '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"'
    del request.headers['sec-ch-ua-mobile']
    request.headers['sec-ch-ua-mobile'] = '?0'
    del request.headers['sec-ch-ua-platform']
    request.headers['sec-ch-ua-platform'] = '"Windows"'
    del request.headers['User-Agent']
    request.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'

browser.request_interceptor = interceptor

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
sizoRecoveryUrl = 'https://f-okno.ru/recovery'
vizitRecoveryUrl = 'https://f-vizit.ru/recovery'
recovery_code = getResetPassworCode()
authorized = False
def get_login_url():
    try:
        if sizoSite:
            browser.get(sizoLoginUrl)
        else:
            browser.get(vizitLoginUrl)
    except WebDriverException:
        browser.close()
        exit()

get_login_url()
def check_auth():
    authorized = None
    try:
        browser.find_element(By.CSS_SELECTOR, 'ul#auth')
        authorized = False
    except NoSuchElementException:
        try:
            browser.find_element(By.CSS_SELECTOR, 'li#clientzone_logout')
            authorized = True
        except NoSuchElementException:
            None
    return authorized

def check_xpath(xpath):
    exists = None
    try:
        browser.find_element(By.XPATH, xpath)
        exists = True
    except NoSuchElementException:
            exists = False
    return exists


def recovery_form_post(recoveryUrl, login_input_xpath, auth_button_xpath, recovery_code_xpath, recovery_button_xpath, new_password_xpath, new_password_button_xpath):
    global recovery_code
    if check_auth() == False:
        if browser.current_url != recoveryUrl:
            logging.debug(f'3.')
            browser.get(recoveryUrl)
            login = browser.find_element(By.XPATH, login_input_xpath)
            login.send_keys(authlogin)
            authButton = browser.find_element(By.XPATH, auth_button_xpath)
            authButton.click()
            recovery_code = ''
        else:
            if not recovery_code:
                recovery_code = getResetPassworCode()
            if browser.current_url == recoveryUrl and check_xpath(recovery_code_xpath) and recovery_code:
                browser.find_element(By.XPATH, recovery_code_xpath).send_keys(recovery_code)
                browser.find_element(By.XPATH, recovery_button_xpath).click()
            if browser.current_url == recoveryUrl and check_xpath(new_password_xpath):
                browser.find_element(By.XPATH, new_password_xpath).send_keys(authpass)
                browser.find_element(By.XPATH, new_password_button_xpath).click()
                if check_auth() == False:
                    recovery_code = ''
                    get_login_url()

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
    presubmit_path = '//div[@class="pre_submit"]/a'
    if sizoSite:
        login_form_post('form#login_form', '//div/input[@name="login"]', '//div/a[@onclick]')
        if check_auth() == False:
            recovery_form_post(
                sizoRecoveryUrl,
                '//div/input[@name="recovery-email"]',
                presubmit_path,
                '//div/input[@name="recoverypass-code"]',
                presubmit_path,
                '//div/input[@name="newpassword"]',
                presubmit_path,
            )
    else:
        login_form_post('//form[@id="login_form"]', '//div/input[@name="email"]', presubmit_path)
        if check_auth() == False:
            recovery_form_post(
                vizitRecoveryUrl, 
                '//div/input[@name="recovery-email"]',
                presubmit_path,
                '//div/input[@name="recoverypass-code"]',
                presubmit_path,
                '//div/input[@name="newpassword"]',
                presubmit_path,
            )

def getDays():
    global prevUrlIdx
    global currentUrlIdx
    global data
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
    prevUrlIdx = currentUrlIdx
    logging.debug(f'2. prevUrlIdx {prevUrlIdx} currentUrlIdx {currentUrlIdx}')
    days = browser.execute_script(scriptDays if sizoSite else scriptDaysVizit)
    logging.debug(f'8. days {days}')
    data[urls[currentUrlIdx]] = days
    currentUrlIdx = (currentUrlIdx+1)%len(urls)
    logging.info(f'{dataFileName}: {json.dumps(data)}')
    with open(dataFileName, 'w') as output_file:
        json.dump(data, output_file, ensure_ascii=False, indent=4)

@repeat(every(int(config['REQUEST_SECONDS_INTERVAL'])).seconds)
def job():
    global loginAttemptsQty
    if not urls : return
    authorized = check_auth()
    if prevUrlIdx != currentUrlIdx or browser.current_url != urls[currentUrlIdx]:
        logging.info(f'1. prevUrlIdx {prevUrlIdx} currentUrlIdx {currentUrlIdx}')
        try:
            if authorized:
                browser.get(urls[currentUrlIdx])
            else:
                loginAttemptsQty += 1
                if sizoSite and (browser.current_url != sizoLoginUrl or loginAttemptsQty>loginAttemptsMax):
                    loginAttemptsQty = 0
                    #get_login_url()
                elif not sizoSite and (browser.current_url != vizitLoginUrl or loginAttemptsQty>loginAttemptsMax):
                    loginAttemptsQty = 0
                    #get_login_url()
        except WebDriverException:
            browser.close()
            exit()
    login()
    logging.debug(f'4.')
    if authorized == True:
        getDays()

if __name__ == "__main__":
    while True:
        logging.debug(f'0.')
        run_pending()
        time.sleep(1)
