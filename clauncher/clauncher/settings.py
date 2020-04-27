import json

CFG_FILE = 'config.json'

def load():
    global s_dict
    with open(CFG_FILE) as json_data_file:
        s_dict = json.load(json_data_file)
