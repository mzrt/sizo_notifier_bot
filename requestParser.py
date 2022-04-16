from errno import ECONNABORTED, ECONNREFUSED, ECONNRESET, EPIPE, ESHUTDOWN
import os
from dotenv import dotenv_values
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')

config = {
    **dotenv_values(".env.shared"),
    **dotenv_values(".env.secret"),
    **dotenv_values(".env.shared.local"),
    **dotenv_values(".env.secret.local"),
    **(dotenv_values(".env.development.local") if 'app' in os.environ and os.environ['app']=="dev" else {}),
    **os.environ,  # override loaded values with environment variables
}

url = config['URL']
import re, requests, json
from lxml import html
import logging
level = logging.DEBUG if 'app' in os.environ and os.environ['app']=="dev" else logging.INFO
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
        logging.debug(f'job save data to {config["DATA_JSON_FILENAME"]}: {json.dumps(data)}')
        with open(config['DATA_JSON_FILENAME'], 'w') as output_file:
            json.dump(data, output_file, ensure_ascii=False, indent=4)

while True:
    run_pending()
    time.sleep(1)