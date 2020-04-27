import json
import uuid

class ARTSResponse(dict):
    def __init__(self, r_uuid, result, details):
        dict.__init__(self, object_id=str(r_uuid), type='arts_resp', data={ 'result': result, 'details': details})

class ARTSRequest(dict):
    def __init__(self, action, type, obj_uuid):
        dict.__init__(self, object_id=str(uuid.uuid4()), action=action, type='arts_req', data={ 'type': type, 'object_id': obj_uuid})
        
class ARTSReg(dict):
    def __init__(self, reg_uuid, rt_uuid, rt_name, rt_max_nmodules, rt_apis, action):
        dict.__init__(self, object_id=str(reg_uuid), action=action, type='arts_req', data={ 'type': 'runtime', 'object_id': str(rt_uuid), 'name': rt_name, 'max_nmodules': str(rt_max_nmodules), 'apis':rt_apis})

class Result():
    ok = 'ok'
    err = 'error'

class Action():
    create = 'create'
    delete = 'delete'
