
import paho.mqtt.client as mqtt
import threading
import json 
import uuid
import time

import clauncher.settings as settings
from clauncher.runtime import RuntimeView
from clauncher.msgdefs import Action, Result, ARTSResponse
from clauncher.modules import ModulesControl, ModulesView
from clauncher.launcher import ModuleLaucher

class MqttManager(mqtt.Client):

    def __init__(self, rt):
        super(MqttManager, self).__init__(str(rt.uuid))
        self.runtime = rt 
        self.Modules = ModulesControl(rt)
        self.reg_attempts = 0
        
        # parse settings
        for t in settings.s_dict['topics']:
            if (t['type'] == 'reg'):
                self.reg_topic = t['topic']
            if (t['type'] == 'ctl'):
                self.ctl_topic = t['topic']
            if (t['type'] == 'dbg'):
                self.dbg_topic = t['topic']
        
    def wait_timeout(self, tevent, stime, callback):
        print('****waiting')
        time.sleep(stime)
        if tevent.isSet() == False:
            callback()
    
    # TODO: do not start a new thread for each timeout
    def set_timeout(self, timeout, callback):
        timeout_event = threading.Event()
        t = threading.Thread(target=self.wait_timeout, args=(timeout_event, timeout, callback))
        t.start()
        return timeout_event

    def register_rt(self):
        # this will use the current runtime uuid as the object id
        self.reg_uuid = uuid.uuid4()
        reg_msg = RuntimeView().json_reg(self.reg_uuid, self.runtime, Action.create)
        print('Registering: ', reg_msg)
        self.publish(self.reg_topic, reg_msg)
        self.reg_attempts += 1
        if (settings.s_dict['runtime']['reg_attempts'] == 0 or settings.s_dict['runtime']['reg_attempts'] > self.reg_attempts):        
            self.reg_done = self.set_timeout(settings.s_dict['runtime']['reg_timeout_seconds'], self.register_rt)

    def on_connect(self, mqttc, obj, flags, rc):
        print('registering runtime')         
        try: 
            self.register_rt()
        except Exception as err:
            print(err)
        
    def on_message(self, mqttc, obj, msg):
        print(msg.topic+" "+str(msg.qos)+" "+str(msg.payload))
        
        str_payload = str(msg.payload.decode("utf-8","ignore"))
        
        if (len(str_payload) == 0): # ignore 0-len payloads
            return
        
        # reg_topic msg 
        if (msg.topic == self.reg_topic):
            try:
                reg_msg = json.loads(str_payload) # convert json payload to a python string, then to dictionary
            except Exception as err:
                print('Error parsing message to reg:', err)
                return
             
            if (reg_msg['type'] != 'arts_resp'): # silently return if type is not arts_resp!
                return
            
            # we are only interested in reg message confirming our registration 
            if reg_msg['object_id'] != str(self.reg_uuid):
                return

            # check if result was ok
            if reg_msg['data']['result'] != Result.ok:
                print('Register failed; Retrying') # we do not set the reg timeout event, so will try again
                return
            
            # cancel timeout; will not retry reg again
            self.reg_done.set()
            
            try:
                rcv_rt_instance = json.loads(reg_msg['data']['details'])
            except Exception as err:
                print('Error parsing message to reg:', err)
                return

            # unsubscribe from reg topic and subscribe to ctl/runtime_uuid
            self.unsubscribe(self.reg_topic)
            self.ctl_topic += '/' + str(self.runtime.uuid)
            self.subscribe(self.ctl_topic)
            
        # ctl_topic msg 
        if (msg.topic == self.ctl_topic):
            try:
                ctl_msg = json.loads(str_payload) # convert json payload to a python string, then to dictionary
            except Exception as err:
                print('Error parsing message to ctl:', err)
                return
            
            # {"object_id": "3f02c335-f66a-4322-b748-e44ef50b3d43", "action": "create", "type": "arts_req", "data": {"type": "module", "details": "{\"uuid\": \"59484356-038c-4b09-af0f-7cdda72d238d\", \"name\": \"module1\", \"parent\": '60f6c17d-48b7-4919-b5f1-571c62b4a55b", \"filename\": \"test.wasm\", \"args\": \"\"}"}
            if (ctl_msg['type'] == 'arts_req'):
                if (ctl_msg['action'] == 'create' and ctl_msg['data']['type'] == 'module'):
                    try:
                        rcv_mod_instance = json.loads(ctl_msg['data']['details'])
                    except Exception as err:
                        print('Error parsing message to ctl:', err)
                        return  

                    print("rcv_mod_instance: ", rcv_mod_instance)
                          
                    try:            
                        print("1")
                        print(rcv_mod_instance['uuid'])
                        mod = self.Modules.create(rcv_mod_instance['uuid'],rcv_mod_instance['name'], rcv_mod_instance['filename'],rcv_mod_instance['fileid'],rcv_mod_instance['filetype'],rcv_mod_instance['args'])
                        print("2")
                        m = ModuleLaucher()
                        print("3")
                        delete_req_json = ModulesView().json_req(mod, Action.delete) 
                        print("4")
                        m.run(mod, self.dbg_topic, self.reg_topic, delete_req_json)
                        print("5")
                    except Exception as err:
                        print('Error creating new module:', err)                        
                        resp = ARTSResponse(ctl_msg['object_id'],Result.err, 'Module could not be created; {1}'.format(err))
                        self.publish(self.ctl_topic, json.dumps(resp))
                        return                      

                    print('Sending Confirmation!')
                    resp = ARTSResponse(ctl_msg['object_id'],Result.ok, json.dumps(str(mod)))
                    self.publish(self.ctl_topic, json.dumps(resp))
        
    def on_publish(self, mqttc, obj, mid):
        print("mid: "+str(mid))

    def on_subscribe(self, mqttc, obj, mid, granted_qos):
        print("Subscribed: "+str(mid)+" "+str(granted_qos))

    def on_log(self, mqttc, obj, level, string):
        print(string)

    def start(self, host):
        print('Connecting to:', host)
        # register last will
        self.will_set(self.reg_topic, str(RuntimeView().json_reg(uuid.uuid4(), self.runtime, Action.delete)), 0, False)        
        self.connect(host, 1883, 60)    
        # subscribe to reg topic     
        self.subscribe(self.reg_topic)
        self.loop_start()
        
                