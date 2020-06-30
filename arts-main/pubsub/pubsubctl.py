'''
Handle pubsub messages

Message definitions:
https://docs.google.com/presentation/d/1HJaQPFMV_sUyMLoiXciZn9KVTCNXCgQ5LeNxbp_Vf2U/edit?usp=sharing
''' 
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
                print("***", reg_msg);
                try:
                    reg_data = reg_msg['data']
                    if 'uuid' in reg_data: 
                        rt_uuid = uuid.UUID(reg_data['uuid'])
                    else: 
                        rt_uuid = uuid.uuid4()
                    rt_name = reg_data.get("name", Runtime._meta.get_field('name').default) 
                    rt_max_nmodules = reg_data.get("max_nmodules", Runtime._meta.get_field('max_nmodules').default) 
                    rt_apis = reg_data.get("apis", Runtime._meta.get_field('apis').default)  
                    a_rt = Runtime.objects.create(uuid=rt_uuid, name=rt_name, max_nmodules=rt_max_nmodules, apis=rt_apis)
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
                print(reg_msg)  
                try:
                    a_uuid = uuid.UUID(reg_msg['data']['uuid'])
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
                
    def on_ctl_message(self, msg):
        try:
            str_payload = str(msg.payload.decode("utf-8","ignore"))
            if (str_payload[0] == "'"):
                str_payload = str_payload[1:len(str_payload)-1]
            ctl_msg = json.loads(str_payload) # convert json payload to a python string, then to dictionary
        except Exception as err:
            try:
                resp = ARTSResponse('could_not_parse', Result.err, 'Could not process request; {0}'.format(err))
            except Exception as err1:
                print(err1)
            print(json.dumps(resp))
            self.mqtt_client.publish(msg.topic, json.dumps(resp))
        
        if (ctl_msg['type'] != 'arts_req'): # silently return if type is not arts_req!
            return
        
        if (ctl_msg['action'] == 'create'):
            if (ctl_msg['data']['type'] == 'module'):
                parent_rt=None
                
                if ('parent' in ctl_msg['data']):
                    try:
                        parent_rt = Runtime.objects.get(pk=ctl_msg['data']['parent']['uuid']) # honor parent, if given
                    except Exception as err:
                        print('Exception:',err)
                
                if (parent_rt == None):
                    try:
                        parent_rt = self.scheduler.schedule_new_module()
                    except Exception as err:
                        print('Exception:',err)
    
                try:
                    ctl_data = ctl_msg['data']
                    mod_name = ctl_data.get('name', Module._meta.get_field('name').default)
                    mod_uuid = None
                    if 'uuid' in ctl_data: 
                        mod_uuid = uuid.UUID(ctl_data['uuid'])
                    else:
                        mod_uuid = uuid.uuid4()
                    mod_filename = ctl_data.get('filename', Module._meta.get_field('filename').default)
                    mod_fileid = ctl_data.get('fileid', Module._meta.get_field('fileid').default)
                    mod_filetype = ctl_data.get('filetype', Module._meta.get_field('filetype').default)
                    mod_args = ctl_data.get('args', Module._meta.get_field('args').default)
                    mod_env = ctl_data.get('env', Module._meta.get_field('env').default)
                    mod_channels = ctl_data.get('channels', Module._meta.get_field('channels').default)
                    a_mod = Module.objects.create(uuid=mod_uuid,
                                                  name=mod_name, 
                                                  filename=mod_filename, 
                                                  fileid=mod_fileid, 
                                                  filetype=mod_filetype,
                                                  parent=parent_rt, 
                                                  args=mod_args,
                                                  env=mod_env,
                                                  channels=mod_channels)
                except Exception as err:
                    resp = json.dumps(ARTSResponse(ctl_msg['object_id'],Result.err, 'Module could not be created. {0}'.format(err)))
                    self.mqtt_client.publish(msg.topic, resp)
                else:
                    # request module start
                    mod_req = json.dumps(ARTSRequest(Action.create, ModuleSerializer(a_mod, many=False).data ))
                    print('Requesting module creation to parent: ', mod_req, ' to: ', msg.topic + "/" + str(parent_rt.uuid))
                    self.mqtt_client.publish(msg.topic + "/" + str(parent_rt.uuid), mod_req)
                    
                #     # TODO: check if module was started at the runtime (read back result on the mqtt topic)

                # send response
                resp = json.dumps(ARTSResponse(ctl_msg['object_id'], Result.ok, ModuleSerializer(a_mod, many=False).data ))
                print('Created Module; Publishing: ', resp, ' to: ', msg.topic)
                self.mqtt_client.publish(msg.topic, resp)

        if (ctl_msg['action'] == 'delete'):
            if (ctl_msg['data']['type'] == 'module'):
                snd_rt = None
                old_rt_uuid = None
                try:
                    a_uuid = uuid.UUID(ctl_msg['data']['uuid'])
                    a_mod = Module.objects.get(pk=a_uuid)
                    old_rt_uuid = a_mod.parent.uuid
                    if ('send_to_runtime' in ctl_msg['data']):
                        snd_rt = Runtime.objects.get(pk=ctl_msg['data']['send_to_runtime']) # get parent runtime, if given
                except Exception as err:
                    resp = json.dumps(ARTSResponse(ctl_msg['object_id'],Result.err, 'Module ({0}) could not be deleted; {1}'.format(str(a_uuid),err)))
                    self.mqtt_client.publish(msg.topic, resp)
                else:
                    # request module delete
                    new_req = ARTSRequest(Action.delete, ModuleSerializer(a_mod, many=False).data );
                    if (snd_rt != None):
                        a_mod.parent.nmodules -= 1 # have to decrease number of modules
                        a_mod.parent.save(update_fields=['nmodules'])
                        a_mod.parent = snd_rt # later module save will increase number of modules (signals.py)
                        new_req['send_to_runtime'] = str(snd_rt.uuid)
                        
                    mod_req = json.dumps(new_req)
                    print('Requesting module delete to parent: ', mod_req, ' to: ', msg.topic + "/" + str(old_rt_uuid))
                    self.mqtt_client.publish(msg.topic + "/" + str(old_rt_uuid), mod_req)
                        
                    # TODO: check if module was deleted at the runtime (read back result on the mqtt topic)
                    
                    if (snd_rt == None):
                        a_mod.delete()
                    else:
                        a_mod.save()
                        
                        
                        
    def on_dbg_message(self, msg):
        print('on_dbg_message:'+msg.topic+" "+str(msg.qos)+" "+str(msg.payload))
