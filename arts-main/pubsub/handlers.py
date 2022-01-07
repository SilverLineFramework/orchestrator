"""MQTT message handlers."""

import uuid

from arts_core.models import Runtime, Module, FileType
from arts_core.serializers import ModuleSerializer, RuntimeSerializer
from . import messages


class UUIDNotFound(Exception):
    """Exception for runtime/module UUID not found."""

    def __init__(self, topic, obj, obj_type="runtime"):
        self.message = messages.Error(
            topic, {"desc": "invalid {} UUID".format(obj_type), "data": obj})


class ARTSHandler():
    """ARTS Message Handler."""

    def __init__(self, scheduler):
        self.scheduler = scheduler

    def _get_object(self, topic, runtime, model=Runtime):
        """Fetch runtime/module by UUID or generate error."""
        try:
            db_entry = model.objects.get(pk=uuid.UUID(runtime))
            return db_entry
        except model.DoesNotExist:
            raise UUIDNotFound(topic, runtime, obj_type=model.type)

    def _create_runtime(self, msg):
        """Register new runtime."""
        obj_data = {}
        for key in Runtime.INPUT_KEYS:
            if key in msg.payload['data']:
                obj_data[key] = msg.payload['data'][key]
        db_entry = Runtime.objects.create(**obj_data)

        return messages.Response(
            msg.topic, msg.payload['object_id'],
            RuntimeSerializer(db_entry, many=False).data)

    def _delete_runtime(self, msg):
        """Delete existing runtime."""
        try:
            runtime = self._get_object(
                msg.topic, msg.payload['data']['uuid'], model=Runtime)
        except UUIDNotFound as e:
            return e.message

        body = RuntimeSerializer(runtime, many=False).data
        runtime.delete()
        return messages.Response(msg.topic, msg.payload['object_id'], body)

    def reg(self, msg):
        """Handle registration message."""
        if msg.payload['type'] != 'arts_req':
            return None

        if msg.payload['action'] == 'create':
            return self._create_runtime(msg)
        elif msg.payload['action'] == 'delete':
            return self._delete_runtime(msg)
        else:
            return messages.Error(msg.topic, {
                "desc": "invalid action", "data": msg.payload['action']})

    def _create_module_ack(self, msg):
        """Handle ACK sent after scheduling module.

        TODO: Should update a flag if ok and reschedule otherwise; currently
        not implemented in the runtime.
        """
        return None

    def _create_module(self, msg):
        """Handle create message."""
        obj_data = {}
        for key in Module.INPUT_KEYS:
            if key in msg.payload['data']:
                obj_data[key] = msg.payload['data']['key']

        if 'apis' not in obj_data:
            if obj_data.get("filetype") == 'PY':
                obj_data['apis'] = "PY"
            else:
                obj_data['apis'] = "WA"

        db_entry = Module(**obj_data)
        db_entry.parent = self.scheduler.schedule_new_module(db_entry)
        db_entry.save()

        return messages.Request(
            "{}/{}".format(msg.topic, db_entry.parent.uuid), "create",
            ModuleSerializer(db_entry, many=False).data)

    def _delete_module(self, msg):
        """Handle delete message."""
        if 'send_to_runtime' in msg.payload['data']:
            try:
                send_rt = self._get_object(
                    msg.topic, msg.payload['data']['send_to_runtime'],
                    model=Runtime)
            except UUIDNotFound as e:
                return e.message
        else:
            send_rt = None

        try:
            module = self._get_object(
                msg.topic, msg.payload['data']['uuid'], model=Module)
        except UUIDNotFound as e:
            return e.message

        res = messages.Request(
            "{}/{}".format(msg.topic, module.parent.uuid), "delete", {
                "type": "module", "uuid": msg.payload['data']['uuid'],
                "send_to_runtime": send_rt
            })
        if send_rt:
            module.parent = send_rt
            module.save()
        else:
            module.delete()

        return res

    def control(self, msg):
        """Handle per-module control message."""
        if msg.payload['type'] == 'runtime_resp':
            return self._create_module_ack(msg)
        elif msg.payload['type'] == 'arts_req':
            if msg.payload['action'] == 'create':
                return self._create_module(msg)
            elif msg.payload['action'] == 'delete':
                return self._delete_module(msg)
            else:
                return messages.Error(msg.topic, {
                    "desc": "invalid action", "data": msg.payload['action']})
        else:
            return messages.Error(msg.topic, {
                "desc": "invalid type", "data": msg.payload['type']})

    def keepalive(self, msg):
        """Handle keepalive message."""
        pass

    def debug(self, msg):
        """Handle debug message."""
        pass

    def profile(self, msg):
        """Handle profiling message."""
        pass
