"""Handler for module control messages."""

from django.forms.models import model_to_dict
from django.conf import settings

from orchestrator.models import State, Runtime, Module

from .handler_base import ControlHandler
from . import messages


class Control(ControlHandler):
    """Runtime control messages."""

    NAME = "ctrl"
    TOPIC = "proc/control/#"

    # if parent is not given will default to schedule on this runtime
    __DFT_RUNTIME_NAME = "pyruntime"

    def create_module_ack(self, msg):
        """Handle ACK sent after scheduling module.

        TODO: Should update a flag if ok and reschedule otherwise; currently
        not implemented in the runtime.
        """
        return None

    def __get_runtime_or_schedule(self, msg):
        """Get parent runtime, or allocate target runtime."""
        try:
            parent = self._get_object(msg.get('data', 'parent'), model=Runtime)
        except messages.MissingField:
            parent = self._get_object(
                Control.__DFT_RUNTIME_NAME, model=Runtime)

        return parent

    def create_module(self, msg):
        """Handle create message."""
        data = msg.get('data')

        try:
            module = self._get_object(msg.get('data', 'uuid'), model=Module)
            if module.status == State.ALIVE:
                # module is running, will error out with a duplicate UUID
                raise messages.DuplicateUUID(data, obj_type='module')
            else:
                module.delete()
        # No conflict or UUID not specified
        except (messages.UUIDNotFound, messages.MissingField):
            pass

        module = self._object_from_dict(Module, data)
        parent = self.__get_runtime_or_schedule(msg)
        module.parent = parent

        active = Module.objects.filter(parent=parent, status=State.ALIVE)
        if active.count() >= parent.max_nmodules:
            module.status = State.QUEUED
            module.save()
            self.log.info("Module queued: {}".format(module.uuid))
        else:
            module.status = State.ALIVE
            module.save()
            return messages.Request(
                "/".join([settings.REALM, "proc/control", module.parent.uuid]),
                "create", {"type": "module", **model_to_dict(module)})

    def delete_module(self, msg):
        """Handle delete message."""
        module_id = msg.get('data', 'uuid')
        module = self._get_object(module_id, model=Module)
        module.status = State.EXITING
        module.save()

        return messages.Request(
            "/".join([settings.REALM, "proc/control", module.parent.uuid]),
            "delete", {"type": "module", "uuid": module_id})

    def exited_module(self, msg):
        """Remove module from database."""
        module_id = msg.get('data', 'uuid')
        module = self._get_object(module_id, model=Module)
        module.status = State.DEAD
        module.save()

        queue = Module.objects.filter(
            parent=module.parent, status=State.QUEUED)
        if queue.count() > 0:
            head = queue.order_by('index')[0]
            head.state = State.ALIVE
            return messages.Request(
                "/".join([settings.REALM, "proc/control", head.parent.uuid]),
                "create", {"type": "module", **model_to_dict(head)})

    def handle(self, msg):
        """Handle per-module control message."""
        self.log.info(msg.payload)
        match (msg.get('action'), msg.get('type')):
            case ('create', 'resp'):
                return self.create_module_ack(msg)
            case ('create', 'req'):
                return self.create_module(msg)
            case ('delete', 'req'):
                return self.delete_module(msg)
            case ('exited', 'req'):
                return self.exited_module(msg)
            case unknown:
                raise messages.InvalidArgument('action/type', unknown)
