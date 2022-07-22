"""MQTT Listener."""

import traceback
import json
import logging

import paho.mqtt.client as mqtt
import ssl

from django.conf import settings

from . import messages


class MQTTListener(mqtt.Client):
    """MQTT Listener class extending mqtt.Client.

    Parameters
    ----------
    handlers : dict (str -> pubsub.BaseHandler)
        Routes topic messages to methods named according to the config topic
        dict keys.
    cid : str
        Client ID for paho MQTT client.
    jwt_config : dict
        JSON Web Token configuration
    """

    def __init__(self, handlers, cid='orchestrator', jwt_config=None):
        super().__init__(cid)

        self._setup = logging.getLogger(name="setup")
        self._req = logging.getLogger(name="request")
        self._resp = logging.getLogger(name="response")

        self.handlers = handlers
        self.jwt_config = jwt_config

        self.__connect_and_subscribe()

    def __connect_and_subscribe(self):
        """Subscribe to control topics."""
        self._setup.info("Starting MQTT client...")

        self.username_pw_set(
            username=settings.MQTT_USERNAME, password=settings.MQTT_PASSWORD)
        if settings.MQTT_SSL:
            self.tls_set(cert_reqs=ssl.CERT_NONE)
        self.connect(settings.MQTT_HOST, settings.MQTT_PORT, 60)

        self.__subscribe_mid = {
            self.subscribe(t, 0)[1]: t for t in settings.MQTT_TOPICS
        }
        self._handler_dispatcher = {
            k: self.handlers[v] for k, v in settings.MQTT_TOPICS.items()
        }

        self.loop_start()

    def on_connect(self, mqttc, obj, flags, rc):
        """Client connect callback."""
        self._setup.info("Connected: rc={}".format(rc))

    def __on_message(self, msg):
        """Message handler internals.

        Handlers take a (topic, data) ```Message``` as input, and return either
        a ```Message``` to send in response, ```None``` for no response, or
        raise an ```SLException``` which should be given as a response.
        """
        try:
            handler = self._handler_dispatcher.get(msg.topic)
        except KeyError:
            return messages.Error({"desc": "Invalid topic", "data": msg.topic})

        try:
            decoded = handler.decode(msg)
            return handler.handle(decoded)
        # ARTS Exceptions are raised by handlers in response to
        # invalid request data (which has been detected).
        except messages.SLException as e:
            return e.message
        # Uncaught exceptions here must be caused by some programmer error
        # or unchecked edge case, so are always returned.
        except Exception as e:
            logging.error(traceback.format_exc())
            logging.error("Caused by: {}".format(str(decoded.payload)))
            return messages.Error(
                {"desc": "Uncaught exception", "data": str(e)})

    def on_message(self, mqttc, obj, msg):
        """MQTT Message handler."""
        res = self.__on_message(msg)
        # only publish if not `None`
        if res:
            payload = json.dumps(res.payload)
            if res.topic == settings.MQTT_LOG:
                self._resp.warning(
                    "{}:{}".format(str(res.topic), payload))
            else:
                self._resp.info(
                    "{}:{}".format(str(res.topic), payload))
            self.publish(res.topic, payload)

    def on_subscribe(self, mqttc, obj, mid, granted_qos):
        """Subscribe callback."""
        self._setup.debug(
            "Subscribed: {}".format(self.__subscribe_mid[mid]))
