"""MQTT message handler."""

import json
import uuid

from pubsub import messages
from api.models import Runtime


class BaseHandler:
    """Base class for message handlers, including some common utilities."""

    @staticmethod
    def decode(msg):
        """Decode MQTT message as JSON."""
        try:
            payload = str(msg.payload.decode("utf-8", "ignore"))
            if (payload[0] == "'"):
                payload = payload[1:len(payload) - 1]
            return messages.Message(msg.topic, json.loads(payload))
        except json.JSONDecodeError:
            raise messages.ARTSException(
                {"desc": "Invalid JSON", "data": msg.payload})

    def handle(self, msg):
        """Handle message.

        Returns
        -------
        messages.Message or None
            If messages.Message, sends this as a response. Otherwise, does
            nothing.

        Raises
        ------
        messages.ARTSException
            When a handler raises ARTSException in the decode or handle
            methods, the error payload is sent to the error channel
            (realm/proc/err) and shown in the ARTS log.
        """
        raise NotImplementedError()

    @staticmethod
    def _get_object(rt, model=Runtime):
        """Fetch runtime/module by UUID or generate error."""
        try:
            return model.objects.get(uuid=rt)
        except model.DoesNotExist:
            raise messages.UUIDNotFound(rt, obj_type=str(model().type))

    @staticmethod
    def _object_from_dict(model, attrs):
        """Convert attrs to model."""
        filtered = {k: v for k, v in attrs.items() if k in model.INPUT_ATTRS}
        return model(**filtered)
