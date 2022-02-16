"""MQTT Listener."""

import traceback
import json

import paho.mqtt.client as mqtt
from json.decoder import JSONDecodeError

from django.conf import settings

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
    jwt_config : dict
        JSON Web Token configuration
    """

    def __init__(self, view, cid='ARTS', jwt_config=None):
        super().__init__(cid)

        print("[Setup] Starting MQTT client...")

        self.view = view
        self.jwt_config = jwt_config

        self.__connect_and_subscribe()

    def __connect_and_subscribe(self):
        """Subscribe to control topics."""
        self.username_pw_set(
            username=settings.MQTT_USERNAME, password=settings.MQTT_PASSWORD)
        self.connect(settings.MQTT_HOST, settings.MQTT_PORT, 60)

        self.__subscribe_mid = {
            self.subscribe(t, 0)[1]: t for t in settings.MQTT_TOPICS
        }
        self._handler_dispatcher = {
            k: getattr(self.view, v) for k, v in settings.MQTT_TOPICS.items()
        }

        self.loop_start()

    def on_connect(self, mqttc, obj, flags, rc):
        """Client connect callback."""
        print("[Setup] Connected: rc={}".format(rc))

    def __json_decode(self, msg):
        """Decode JSON MQTT message."""
        payload = str(msg.payload.decode("utf-8", "ignore"))
        if (payload[0] == "'"):
            payload = payload[1:len(payload) - 1]
        return messages.Message(msg.topic, json.loads(payload))

    def __on_message(self, msg):
        """Message handler internals.

        Handlers take a (topic, data) ```Message``` as input, and return either
        a ```Message``` to send in response, ```None``` for no response, or
        raise an ```ARTSException``` which should be given as a response.
        """
        try:
            decoded = self.__json_decode(msg)
        except JSONDecodeError:
            import pdb
            pdb.set_trace()
            return messages.Error(
                {"desc": "Invalid JSON", "data": msg.payload})

        handler = self._handler_dispatcher.get(decoded.topic)
        if callable(handler):
            try:
                return handler(decoded)
            # ARTS Exceptions are raised by handlers in response to
            # invalid request data (which has been detected).
            except messages.ARTSException as e:
                return e.message
            # Uncaught exceptions should only be due to programmer error.
            except Exception as e:
                print(traceback.format_exc())
                print("Input message: {}".format(str(decoded.payload)))
                return messages.Error(
                    {"desc": "Uncaught exception", "data": str(e)})
        else:
            return messages.Error({"desc": "Invalid topic", "data": msg.topic})

    def on_message(self, mqttc, obj, msg):
        """MQTT Message handler."""
        res = self.__on_message(msg)
        # only publish if not `None`
        if res:
            payload = json.dumps(res.payload)
            print("Response [topic={}]:\n{}".format(str(res.topic), payload))
            self.publish(res.topic, payload)

    def on_subscribe(self, mqttc, obj, mid, granted_qos):
        """Subscribe callback."""
        print("[Setup] Subscribed: {}".format(self.__subscribe_mid[mid]))

    def on_log(self, mqttc, obj, level, string):
        """Logging callback."""
        pass
