"""MQTT client wrapper."""

import logging
import ssl
import json
from threading import Semaphore

import paho.mqtt.client as mqtt

from beartype import beartype
from beartype.typing import NamedTuple, Optional


@beartype
class MQTTServer(NamedTuple):
    """MQTT server and login information.

    Attributes
    ----------
    host: MQTT server web address.
    port: Server port number (usually 1883 or 8883 if using SSL).
    user: Username.
    pwd: Password.
    ssl: Whether server has TLS/SSL enabled.
    """

    host: str
    port: int
    user: str
    pwd: str
    ssl: bool

    @classmethod
    def from_json(cls, path: str):
        """Load settings from JSON configuration file."""
        with open(path) as f:
            data = json.load(f)
        return cls(
            host=data.get("mqtt", "localhost"),
            port=data.get("mqtt_port", 1883),
            user=data.get("mqtt_username", "cli"),
            pwd=data.get("pwd", ""),
            ssl=data.get("use_ssl", False))


@beartype
class MQTTClient(mqtt.Client):
    """MQTT Client wrapper.

    Parameters
    ----------
    client_id: client ID.
    """

    def __init__(self, client_id: str = "client") -> None:
        self.__log = logging.getLogger('mq')
        self.client_id = client_id
        super().__init__(client_id=client_id)

    def connect(self, server: Optional[MQTTServer] = None) -> None:
        """Connect to MQTT server.

        Parameters
        ----------
        server: MQTT broker information. Uses default (localhost:1883, no
            security) if None.
        """
        if server is None:
            server = MQTTServer(
                host="localhost", port=1883, user="cli", pwd="", ssl=False)

        semaphore = Semaphore()
        semaphore.acquire()

        def _on_connect(mqttc, obj, flags, rc):
            semaphore.release()

        self.on_connect = _on_connect

        self.__log.info(
            "Connecting MQTT client: {}".format(self.client_id))
        self.__log.info("SSL: {}".format(server.ssl))
        self.__log.info("Username: {}".format(server.user))
        try:
            self.__log.info("Password file: {}".format(server.pwd))
            with open(server.pwd, 'r') as f:
                passwd = f.read().rstrip('\n')
        except FileNotFoundError:
            passwd = ""
            self.__log.warn("No password supplied; using an empty password.")

        self.username_pw_set(server.user, passwd)
        if server.ssl:
            self.tls_set(cert_reqs=ssl.CERT_NONE)
        super().connect(server.host, server.port, 60)

        # Waiting for on_connect to release
        self.loop_start()
        semaphore.acquire()
        self.__log.info("Connected to MQTT server.")
