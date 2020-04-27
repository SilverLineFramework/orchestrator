'''
*TL;DR
Tests for Runtimes
'''

from clauncher.modules import ModulesControl, ModuleView
from clauncher.utils import Actions

import unittest
import json

class ModulesControlTestSuite(unittest.TestCase):
    '''Modules Model Tests'''

    def test_create_module_stores_module(self):
        mm = ModulesControl(None)
        mm.create('uuid1', 'name1')
        mods = list(mm)
        print(mods)
        assert(mods == [{'uuid': 'uuid1', 'name': 'name1', 'parent': None, 'filename': '', 'filetype': 'WASM'}])

    def test_create_two_modules_stores_them(self):
        mm = ModulesControl(None)
        mm.create('uuid1', 'name1')
        mm.create('uuid2', 'name2')
        mods = list(mm)
        assert(mods == [{'uuid': 'uuid1', 'name': 'name1', 'parent': None, 'filename': '', 'filetype': 'WASM'}, {'uuid': 'uuid2', 'name': 'name2', 'parent': None, 'filename': '', 'filetype': 'WASM'}])

    def test_create_missing_uuid_throws_exception(self):
        mm = ModulesControl(None)
        with self.assertRaises(TypeError):
            mm.create('name1')

    def test_create_duplicate_uuid_throws_exception(self):
        mm = ModulesControl(None)
        mm.create('uuid1', 'name')
        with self.assertRaises(Exception):
            mm.create('uuid1', 'name1')

    def test_read_two_modules_returns_them(self):
        mm = ModulesControl(None)
        mm.create('uuid1', 'name1')
        mm.create('uuid2', 'name2')
        mod1 = mm.read('uuid1')
        assert(mod1 == {'uuid': 'uuid1', 'name': 'name1', 'parent': None, 'filename': '', 'filetype': 'WASM'})
        mod1 = mm.read('uuid2')
        assert(mod1 == {'uuid': 'uuid2', 'name': 'name2', 'parent': None, 'filename': '', 'filetype': 'WASM'})
        
    def test_update_module_updates_it(self):
        mm = ModulesControl(None)
        mm.create('uuid1', 'name')
        mm.update('uuid1', 'new_name')
        mods = list(mm)
        assert(mods == [{'uuid': 'uuid1', 'name': 'new_name', 'parent': None, 'filename': '', 'filetype': 'WASM'}])

    def test_update_two_modules_updates_them(self):
        mm = ModulesControl(None)
        mm.create('uuid1', 'name1')
        mm.create('uuid2', 'name2')        
        mm.update('uuid1', 'new_name1')
        mm.update('uuid2', 'new_name2')
        mods = list(mm)
        assert(mods == [{'uuid': 'uuid1', 'name': 'new_name1', 'parent': None, 'filename': '', 'filetype': 'WASM'}, {'uuid': 'uuid2', 'name': 'new_name2', 'parent': None, 'filename': '', 'filetype': 'WASM'}])

    def test_delete_module_deletes_it(self):
        mm = ModulesControl(None)
        mm.create('uuid1', 'name1')
        mm.delete('uuid1')
        mods = list(mm)
        assert(mods == [])

    def test_delete_module_from_list_deletes_it(self):
        mm = ModulesControl(None)
        mm.create('uuid1', 'name1')
        mm.create('uuid2', 'name2')
        mm.create('uuid3', 'name3')                
        mm.delete('uuid1')
        mods = list(mm)
        print(mods)
        assert(mods == [{'uuid': 'uuid2', 'name': 'name2', 'parent': None, 'filename': '', 'filetype': 'WASM'}, {'uuid': 'uuid3', 'name': 'name3', 'parent': None, 'filename': '', 'filetype': 'WASM'}])
        
class RuntimesViewTestSuite(unittest.TestCase):
    '''Runtimes View Tests'''
    
    def test_json_graph_item_returns_valid_json(self):
        mm = ModulesControl(None)
        mod1 = mm.create('uuid1', 'name1')
        mv = ModuleView()
        mod_json = mv.json_graph_item(mod1, Actions.create)
        assert(mod_json == json.dumps({'uuid': 'uuid1', 'name': 'name1', 'action': 'create', 'data': { 'type': 'module', 'parent': None, 'filename': '', 'filetype': 'WASM'}}))
        
if __name__ == '__main__':
    unittest.main()
