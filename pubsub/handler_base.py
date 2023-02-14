"""MQTT message handler."""

import json
import logging
import traceback
from paho.mqtt import client

from beartype.typing import Optional, Union
from beartype import beartype

from .messages import Message, SLException, UUIDNotFound, Error
from orchestrator.models import Runtime


@beartype
class ControlHandler:
    """Base class for message handlers, including some common utilities."""

    NAME = "abstract"
    TOPIC = None

    def __init__(self):
        self.log = logging.getLogger(self.NAME)

    @staticmethod
    def decode(msg: client.MQTTMessage) -> Message:
        """Decode MQTT message as JSON."""
        try:
            payload = str(msg.payload.decode("utf-8", "ignore"))
            if (payload[0] == "'"):
                payload = payload[1:len(payload) - 1]
            return Message(msg.topic, json.loads(payload))
        except json.JSONDecodeError:
            raise SLException({"desc": "Invalid JSON", "data": msg.payload})

    def handle_message(self, msg: client.MQTTMessage) -> list[Message]:
        """Message handler wrapper with error handling."""
        decoded = None
        try:
            decoded = self.decode(msg)
            res = self.handle(decoded)
            if res is None:
                return []
            elif isinstance(res, list):
                return res
            else:
                return [res]

        # SLExceptions are raised by handlers in response to
        # invalid request data (which has been detected).
        except SLException as e:
            return [e.message]
        # Uncaught exceptions here must be caused by some programmer error
        # or unchecked edge case, so are always returned.
        except Exception as e:
            self.log.error(traceback.format_exc())
            cause = decoded.payload if decoded else msg.payload
            self.log.error("Caused by: {}".format(str(cause)))
            return [Error({"desc": "Uncaught exception", "data": str(e)})]

    def handle(self, msg: Message) -> Optional[Union[Message, list[Message]]]:
        """Handle message.

        Parameters
        ----------
        msg: MQTT input message.

        Returns
        -------
        If messages.Message or a list of messages, sends as a response.
        Otherwise (if None), does nothing.

        Raises
        ------
        messages.SLException
            When a handler raises SLException in the decode or handle
            methods, the error payload is sent to the log channel
            (realm/proc/log) and shown in the orchestrator log.
        """
        raise NotImplementedError()

    @staticmethod
    def _get_object(rt: str, model=Runtime):
        """Fetch runtime/module by name or UUID or generate error."""
        try:
            return model.objects.get(name=rt)
        except model.DoesNotExist:
            try:
                return model.objects.get(uuid=rt)
            except model.DoesNotExist:
                raise UUIDNotFound(rt, obj_type=str(model.TYPE))

    @staticmethod
    def _object_from_dict(model, attrs: dict):
        """Convert attrs to model."""
        filtered = {k: v for k, v in attrs.items() if k in model.INPUT_ATTRS}
        return model(**filtered)
