"""MQTT Listener."""

import traceback
import json
import logging

from libsilverline import Client

from django.conf import settings

from . import messages


class MQTTListener(Client):
    """MQTT Listener class extending libsilverline's Client.

    Parameters
    ----------
    name : str
        Client ID for paho MQTT client. MUST be unique -- will cause all sorts
        of strange errors with no apparent pattern if not unique.
    """

    def __init__(self, *args, **kwargs):
        self._req = logging.getLogger(name="request")
        self._resp = logging.getLogger(name="response")
        super().__init__(*args, **kwargs)

    def handle_message(self, handler):
        """Message handler decorator.

        Handlers take a (topic, data) ``Message`` as input, and return either
        a ``Message`` to send in response, ``None`` for no response, or
        raise an ``SLException`` which should be given as a response.

        If multiple responses are to be given, they can be returned as a list.
        The responses are then published in the order that they are returned.
        """
        def inner(client, userdata, msg):
            results = self._handle_message(handler, msg)
            if results:
                if not isinstance(results, list):
                    results = [results]
                for res in results:
                    payload = json.dumps(res.payload)
                    log_msg = "{}:{}".format(str(res.topic), payload)
                    if res.topic == settings.MQTT_LOG:
                        self._resp.warning(log_msg)
                    else:
                        self._resp.info(log_msg)
                    self.publish(res.topic, payload, qos=2)
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
