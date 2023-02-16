"""Message definitions."""

import uuid
import json

from django.conf import settings

from beartype.typing import Union


# Valid JSON entry
JsonData = Union[list, dict, str, tuple, int, float]


class Result:
    """Result ok/error enum."""

    ok = 'ok'
    err = 'error'


class Action:
    """Action create/delete enum."""

    create = 'create'
    delete = 'delete'


class Message:
    """Pubsub Message container."""

    def __init__(self, topic: str, payload: JsonData) -> None:
        self.topic = topic
        self.payload = payload

    def get(self, *args: list) -> any:
        """Get attribute, or raise appropriate error.

        Raises
        ------
        MissingField
            Equivalent of ```KeyError```, with appropriate error generation.
        """
        try:
            d = self.payload
            for p in args:
                d = d[p]
            return d
        except (KeyError, TypeError):
            raise MissingField(args)


def Error(data: JsonData) -> Message:
    """Error message."""
    return Message(settings.MQTT_LOG, {
        "object_id": str(uuid.uuid4()),
        "action": "error",
        "type": "resp",
        "data": data
    })


def __convert_str_attrs(d: dict) -> None:
    """Convert JSON-encoded string attributes into proper objects."""
    convert_keys = [
        'apis', 'args', 'env', 'channels', 'peripherals', 'metadata']
    # convert array attributes saved as strings into objects
    for key in convert_keys:
        try:
            attr_str = d[key].replace("'", '"')
            d[key] = json.loads(attr_str)
        except Exception as _:
            pass


def Response(
    topic: str, src_uuid: str, details: JsonData, result: str = Result.ok,
    convert: bool = True
) -> Message:
    """Orchestrator Response."""
    if convert:
        __convert_str_attrs(details)
    return Message(topic, {
        "object_id": str(src_uuid), "type": "resp",
        "data": {"result": result, "details": details}
    })


def Request(
    topic: str, action: str, data: JsonData, convert: bool = True
) -> Message:
    """Orchestrator Request."""
    if convert:
        __convert_str_attrs(data)
    return Message(topic, {
        "object_id": str(uuid.uuid4()), "action": action, "type": "req",
        "data": data
    })


class SLException(Exception):
    """Base class for orchestrator exceptions."""

    def __init__(self, payload: JsonData) -> None:
        self.message = Error(payload)


class UUIDNotFound(SLException):
    """Runtime/module UUID not found."""

    def __init__(self, obj: JsonData, obj_type: str = "runtime") -> None:
        super().__init__(
            {"desc": "invalid {} Name/UUID".format(obj_type), "data": obj})


class DuplicateUUID(SLException):
    """Attempted to create a duplicate UUID.

    This is expected in per-scene instantiated modules.
    """

    def __init__(self, obj: JsonData, obj_type="runtime") -> None:
        super().__init__({
            "desc": "duplicate {} UUID; request ignored".format(obj_type),
            "data": obj
        })


class InvalidArgument(SLException):
    """Exception for invalid argument value."""

    def __init__(self, arg_name: str, arg_value: JsonData) -> None:
        super().__init__(
            {"desc": "invalid {}".format(arg_name), "data": arg_value})


class MissingField(SLException):
    """Required field is missing."""

    def __init__(self, path: str) -> None:
        super().__init__({"desc": "missing field", "data": "/".join(path)})


class FileNotFound(SLException):
    """WASM file is missing."""

    def __init__(self, path: str) -> None:
        super().__init__({"desc": "file not found", "data": path})
