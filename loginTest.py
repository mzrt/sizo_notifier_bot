# Local imports
from seleniumParser import login, get_login_url, browser

get_login_url()

for request in browser.requests:
    if request.url == 'https://f-okno.ru/login':
        print('params', request.params)
        print(request.headers)

login()

#browser.close()