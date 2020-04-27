"""
*TL;DR
Runtime classe; Store information about the runtime
"""

from clauncher.msgdefs import ARTSReg
import json
import uuid

class Runtime(dict):
    type = 'runtime'
    def __init__(self, rt_name, rt_uuid=uuid.uuid4(), rt_max_nmodules=3, rt_apis=['wasi:snapshot_preview1', 'python:core']):
        dict.__init__(self, uuid=rt_uuid, name=rt_name, max_nmodules=rt_max_nmodules, apis=rt_apis)

    @property
    def uuid(self):    
        return self['uuid']

    @uuid.setter
    def uuid(self, rt_uuid):    
        self['uuid'] = rt_uuid
    
    @property
    def name(self):    
        return self['name']

    @name.setter
    def name(self, rt_name):    
        self['name'] = rt_name

    @property
    def max_nmodules(self):    
        return self['max_nmodules']

    @max_nmodules.setter
    def max_nmodules(self, rt_max_nmodules):    
        self['max_nmodules'] = rt_max_nmodules

    @property
    def apis(self):    
        return self['apis']

    @apis.setter
    def apis(self, rt_apis):    
        self['apis'] = rt_apis
        
class RuntimeView():
    def json_item_list(self, item_list):
        return json.dumps(item_list)
                    
    def json_reg(self, reg_uuid, runtime, action):
        return json.dumps(ARTSReg(reg_uuid, runtime.uuid, runtime.name, runtime.max_nmodules, runtime.apis, action))