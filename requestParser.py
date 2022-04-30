from errno import ECONNABORTED, ECONNREFUSED, ECONNRESET, EPIPE, ESHUTDOWN
import os
import re, requests, json
from lxml import html
import logging
from dotenv import dotenv_values

devMode = 'app' in os.environ and os.environ['app']=="dev"
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')

config = {
    **dotenv_values(".env.shared"),
    **dotenv_values(".env.secret"),
    **dotenv_values(".env.shared.local"),
    **dotenv_values(".env.secret.local"),
    **(dotenv_values(".env.development.local") if devMode else {}),
    **os.environ,  # override loaded values with environment variables
}

dataFileName = config['DATA_JSON_FILENAME']
url = config['URL']
level = logging.DEBUG if devMode else logging.INFO
logging.basicConfig(filename=config['LOG_FILENAME_PARSER'], encoding='utf-8', level=level)

logging.info(f'config {json.dumps(config, indent=4)}')
def load_data():
    try:
        # establishing session
        session = requests.Session() 
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0'
        })
        request = session.get(url)
        logging.debug(f'load_data get {url}')
        return request.text
    except OSError as e:
        if e.errno not in (EPIPE, ESHUTDOWN, ECONNABORTED, ECONNREFUSED, ECONNRESET):
            raise Exception('Возникла непредвиденная ошибка: {}'.format(e)) from None
        session.close()
        logging.info('Ошибка подключения по адресу '+url+(':\n{}'.format(e)))
    return ''

def getDaysQty(response):
    return len(
        list(
            map(
                lambda item: re.sub( '^.*&date=(\d{4})-(\d\d)-(\d\d).*$', '\\3.\\2.\\1', item),
                response.xpath('//a[@onclick]/@href')
            )
        )
    )

def getUrls(response):
    onclickUrls = list(response.xpath('//a[@onclick]/@onclick'))
    suffix = ''
    if(len(onclickUrls)>0):
        suffix = re.sub( "^.*'(&ss=(\d)+)'.*", '\\1', onclickUrls[0])
    return list(
        map(
            lambda item: item + suffix,
            response.xpath('//a[@onclick]/@href')
        )
    )
def getDaysList(response):
    dayList = list(
        map(
            lambda item: re.sub( '^.*&date=(\d{4})-(\d\d)-(\d\d).*$', '\\3.\\2.\\1', item),
            response.xpath('//a[@onclick]/@href')
        )
    )
    logging.debug(f'getDaysList {len(dayList)} {dayList}')
    return dayList

from schedule import every, repeat, run_pending
import time

@repeat(every(int(config['REQUEST_MINUTES_INTERVAL'])).minutes)
def job():
    r = load_data()
    if(len(r)>0):
        tree = html.fromstring(r)
        data = {
            'url': url,
            'dates': getDaysList(tree)
        }
        logging.debug(f'job save data to {dataFileName}: {json.dumps(data)}')
        with open(dataFileName, 'w') as output_file:
            json.dump(data, output_file, ensure_ascii=False, indent=4)

while True:
    run_pending()
    time.sleep(1)