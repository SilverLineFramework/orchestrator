"""
*TL;DR
Connects to mqtt; Routes mqtt messages to the view
"""
import paho.mqtt.client as mqtt
from queue import Queue
import unittest
import json
import time

import pubsub.views

CONFIG_FILE='pubsub/config.json'

class MqttViewTestSuite(unittest.TestCase):

    def setUp(self): 
        self.mqttc = mqtt.Client()
        self.mqttc.on_message = self.on_message
        self.mqttc.on_log = self.on_log
                
        with open(CONFIG_FILE) as json_file:
            self.config = json.load(json_file)
        
        self.topics = {}
        self.q = Queue()
        
        '''
        subscribe to each topic in the config file
        '''
        self.mqttc.connect(self.config['mqtt_server']['host'], 1883, 60)
        for t in self.config['subscribe_topics']:
            print('Subscribing:', t['topic'])
            self.mqttc.subscribe(t['topic'], 0)
            topic_type = t['on_message'][3:6] # NOTE: assumes handlers are called 'on_xxx'
            self.topics[topic_type] = t['topic'] 
                
    def on_message(self, mqttc, obj, msg):
        print("msg: "+str(msg))
        self.q.put(msg)

    def on_log(self, mqttc, obj, level, string):
        print(string)

    # TODO: Need to startup app to test these
    # def test_create_runtime(self):
    #     rt_msg = { "object_id": "64c41912-4daf-11ea-b77f-2e728ce88821", "action": "create", "type": "arts_req", "data": { "type":"runtime", "name": "runtime1" } }
    #     # send create runtime message to reg topic
    #     self.mqttc.publish(self.topics['reg'], str(rt_msg))
    #     response = self.q.get()
    #     print(str(response))
        
