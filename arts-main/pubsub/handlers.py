"""MQTT message handlers."""

import uuid

from arts_core.models import Runtime, Module, File, FileType
from arts_core.serializers import ModuleSerializer, RuntimeSerializer
from . import messages
from wasm_files import file_handler


class ARTSHandler():
    """ARTS Message Handler."""

    def __init__(self, scheduler, profiler):
        self.scheduler = scheduler
        self.profiler = profiler

    def _get_object(self, rt, model=Runtime):
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

        print("\n[Registration] {}".format(msg.payload))

        action = msg.get('action')
        if action == 'create':
            db_entry = self.__object_from_dict(Runtime, msg.get('data'))
            db_entry.save()
            self.profiler.register_runtime(
                msg.get('data', 'uuid'), msg.get('data', 'name'))
            return messages.Response(
                msg.topic, msg.get('object_id'),
                RuntimeSerializer(db_entry, many=False).data)
        elif action == 'delete':
            runtime = self._get_object(msg.get('data', 'uuid'), model=Runtime)
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
            try:
                file = msg.get('data', 'args', 1)
            except:
                file = msg.get('data', 'filename')
        else:
            file = msg.get('data', 'filename')

        try:
            return File.objects.get(name=file)
        except File.DoesNotExist:
            return File.objects.create(
                name=file, type=msg.get('data', 'filetype'))

    def __get_runtime_or_schedule(self, msg, module):
        """Get parent runtime, or allocate target runtime."""
        sched_ret = self.scheduler.schedule_new_module(module)
        if 'parent' in msg.get('data'):
            if (msg.payload['data']['parent']):
                rt = msg.get('data', 'parent', 'uuid')
                sched_ret = self._get_object(rt, model=Runtime)
        return sched_ret

    def __create_module(self, msg, send_wasm=False):
        """Handle create message."""
        if send_wasm:
            # If here, send the WASM file over to the runtime.
            module = self._get_object(
                msg.get('data', 'details', 'uuid'), model=Module)
            if module.filetype != FileType.WA:
                raise messages.FileNotFound(module.filename)
            module.wasm = file_handler.get_wasm(module.filename)
        else:
            data = msg.get('data')
            if 'apis' not in data:
                data['apis'] = ['wasm', 'wasi']
            if 'filetype' not in data:
                if "python" in str(data.get("filename")):
                    data['filetype'] = FileType.PY
                else:
                    data['filetype'] = FileType.WA

            module = self.__object_from_dict(Module, data)
            module.source = self.__create_or_get_file(msg)
            module.parent = self.__get_runtime_or_schedule(msg, module)
            module.save()
            self.profiler.register_module(
                msg.get('data', 'uuid'), msg.get('data', 'name'))

        return messages.Request(
            "{}/{}".format(msg.topic, module.parent.uuid), "create",
            ModuleSerializer(module, many=False).data)

    def __delete_module(self, msg):
        """Handle delete message."""
        module_id = msg.get('data', 'uuid')
        module = self._get_object(module_id, model=Module)
        uuid_current = str(module.parent.uuid)

        data = msg.get('data')
        if 'send_to_runtime' in data:
            send_rt = data['send_to_runtime']
            module.parent = self._get_object(send_rt, model=Runtime)
            module.save()
        else:
            send_rt = None
            module.delete()

        return messages.Request(
            "{}/{}".format(msg.topic, uuid_current), "delete", {
                "type": "module", "uuid": module_id,
                "send_to_runtime": send_rt})

    def __exited_module(self, msg):
        """Remove module from database."""
        module_id = msg.get('data', 'uuid')
        module = self._get_object(module_id, model=Module)
        module.delete()
        return None

    def control(self, msg):
        """Handle per-module control message."""
        # arts_resp -> is a message we sent, should be ignored
        msg_type = msg.get('type')
        if msg_type == 'arts_resp':
            return None

        print("\n[Control] {}".format(msg.payload))

        if msg_type == 'runtime_resp':
            result = msg.get('data', 'result')
            if result == "no file":
                # Send the WASM/AOT file over
                return self.__create_module(msg, True)
            else:
                return self.__create_module_ack(msg)
        elif msg_type == 'arts_req':
            action = msg.get('action')
            if action == 'create':
                return self.__create_module(msg, False)
            elif action == 'delete':
                return self.__delete_module(msg)
            elif action == 'exited':
                return self.__exited_module(msg)
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
        return None
