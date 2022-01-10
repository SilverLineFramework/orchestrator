"""MQTT message handlers."""

import uuid

from arts_core.models import Runtime, Module, File, FileType
from arts_core.serializers import ModuleSerializer, RuntimeSerializer
from . import messages


class ARTSHandler():
    """ARTS Message Handler."""

    def __init__(self, scheduler, profiler):
        self.scheduler = scheduler
        self.profiler = profiler

    def _get_object(self, topic, rt, model=Runtime):
        """Fetch runtime/module by UUID or generate error."""
        try:
            return model.objects.get(pk=uuid.UUID(rt))
        except model.DoesNotExist:
            raise messages.UUIDNotFound(rt, obj_type=str(model().type))

    def __object_from_dict(self, model, attrs):
        """Convert attrs to model."""
        filtered = {k: v for k, v in attrs.items() if k in model.INPUT_ATTRS}
        if 'uuid' in attrs:
            filtered['uuid'] = uuid.UUID(attrs['uuid'])
        return model(**filtered)

    def reg(self, msg):
        """Handle registration message."""
        if msg.get('type') == 'arts_resp':
            return None

        print("\nReceived registration message [topic={}]:\n{}".format(
            str(msg.topic), msg.payload))

        action = msg.get('action')
        if action == 'create':
            db_entry = self.__object_from_dict(Runtime, msg.get('data'))
            db_entry.save()
            return messages.Response(
                msg.topic, msg.get('object_id'),
                RuntimeSerializer(db_entry, many=False).data)
        elif action == 'delete':
            runtime = self._get_object(
                msg.topic, msg.get('data', 'uuid'), model=Runtime)
            body = RuntimeSerializer(runtime, many=False).data
            runtime.delete()
            return messages.Response(msg.topic, msg.get('object_id'), body)
        else:
            raise messages.InvalidArgument("action", msg.get('action'))

    def __create_module_ack(self, msg):
        """Handle ACK sent after scheduling module.

        TODO: Should update a flag if ok and reschedule otherwise; currently
        not implemented in the runtime.
        """
        return None

    def __create_or_get_file(self, msg):
        """Link existing file entry or create new file entry."""
        if msg.payload['data']['filetype'] == FileType.PY:
            file = msg.get('data', 'args', 1)
        else:
            file = msg.get('data', 'filename')

        try:
            return File.objects.get(name=file)
        except File.DoesNotExist:
            return File.objects.create(
                name=file, type=msg.get('data', 'filetype'))

    def __get_runtime_or_schedule(self, msg, module):
        """Get parent runtime, or allocate target runtime."""
        if 'parent' in msg.get('data'):
            rt = msg.get('data', 'parent', 'uuid')
            return self._get_object(msg.topic, rt, model=Runtime)
        else:
            return self.scheduler.schedule_new_module(module)

    def __create_module(self, msg):
        """Handle create message."""
        data = msg.get('data')
        if 'apis' not in data:
            if data.get("filetype") == FileType.PY:
                data['apis'] = ["python:python3"]
            else:
                data['apis'] = ["wasi:snapshot_preview1"]
        if 'filetype' not in data:
            if "python" in str(data.get("filename")):
                data['filetype'] = FileType.PY
            else:
                data['filetype'] = FileType.WA

        module = self.__object_from_dict(Module, data)
        module.source = self.__create_or_get_file(msg)
        module.parent = self.__get_runtime_or_schedule(msg, module)
        module.save()

        return messages.Request(
            "{}/{}".format(msg.topic, module.parent.uuid), "create",
            ModuleSerializer(module, many=False).data)

    def __delete_module(self, msg):
        """Handle delete message."""
        module_id = msg.get('data', 'uuid')
        module = self._get_object(msg.topic, module_id, model=Module)
        uuid_current = str(module.parent.uuid)

        data = msg.get('data')
        if 'send_to_runtime' in data:
            send_rt = data['send_to_runtime']
            module.parent = self._get_object(msg.topic, send_rt, model=Runtime)
            module.save()
        else:
            send_rt = None
            module.delete()

        return messages.Request(
            "{}/{}".format(msg.topic, uuid_current), "delete", {
                "type": "module", "uuid": module_id,
                "send_to_runtime": send_rt})

    def control(self, msg):
        """Handle per-module control message."""
        # arts_resp -> is a message we sent, should be ignored
        msg_type = msg.get('type')
        if msg_type == 'arts_resp':
            return None

        print("\nReceived control message [topic={}]:\n{}".format(
            str(msg.topic), msg.payload))

        if msg_type == 'runtime_resp':
            return self.__create_module_ack(msg)
        elif msg_type == 'arts_req':
            action = msg.get('action')
            if action == 'create':
                return self.__create_module(msg)
            elif action == 'delete':
                return self.__delete_module(msg)
            else:
                raise messages.InvalidArgument('action', action)
        else:
            raise messages.InvalidArgument('type', msg_type)

    def keepalive(self, msg):
        """Handle keepalive message."""
        return None

    def debug(self, msg):
        """Handle debug message."""
        print(str(msg.payload))
        return None

    def profile(self, msg):
        """Handle profiling message."""
        self.profiler.update(
            module_id=msg.get("module_id"), runtime_id=msg.get("runtime_id"),
            data=msg.get("data"))
        self.profiler.save()
        return None
