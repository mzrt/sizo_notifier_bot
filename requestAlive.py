import os

def getLastTimeout(requestDataFileName:str):
    if(os.path.isfile(requestDataFileName)):
        statbuf = os.stat(requestDataFileName)
        return statbuf.st_mtime
    return 0