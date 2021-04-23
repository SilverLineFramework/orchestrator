import json
import uuid

def convert_str_attrs_into_obj(dict):
    convert_keys = ['apis', 'args', 'env', 'channels', 'peripherals']
    # convert array attributes saved as strings into objects
    for key in convert_keys:
        try:
            attr_str = dict[key].replace("'", '"')
            dict[key] = json.loads(attr_str)
            print(key, attr_str, dict[key])
        except Exception as err:
            pass

class ARTSResponse(dict):
    def __init__(self, r_uuid, result, details, convert_str_attrs=True):
        if convert_str_attrs:
            # convert string attributes into objects
            convert_str_attrs_into_obj(details)
        dict.__init__(self, object_id=str(r_uuid), type='arts_resp', data={ 'result': result, 'details': details})

class ARTSRequest(dict):
    def __init__(self, action, rdata, convert_str_attrs=True):
        if convert_str_attrs:
            # convert string attributes into objects
            print("Converting:", rdata)
            convert_str_attrs_into_obj(rdata)
        dict.__init__(self, object_id=str(uuid.uuid4()), action=action, type='arts_req', data=rdata)

class ARTSReg(dict):
    def __init__(self, reg_uuid, rt_uuid, rt_name, action):
        dict.__init__(self, object_id=str(reg_uuid), action=action, type='arts_req', data={ 'type': 'runtime', 'object_id': str(rt_uuid), 'name': rt_name})

class Result():
    ok = 'ok'
    err = 'error'

class Action():
    create = 'create'
    delete = 'delete'
