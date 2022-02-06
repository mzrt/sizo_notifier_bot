import os, json

def load(filename:str):
    usersData = {}
    usersData['lastNotifyDateService'] = 0
    usersData['issuefixed'] = 'true'
    usersData['chatIds'] = {}
    if(os.path.isfile(filename)):
        with open(filename, 'r') as input_file:
            usersData = json.load(input_file)
    return usersData

def save(filename:str, usersData = {}):
    with open(filename, 'w') as output_file:
        json.dump(usersData, output_file, ensure_ascii=False, indent=4)
    return True