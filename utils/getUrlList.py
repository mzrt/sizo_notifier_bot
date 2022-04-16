import re

def getParselUrls(response):
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

def getRegions(response):
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