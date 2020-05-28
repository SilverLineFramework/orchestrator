"""
*TL;DR
Connects to mqtt; Routes mqtt messages to the view
"""
import paho.mqtt.client as mqtt
import json
import time

CONFIG_FILE='pubsub/config.json'

class MqttListner(mqtt.Client):

    def __init__(self, view_class, cid='', conn_subs=True, ):
        super(MqttListner, self).__init__(cid)
        
        import pubsub.pubsubctl
        
        with open(CONFIG_FILE) as json_file:
            self.config = json.load(json_file)
        
        if (conn_subs):
            self.connect_and_subscribe()

        view_class.set_mqtt_client(self) # tell the view we are the mqtt_client
        self.view = view_class # save the view class
        
    def on_connect(self, mqttc, obj, flags, rc):
        print("rc: "+str(rc))

    def on_message(self, mqttc, obj, msg):
        '''
        route messages to the appropriate view method
        '''
        for t in self.config['subscribe_topics']:
            print(msg.topic, '=', t['topic'])
            if msg.topic == t['topic']: # topic must match exactly (no subtopics)
                topic_onmsg = getattr(self.view, t['on_message'])
                return topic_onmsg(msg)

    def on_subscribe(self, mqttc, obj, mid, granted_qos):
        print("Subscribed: "+str(mid)+" "+str(granted_qos))

    def on_log(self, mqttc, obj, level, string):
        print(string)
        
    def connect_and_subscribe(self):
        '''
        subscribe to each topic in the config file
        '''
        self.connect(self.config['mqtt_server']['host'], 1883, 60)
        for t in self.config['subscribe_topics']:
            print('Subscribing:', t['topic'])
            self.subscribe(t['topic'], 0)  
            
        self.loop_start()
