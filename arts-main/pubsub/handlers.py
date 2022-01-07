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

    def __init__(self, scheduler, profiler):
        self.scheduler = scheduler
        self.profiler = profiler

    def _get_object(self, topic, runtime, model=Runtime):
        """Fetch runtime/module by UUID or generate error."""
        try:
            db_entry = model.objects.get(pk=uuid.UUID(runtime))
            return db_entry
        except model.DoesNotExist:
            raise UUIDNotFound(topic, runtime, obj_type=str(model().type))

    def __object_from_dict(self, model, attrs):
        """Convert attrs to model."""
        filtered = {k: v for k, v in attrs.items() if k in model.INPUT_ATTRS}
        if 'uuid' in attrs:
            filtered['uuid'] = uuid.UUID(attrs['uuid'])
        return model(**filtered)

    def reg(self, msg):
        """Handle registration message."""
        if msg.payload['type'] == 'arts_resp':
            return None

        print("\nReceived registration message [topic={}]:\n{}".format(
            str(msg.topic), msg.payload))

        if msg.payload['action'] == 'create':
            db_entry = self.__object_from_dict(Runtime, msg.payload['data'])
            db_entry.save()
            return messages.Response(
                msg.topic, msg.payload['object_id'],
                RuntimeSerializer(db_entry, many=False).data)
        elif msg.payload['action'] == 'delete':
            try:
                runtime = self._get_object(
                    msg.topic, msg.payload['data']['uuid'], model=Runtime)
            except UUIDNotFound as e:
                return e.message
            body = RuntimeSerializer(runtime, many=False).data
            runtime.delete()
            return messages.Response(msg.topic, msg.payload['object_id'], body)
        else:
            return messages.Error(msg.topic, {
                "desc": "invalid action", "data": msg.payload['action']})

    def __create_module_ack(self, msg):
        """Handle ACK sent after scheduling module.

        TODO: Should update a flag if ok and reschedule otherwise; currently
        not implemented in the runtime.
        """
        return None

    def __create_module(self, msg):
        """Handle create message."""
        if 'apis' not in msg.payload['data']:
            if msg.payload['data'].get("filetype") == 'PY':
                msg.payload['data']['apis'] = "PY"
            else:
                msg.payload['data']['apis'] = "WA"

        module = self.__object_from_dict(Module, msg.payload['data'])
        if 'parent' in msg.payload['data']:
            try:
                module.parent = self._get_object(
                    msg.topic, msg.payload['data']['parent']['uuid'],
                    model=Runtime)
            except UUIDNotFound as e:
                return e.message
        else:
            module.parent = self.scheduler.schedule_new_module(module)
        module.save()

        return messages.Request(
            "{}/{}".format(msg.topic, module.parent.uuid), "create",
            ModuleSerializer(module, many=False).data)

    def __delete_module(self, msg):
        """Handle delete message."""
        data = msg.payload['data']
        try:
            module = self._get_object(msg.topic, data['uuid'], model=Module)
            uuid_current = str(module.parent.uuid)
        except UUIDNotFound as e:
            return e.message

        if 'send_to_runtime' in data:
            try:
                module.parent = self._get_object(
                    msg.topic, data['send_to_runtime'], model=Runtime)
                module.save()
            except UUIDNotFound as e:
                return e.message
        else:
            send_rt = None
            module.delete()

        return messages.Request(
            "{}/{}".format(msg.topic, uuid_current), "delete", {
                "type": "module", "uuid": data['uuid'],
                "send_to_runtime": send_rt})

    def control(self, msg):
        """Handle per-module control message."""
        if msg.payload['type'] == 'arts_resp':
            return None

        print("\nReceived control message [topic={}]:\n{}".format(
            str(msg.topic), msg.payload))

        if msg.payload['type'] == 'runtime_resp':
            return self.__create_module_ack(msg)
        elif msg.payload['type'] == 'arts_req':
            if msg.payload['action'] == 'create':
                return self.__create_module(msg)
            elif msg.payload['action'] == 'delete':
                return self.__delete_module(msg)
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
        self.profiler.add(msg.payload)
        self.profiler.save()
        return None
