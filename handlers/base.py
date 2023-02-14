"""MQTT message handler."""

import json

from beartype.typing import Optional, Union
from beartype import beartype

from pubsub.messages import Message, SLException, UUIDNotFound
from orchestrator.models import Runtime


@beartype
class ControlHandler:
    """Base class for message handlers, including some common utilities."""

    topic = None

    @staticmethod
    def decode(msg):
        """Decode MQTT message as JSON."""
        try:
            payload = str(msg.payload.decode("utf-8", "ignore"))
            if (payload[0] == "'"):
                payload = payload[1:len(payload) - 1]
            return Message(msg.topic, json.loads(payload))
        except json.JSONDecodeError:
            raise SLException({"desc": "Invalid JSON", "data": msg.payload})

    def handle(self, msg: Message) -> Optional[Union[Message, list[Message]]]:
        """Handle message.

        Returns
        -------
        If messages.Message or a list of messages, sends as a response.
        Otherwise, does nothing.

        Raises
        ------
        messages.SLException
            When a handler raises SLException in the decode or handle
            methods, the error payload is sent to the error channel
            (realm/proc/err) and shown in the orchestrator log.
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
