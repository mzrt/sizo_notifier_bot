import os
from dotenv import dotenv_values
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')

config = {
    **dotenv_values(".env.shared"),
    **dotenv_values(".env.secret"),
    **dotenv_values(".env.shared.local"),
    **dotenv_values(".env.secret.local"),
    **os.environ,  # override loaded values with environment variables
}

url = config['URL']
import re, requests, json
from lxml import html
import logging
logging.basicConfig(filename='requestParser.log', encoding='utf-8', level=logging.INFO)

logging.info(f'config {json.dumps(config, indent=4)}')
def load_data():
    # establishing session
    session = requests.Session() 
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0'
    })
    request = session.get(url)
    logging.debug(f'load_data get {url}')
    return request.text

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
    logging.info(f'getDaysList {len(dayList)} {dayList}')
    return dayList

from schedule import every, repeat, run_pending
import time

@repeat(every(2).minutes)
def job():
    r = load_data()
    tree = html.fromstring(r)
    data = {
        'url': url,
        'dates': getDaysList(tree)
    }
    logging.debug(f'job {json.dumps(data)}')
    with open('data.json', 'w') as output_file:
        json.dump(data, output_file, ensure_ascii=False, indent=4)

while True:
    run_pending()
    time.sleep(1)