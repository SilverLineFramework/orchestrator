"""
*TL;DR
Module classes; Store information about the wasm modules running 
"""

import json
from clauncher.utils import FileTypes 
from clauncher.msgdefs import ARTSRequest

class Module(dict):
    type = 'module'
    def __init__(self, mod_uuid, mod_name, parent_rt=None, mod_fn='', mod_fid='', mod_ft=FileTypes.WA, mod_args=''):
        dict.__init__(self, uuid=mod_uuid, name=mod_name, parent=parent_rt, filename=mod_fn, fileid=mod_fid, filetype=mod_ft, args=mod_args)

    @property
    def uuid(self):    
        return self['uuid']

    @uuid.setter
    def uuid(self, mod_uuid):    
        self['uuid'] = mod_uuid
    
    @property
    def name(self):    
        return self['name']

    @name.setter
    def name(self, mod_name):    
        self['name'] = mod_name

    @property
    def parent(self):    
        return self['parent']

    @parent.setter
    def parent(self, parent_rt):    
        self['parent'] = parent_rt

    @property
    def filename(self):    
        return self['filename']

    @filename.setter
    def filename(self, fn):    
        self['filename'] = fn

    @property
    def filetype(self):    
        return self['filetype']

    @filetype.setter
    def filetype(self, ft):    
        self['filetype'] = ft

    @property
    def fileid(self):    
        return self['fileid']

    @fileid.setter
    def fileid(self, fid):    
        self['fileid'] = fid

    @property
    def args(self):    
        return self['args']

    @args.setter
    def args(self, m_args):    
        self['args'] = m_args
                                                            
class ModulesControl():
    def __init__(self, parent_rt):
        self.modules = [] # list of modules
        self.parent = parent_rt
    
    def __iter__(self):
        for module in self.modules:
            yield module
        
    def create(self, module_uuid, module_name, fn='', fid='', ft=FileTypes.WA, args=''):
        rt = list(filter(lambda i: i.uuid == module_uuid, self.modules))
        if rt:
            raise Exception('UUID {} already exists'.format(module_uuid))
        else:
            # create module
            module = Module(module_uuid, module_name, self.parent, fn, fid, ft, args)
            self.modules.append(Module(module_uuid, module_name))
            return module

    def read(self, module_uuid):
        rt = list(filter(lambda i: i.uuid == module_uuid, self.modules))
        if rt:
            return rt[0]
        else:
            raise Exception('UUID {} not found'.format(module_uuid)) 
        
    def update(self, module_uuid, module_name, fn='', fid='', ft=FileTypes.WA, args=''):
        module_idx = list(filter(lambda i_i: i_i[1].uuid == module_uuid, enumerate(self.modules)))
        if module_idx:
            i, module_to_update = module_idx[0][0], module_idx[0][1]
            self.modules[i] = Module(module_uuid, module_name)
        else:
            raise Exception('UUID {} not found'.format(module_uuid)) 

    def update_obj(self, module_obj):
        module_idx = list(filter(lambda i_i: i_i[1].uuid == module_obj.uuid, enumerate(self.modules)))
        if module_idx:
            i, module_to_update = module_idx[0][0], module_idx[0][1]
            self.modules[i] = module_obj
        else:
            raise Exception('UUID {} not found'.format(module_obj.uuid)) 
                
    def delete(self, module_uuid):
        module_idx = list(filter(lambda i_i: i_i[1].uuid == module_uuid, enumerate(self.modules)))
        if module_idx:
            i, rt_to_delete = module_idx[0][0], module_idx[0][1]
            del self.modules[i]
        else:
            raise Exception('UUID {} not found'.format(module_uuid)) 
            
class ModulesView():
    def json_item_list(self, item_list):
        return json.dumps(item_list)
                    
    def json_graph_item(self, module, action):
        return json.dumps({'uuid': str(module.uuid), 'name': module.name, 'action': action, 'data': { 'type': module.type, 'parent': module.parent, 'filename': module.filename, 'fileid': module.fileid, 'filetype': module.filetype, 'args': module.args}})

    def json_req(self, module, action):
        return json.dumps(ARTSRequest(action, 'module', str(module.uuid)))
