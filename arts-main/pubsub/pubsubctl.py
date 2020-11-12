'''
Handle pubsub messages

Message definitions:
https://docs.google.com/presentation/d/1HJaQPFMV_sUyMLoiXciZn9KVTCNXCgQ5LeNxbp_Vf2U/edit?usp=sharing
''' 
import paho.mqtt.client as mqtt
from arts_core.models import Runtime, Module, Link, FileType
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
            #TODO: Allow for response messages from module
            return
        
        parent_rt=None
        if (ctl_msg['action'] == 'create'):
            if (ctl_msg['data']['type'] == 'module'):
                
                
                if ('parent' in ctl_msg['data']):
                    try:
                        parent_rt = Runtime.objects.get(pk=ctl_msg['data']['parent']['uuid']) # honor parent, if given
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
                    mod_peripherals = ctl_data.get('peripherals', Module._meta.get_field('peripherals').default)
                    # get apis if given, or infer from filetype
                    mod_apis=None
                    if ('apis' in ctl_data):
                        mod_apis = ctl_data['apis']
                    else: 
                        if (mod_filetype == FileType.WA):
                            mod_apis = "[\"wasi:snapshot_preview1\"]"
                        elif (mod_filetype == FileType.PY):   
                            mod_apis = "[\"python:python3\"]"
                          
                    a_mod = Module(uuid=mod_uuid,
                                                  name=mod_name, 
                                                  filename=mod_filename, 
                                                  fileid=mod_fileid, 
                                                  filetype=mod_filetype,
                                                  apis=mod_apis,
                                                  parent=parent_rt, 
                                                  args=mod_args,
                                                  env=mod_env,
                                                  channels=mod_channels,
                                                  peripherals=mod_peripherals)
                except Exception as err:
                    resp = json.dumps(ARTSResponse(ctl_msg['object_id'],Result.err, 'Module could not be created. {0}'.format(err)))
                    self.mqtt_client.publish(msg.topic, resp)
                else:
                    try:
                        if (parent_rt == None):
                            # schedule the module
                            parent_rt = self.scheduler.schedule_new_module(a_mod)
                    except Exception as err:
                        print('Scheduler error: ',err)
                        resp = json.dumps(ARTSResponse(ctl_msg['object_id'],Result.err, 'Error Scheduling module. {0}'.format(err)))
                        self.mqtt_client.publish(msg.topic, resp)
                    else:    
                        a_mod.parent = parent_rt
                        
                        # request module start
                        mod_req = ARTSRequest(Action.create, ModuleSerializer(a_mod, many=False).data)

                        # Convert array fields into actual arrays.
                        if 'apis' in mod_req['data']:
                            apis_string = mod_req['data']['apis'].replace("'", '"')
                            try:
                                mod_req['data']['apis'] = json.loads(apis_string)
                            except:
                                pass
                        if 'args' in mod_req['data']:
                            args_string = mod_req['data']['args'].replace("'", '"')
                            try:
                                mod_req['data']['args'] = json.loads(args_string)
                            except:
                                pass
                        if 'env' in mod_req['data']:
                            env_string = mod_req['data']['env'].replace("'", '"')
                            try:
                                mod_req['data']['env'] = json.loads(env_string)
                            except:
                                pass
                        if 'channels' in mod_req['data']:
                            channels_string = mod_req['data']['channels'].replace("'", '"')
                            try:
                                mod_req['data']['channels'] = json.loads(channels_string)
                            except:
                                pass
                        if 'peripherals' in mod_req['data']:
                            peripherals_string = mod_req['data']['peripherals'].replace("'", '"')
                            try:
                                mod_req['data']['peripherals'] = json.loads(peripherals_string)
                            except:
                                pass

                        mod_req = json.dumps(mod_req)

                        print('Requesting module creation to parent: ', mod_req, ' to: ', msg.topic + "/" + str(parent_rt.uuid))
                        self.mqtt_client.publish(msg.topic + "/" + str(parent_rt.uuid), mod_req)
                        
                        # TODO: check if module was started at the runtime (read back result on the mqtt topic)

                        a_mod.save() # save the module

                        # send response
                        resp = ARTSResponse(ctl_msg['object_id'], Result.ok, ModuleSerializer(a_mod, many=False).data)
                       
                        # Convert array fields into actual arrays.
                        if 'apis' in resp['data']['details']:
                            apis_string = resp['data']['details']['apis'].replace("'", '"')
                            try:
                                resp['data']['details']['apis'] = json.loads(apis_string)
                            except:
                                pass
                        if 'args' in resp['data']['details']:
                            args_string = resp['data']['details']['args'].replace("'", '"')
                            try:
                                resp['data']['details']['args'] = json.loads(args_string)
                            except:
                                pass
                        if 'env' in resp['data']['details']:
                            env_string = resp['data']['details']['env'].replace("'", '"')
                            try:
                                resp['data']['details']['env'] = json.loads(env_string)
                            except:
                                pass
                        if 'channels' in resp['data']['details']:
                            channels_string = resp['data']['details']['channels'].replace("'", '"')
                            try:
                                resp['data']['details']['channels'] = json.loads(channels_string)
                            except:
                                pass
                        if 'peripherals' in resp['data']['details']:
                            peripherals_string = resp['data']['details']['peripherals'].replace("'", '"')
                            try:
                                resp['data']['details']['peripherals'] = json.loads(peripherals_string)
                            except:
                                pass

                        resp = json.dumps(resp)
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
