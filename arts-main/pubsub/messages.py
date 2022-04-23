"""Message definitions."""

import uuid
import json

from django.conf import settings


class Result():
    """Result ok/error enum."""

    ok = 'ok'
    err = 'error'


class Action():
    """Action create/delete enum."""

    create = 'create'
    delete = 'delete'


class Message:
    """Pubsub Message container."""

    def __init__(self, topic, payload):
        self.topic = topic
        self.payload = payload

    def get(self, *args):
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

    def set(self, value, *args):
        """ Set attribute, or raise appropriate error
        """
        try:
            d = self.payload
            for p in args[:-1]:
                d = d[p]
            d[args[-1]] = value
        except (KeyError, TypeError):
            raise MissingField(args)


def Error(data):
    """Error message."""
    return Message(settings.MQTT_ERR, {
        "object_id": str(uuid.uuid4()),
        "action": "error",
        "type": "arts_resp",
        "data": data
    })


def __convert_str_attrs(d):
    """Convert JSON-encoded string attributes into proper objects."""
    convert_keys = ['apis', 'args', 'env', 'channels', 'peripherals', "aot_target"]
    # convert array attributes saved as strings into objects
    for key in convert_keys:
        try:
            attr_str = d[key].replace("'", '"')
            d[key] = json.loads(attr_str)
        except Exception as _:
            pass


def Response(topic, src_uuid, details, result=Result.ok, convert=True):
    """ARTS Response."""
    if convert:
        __convert_str_attrs(details)
    return Message(topic, {
        "object_id": str(src_uuid), "type": "arts_resp",
        "data": {"result": result, "details": details}
    })


def Request(topic, action, data, convert=True):
    """ARTS Request."""
    if convert:
        __convert_str_attrs(data)
    return Message(topic, {
        "object_id": str(uuid.uuid4()), "action": action, "type": "arts_req",
        "data": data
    })


class ARTSException(Exception):
    """Base class for ARTS exceptions."""

    def __init__(self, payload):
        self.message = Error(payload)


class UUIDNotFound(ARTSException):
    """Exception for runtime/module UUID not found."""

    def __init__(self, obj, obj_type="runtime"):
        super().__init__(
            {"desc": "invalid {} UUID".format(obj_type), "data": obj})


class InvalidArgument(ARTSException):
    """Exception for invalid argument value."""

    def __init__(self, arg_name, arg_value):
        super().__init__(
            {"desc": "invalid {}".format(arg_name), "data": arg_value})


class MissingField(ARTSException):
    """Required field is missing."""

    def __init__(self, path):
        super().__init__(
            {"desc": "missing field", "data": "/".join(path)})


class FileNotFound(ARTSException):
    """WASM file is missing."""

    def __init__(self, path):
        super().__init__(
            {"desc": "file not found", "data": path})
