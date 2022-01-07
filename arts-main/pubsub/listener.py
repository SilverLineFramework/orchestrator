"""MQTT Listener."""

import traceback
import json
import pprint

import paho.mqtt.client as mqtt
from json.decoder import JSONDecodeError

from . import messages


class MQTTListener(mqtt.Client):
    """MQTT Listener class extending mqtt.Client.

    Parameters
    ----------
    view : ARTSHandler
        Routes topic messages to methods named according to the config topic
        dict keys.
    cid : str
        Client ID for paho MQTT client.
    pubsub_config : dict
        Configuration for pubsub topics.
    jwt_config : dict
        JSON Web Token configuration
    """

    def __init__(self, view, cid='ARTS', pubsub_config=None, jwt_config=None):
        super().__init__(cid)

        print("Starting MQTT client.")
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(pubsub_config)

        self.config = pubsub_config
        self.view = view
        self.jwt_config = jwt_config

        self.__connect_and_subscribe()

    def __connect_and_subscribe(self):
        """Subscribe to control topics."""
        if self.config['mqtt_credentials'] is not None:
            self.username_pw_set(**self.config['mqtt_credentials'])
        self.connect(
            self.config['mqtt_server']['host'],
            self.config['mqtt_server']['port'], 60)
        for t in self.config['subscribe_topics']:
            print('Subscribing:', t)
            self.subscribe(t, 0)

        self.loop_start()

    def on_connect(self, mqttc, obj, flags, rc):
        """Topic connect callback."""
        print("rc: {}".format(rc))

    def __json_decode(self, msg):
        """Decode JSON MQTT message."""
        payload = str(msg.payload.decode("utf-8", "ignore"))
        if (payload[0] == "'"):
            payload = payload[1:len(payload) - 1]
        return messages.Message(msg.topic, json.loads(payload))

    def __on_message(self, msg):
        """Message handler internals."""
        try:
            decoded = self.__json_decode(msg)
        except JSONDecodeError:
            return messages.Error(
                msg.topic, {"desc": "Invalid JSON", "data": msg.payload})

        handler = self.config['subscribe_topics'].get(decoded.topic)
        if handler:
            try:
                return getattr(self.view, handler)(decoded)
            except Exception as e:
                print(traceback.format_exc())
                return messages.Error(
                    msg.topic, {"desc": "Uncaught exception", "data": str(e)})
        else:
            return messages.Error(
                msg.topic, {"desc": "Invalid topic", "data": msg.topic})

    def on_message(self, mqttc, obj, msg):
        """MQTT Message handler."""
        res = self.__on_message(msg)
        # only publish if not `None`
        if res:
            print("Publishing response [topic={}]:\n{}".format(
                str(res.topic), json.dumps(res.payload)))
            self.publish(res.topic, json.dumps(res.payload))

    def on_subscribe(self, mqttc, obj, mid, granted_qos):
        """Subscribe callback."""
        print("Subscribed: {} {}".format(mid, granted_qos))

    def on_log(self, mqttc, obj, level, string):
        """Logging callback."""
        # print(string)
