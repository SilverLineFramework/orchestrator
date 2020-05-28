import paho.mqtt.client as mqtt
from arts_core.models import Runtime, Module, Link
from arts_core.serializers import RuntimeSerializer, ModuleSerializer, LinkSerializer
import json
import uuid
from pubsub.msgdefs import ARTSResponse, ARTSRequest, Action, Result

class ARTSMQTTCtl():
    
    def set_mqtt_client(self, mqtt_client):
        self.mqtt_client = mqtt_client

    def set_scheduler(self, scheduler):
        self.scheduler = scheduler
    
    def on_reg_message(self, msg):
        '''
        Register runtime messages:
            { "object_id": "<request uuid; randomly generated>", "action": "create",  "type": "arts_req",  "data": { "type":"runtime", "name": "runtime1" } } 
                response to same topic: { "object_id": "<request uuid>","type": "arts_resp",  "data": { "result": "ok|error" "details": "{<serialized instance>}|<error_msg>" } } 
            { "object_id":"<request uuid>", "action": "delete" }
                response to same topic: { "object_id": "<request uuid>", "type": "arts_resp",  "data": { "result": "ok|error", "details": "{<serialized instance>}|<error_msg>" } } 
        ''' 
        try:
            str_payload = str(msg.payload.decode("utf-8","ignore"))
            if (str_payload[0] == "'"):
                str_payload = str_payload[1:len(str_payload)-1]
            reg_msg = json.loads(str_payload) # convert json payload to a python string, then to dictionary
        except Exception as err:
            try:
                resp = ARTSResponse('could_not_parse', Result.err, 'Could not process request; {0}'.format(err))
            except Exception as err1:
                print(err1)
            print(json.dumps(resp))
            self.mqtt_client.publish(msg.topic, json.dumps(resp))
            
        if (reg_msg['type'] != 'arts_req'): # silently return if type is not arts_req!
            return
         
        if (reg_msg['action'] == 'create'):                
            if (reg_msg['data']['type'] == 'runtime'):
                try:
                    reg_data = reg_msg['data']
                    rt_uuid = reg_data.get("object_id", Runtime._meta.get_field('uuid').default) 
                    rt_name = reg_data.get("name", Runtime._meta.get_field('name').default) 
                    rt_max_nmodules = reg_data.get("max_nmodules", Runtime._meta.get_field('max_nmodules').default) 
                    rt_apis = reg_data.get("apis", Runtime._meta.get_field('apis').default)  
                    a_rt = Runtime.objects.create(uuid=uuid.UUID(rt_uuid), name=rt_name, max_nmodules=rt_max_nmodules, apis=rt_apis)
                except Exception as err:
                    resp = ARTSResponse(reg_msg['object_id'],Result.err, 'Runtime could not be created {0}'.format(err))
                    print(json.dumps(resp))
                    self.mqtt_client.publish(msg.topic, json.dumps(resp))
                else:
                    try:               
                        #json_serialized = json.dumps(RuntimeSerializer(a_rt, many=False).data)
                        #resp = ARTSResponse(reg_msg['object_id'], Result.ok, json_serialized)
                        resp = json.dumps(ARTSResponse(reg_msg['object_id'], Result.ok, RuntimeSerializer(a_rt, many=False).data))                        
                    except Exception as err:
                        print(err)
                    print(resp)
                    #print('Created; Publishing: ', json.dumps(resp), ' to: ', msg.topic)
                    #self.mqtt_client.publish(msg.topic, json.dumps(resp))
                    print('Created; Publishing: ', resp, ' to: ', msg.topic)
                    self.mqtt_client.publish(msg.topic, resp)
            
        if (reg_msg['action'] == 'delete'):
            if (reg_msg['data']['type'] == 'runtime'):         
                try:
                    a_uuid = uuid.UUID(reg_msg['data']['object_id'])
                    a_rt = Runtime.objects.get(pk=a_uuid)
                except Exception as err:
                    resp = json.dumps(ARTSResponse(reg_msg['object_id'],Result.err, 'Runtime ({0}) could not be deleted; {1}'.format(str(a_uuid),err)))
                    self.mqtt_client.publish(msg.topic, resp)
                else:
                    resp = json.dumps(ARTSResponse(reg_msg['object_id'], Result.ok, RuntimeSerializer(a_rt, many=False).data))
                    a_rt.delete()
                    print(resp)
                    print('Deleted; Publishing: ', resp, ' to: ', msg.topic + "/" + str(a_uuid))
                    self.mqtt_client.publish(msg.topic, resp)

            if (reg_msg['data']['type'] == 'module'):         
                try:
                    a_uuid = uuid.UUID(reg_msg['data']['object_id'])
                    a_mod = Module.objects.get(pk=a_uuid)
                except Exception as err:
                    resp = json.dumps(ARTSResponse(reg_msg['object_id'],Result.err, 'Module ({0}) could not be deleted; {1}'.format(str(a_uuid),err)))
                    print(resp)
                    self.mqtt_client.publish(msg.topic, resp)
                else:
                    resp = json.dumps(ARTSResponse(reg_msg['object_id'], Result.ok, ModuleSerializer(a_mod, many=False).data))
                    a_mod.delete()
                    print(resp)
                    print('Deleted; Publishing: ', resp, ' to: ', msg.topic + "/" + str(a_uuid))
                    self.mqtt_client.publish(msg.topic, resp)
                
    def on_ctl_message(self, msg):
        '''
        ARTS Control messages (sent from clients, asking to CRD modules):
            { "object_id":"<request uuid>", "action": "create", "type": "module", "data": { "type":"module", "name": "<module name>", "filename": ".wasm file", "fileid": "file id", "filetype": "PY|WASM", "parent_object_id": "<runtime uuid where to run; optional>", "args": "module args"} }
                response to same topic: { "object_id": "<request uuid>", "type": "arts_resp",  "data": { "result": "ok|error", "details": "{<serialized instance>}|<error_msg>" } } 
            { "object_id":"<module uuid>", "action": "delete", "type": "module" }
                response to same topic: { "object_id": "<request uuid>", "type": "arts_resp",  "data": { "result": "ok|error", "details": "{<serialized instance>}|<error_msg>" } } 
            { "object_id":"<module uuid>", "action": "update", "type": "module" "data": { "parent": "<runtime uuid where to run; optional>"} }
                response to same topic: { "object_id": "<request uuid>", "type": "arts_resp",  "data": { "result": "ok|error", "details": "{<serialized instance>}|<error_msg>" } }                 
        '''
        
        ctl_msg = json.loads(str(msg.payload.decode("utf-8","ignore"))) # convert json payload to a python string, then to dictionary
        
        if (ctl_msg['action'] == 'create'):
            if (ctl_msg['data']['type'] == 'module'):
                parent_rt=None
                if ('parent_object_id' in ctl_msg['data']):
                    parent_rt = Runtime.objects.get(pk=ctl_msg['data']['parent_object_id']) # honor parent, if given
                else:
                    try:
                        parent_rt = self.scheduler.schedule_new_module()
                    except Exception as err:
                        print('Exception:',err)
                
                m_args = ''
                if 'args' in ctl_msg['data']: 
                    m_args = ctl_msg['data']['args']
    
                try:
                    ctl_data = ctl_msg['data']
                    mod_name = ctl_data.get('name', Module._meta.get_field('name').default)
                    mod_filename = ctl_data.get('filename', Module._meta.get_field('filename').default)
                    mod_fileid = ctl_data.get('fileid', Module._meta.get_field('fileid').default)
                    mod_filetype = ctl_data.get('filetype', Module._meta.get_field('filetype').default)
                    mod_args = ctl_data.get('args', Module._meta.get_field('args').default)
                    a_mod = Module.objects.create(name=mod_name, 
                                                  filename=mod_filename, 
                                                  fileid=mod_fileid, 
                                                  filetype=mod_filetype,
                                                  parent=parent_rt, 
                                                  args=mod_args)
                except Exception as err:
                    resp = json.dumps(ARTSResponse(ctl_msg['object_id'],Result.err, 'Module could not be created. {0}'.format(err)))
                    self.mqtt_client.publish(msg.topic, resp)
                else:
                    # request module start
                    mod_req = json.dumps(ARTSRequest(Action.create, 'module', ModuleSerializer(a_mod, many=False).data ))
                    print('Requesting module creation to parent: ', mod_req, ' to: ', msg.topic + "/" + str(parent_rt.uuid))
                    self.mqtt_client.publish(msg.topic + "/" + str(parent_rt.uuid), mod_req)
                    
                #     # TODO: check if module was started at the runtime (read back result on the mqtt topic)

                # send response
                resp = json.dumps(ARTSResponse(ctl_msg['object_id'], Result.ok, ModuleSerializer(a_mod, many=False).data ))
                print('Created Module; Publishing: ', resp, ' to: ', msg.topic)
                self.mqtt_client.publish(msg.topic, resp)
                    
            #if (reg_msg['action'] == 'create'):
        
    def on_dbg_message(self, msg):
        print('on_dbg_message:'+msg.topic+" "+str(msg.qos)+" "+str(msg.payload))
