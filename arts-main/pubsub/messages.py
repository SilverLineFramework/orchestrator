"""Message definitions."""

import collections
import uuid
import json


class Result():
    """Result ok/error enum."""

    ok = 'ok'
    err = 'error'


class Action():
    """Action create/delete enum."""

    create = 'create'
    delete = 'delete'


Message = collections.namedtuple("ARTSMessage", ["topic", "payload"])


def Error(topic, data):
    """Error message."""
    return Message(topic, {
        "object_id": str(uuid.uuid4()),
        "action": "error",
        "type": "arts_resp",
        "data": data
    })


def __convert_str_attrs(d):
    """Convert JSON-encoded string attributes into proper objects."""
    convert_keys = ['apis', 'args', 'env', 'channels', 'peripherals']
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
