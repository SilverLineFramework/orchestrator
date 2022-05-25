"""Handler for module control messages."""

from django.db import IntegrityError

from pubsub import messages
from wasm_files import file_handler
from arts_core.models import FileType, Runtime, Module, File
from arts_core.serializers import ModuleSerializer

from .base import BaseHandler


class Control(BaseHandler):
    """Runtime control messages."""

    def __init__(self, scheduler, *args, **kwargs):
        self.scheduler = scheduler
        super().__init__(*args, **kwargs)

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
            except messages.MissingField:
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

            module = self._object_from_dict(Module, data)
            module.source = self.__create_or_get_file(msg)
            module.parent = self.__get_runtime_or_schedule(msg, module)

            try:
                module.save()
            except IntegrityError as e:
                if 'UNIQUE constraint' in str(e):
                    raise messages.DuplicateUUID(data, obj_type='module')

            self.callback("create_module", module)

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
            self.callback("migrate_module", module)
            module.save()
        else:
            send_rt = None
            self.callback("delete_module", module)
            module.delete()

        return messages.Request(
            "{}/{}".format(msg.topic, uuid_current), "delete", {
                "type": "module", "uuid": module_id,
                "send_to_runtime": send_rt})

    def __exited_module(self, msg):
        """Remove module from database."""
        module_id = msg.get('data', 'uuid')
        module = self._get_object(module_id, model=Module)
        self.callback("exited_module", module)
        module.delete()
        return None

    def handle(self, msg):
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
