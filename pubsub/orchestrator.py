"""MQTT Listener."""

import json
import logging
import uuid
from django.conf import settings

from beartype.typing import Optional
from beartype import beartype

from libsilverline import MQTTClient, MQTTServer
from .handler_base import ControlHandler
from .handler_registration import Registration
from .handler_control import Control
from .handler_keepalive import Keepalive


@beartype
class Orchestrator(MQTTClient):
    """MQTT Listener class extending libsilverline's Client."""

    _HEADER = r"""
       _           _
      /_\  ___ ___| |_  _ ___
     / _ \/ -_) _ \ | || (_-<
    /_/ \_\___\___/_|\_,_/__/
    Silverline: Orchestrator
    """

    def __init__(
        self, name: str = "orchestrator", server: Optional[MQTTServer] = None
    ) -> None:
        super().__init__(
            client_id="{}:{}".format(name, uuid.uuid4()),
            server=server, bridge=True)

        self.__log = logging.getLogger(name="resp")
        self.name = name

    def start(self, ) -> None:
        """Start orchestrator pubsub interface."""
        print(self._HEADER)
        super().start()
        for handler in [Registration, Control, Keepalive]:
            self.__add_handler(handler())

    def __add_handler(self, handler: ControlHandler) -> None:
        """Message handler registration."""
        topic = "{}/{}".format(settings.REALM, handler.TOPIC)

        def inner(client, userdata, msg):
            results = handler.handle_message(msg)
            for res in results:
                payload = json.dumps(res.payload)
                log_msg = "{}:{}".format(str(res.topic), payload)
                if res.topic == settings.MQTT_LOG:
                    self.__log.warning(log_msg)
                else:
                    self.__log.info(log_msg)
                self.publish(res.topic, payload, qos=2)

        self.subscribe(topic)
        self.message_callback_add(topic, inner)
