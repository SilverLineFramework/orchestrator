"""MQTT Listener."""

import traceback
import json
import logging

import paho.mqtt.client as mqtt
import ssl
import uuid

from django.conf import settings

from . import messages
from handlers import HANDLERS


class MQTTListener(mqtt.Client):
    """MQTT Listener class extending mqtt.Client.

    Parameters
    ----------
    name : str
        Client ID for paho MQTT client.
    """

    def __init__(self, name='orchestrator'):
        super().__init__("{}:{}".format(name, str(uuid.uuid4())))

        self._setup = logging.getLogger(name="setup")
        self._req = logging.getLogger(name="request")
        self._resp = logging.getLogger(name="response")

        self._setup.info("Starting MQTT client...")
        self.username_pw_set(
            username=settings.MQTT_USERNAME, password=settings.MQTT_PASSWORD)
        if settings.MQTT_SSL:
            self.tls_set(cert_reqs=ssl.CERT_NONE)
        self.connect(settings.MQTT_HOST, settings.MQTT_PORT, 60)
        self.loop_start()

    def handle_message(self, handler):
        """Message handler decorator.

        Handlers take a (topic, data) ```Message``` as input, and return either
        a ```Message``` to send in response, ```None``` for no response, or
        raise an ```SLException``` which should be given as a response.
        """
        def inner(client, userdata, msg):
            res = self._handle_message(handler, msg)
            if res:
                payload = json.dumps(res.payload)
                log_msg = "{}:{}".format(str(res.topic), payload)
                if res.topic == settings.MQTT_LOG:
                    self._resp.warning(log_msg)
                else:
                    self._resp.info(log_msg)
                self.publish(res.topic, payload)
        return inner

    def _handle_message(self, handler, msg):
        try:
            decoded = handler.decode(msg)
            return handler.handle(decoded)
        # SLExceptions are raised by handlers in response to
        # invalid request data (which has been detected).
        except messages.SLException as e:
            return e.message
        # Uncaught exceptions here must be caused by some programmer error
        # or unchecked edge case, so are always returned.
        except Exception as e:
            logging.error(traceback.format_exc())
            cause = decoded.payload if decoded else msg.payload
            logging.error("Caused by: {}".format(str(cause)))
            return messages.Error(
                {"desc": "Uncaught exception", "data": str(e)})

    def on_message(self, client, userdata, msg):
        """Callback for unrecognized topic."""
        logging.error("Unrecognized topic: {}.".format(msg.topic))

    def subscribe_callback(self, topic, callback):
        """Subscribe and add callback."""
        print(topic)
        self.subscribe(topic)
        self.message_callback_add(topic, callback)

    def on_connect(self, mqttc, obj, flags, rc):
        """Client connect callback."""
        self._setup.info("Connected: rc={}".format(rc))
        for topic, callback in HANDLERS.items():
            self.subscribe_callback(
                settings.MQTT_TOPICS[topic], self.handle_message(callback()))
