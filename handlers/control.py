"""Handler for module control messages."""

import logging

from django.db import IntegrityError
from django.conf import settings
from django.forms.models import model_to_dict

from pubsub import messages
from api.models import FileType, Runtime, Module

from .base import BaseHandler


class Control(BaseHandler):
    """Runtime control messages."""

    def __init__(self, *args, **kwargs):
        self.topic = settings.MQTT_CONTROL
        self._log = logging.getLogger("control")
        super().__init__(*args, **kwargs)

    def create_module_ack(self, msg):
        """Handle ACK sent after scheduling module.

        TODO: Should update a flag if ok and reschedule otherwise; currently
        not implemented in the runtime.
        """
        return None

    def __get_runtime_or_schedule(self, msg, module):
        """Get parent runtime, or allocate target runtime."""
        # sched_ret = self.scheduler.schedule_new_module(module)
        # if 'parent' in msg.get('data'):
        #     if (msg.payload['data']['parent']):
        #        rt = msg.get('data', 'parent')
        #        sched_ret = self._get_object(rt, model=Runtime)
        # return sched_ret
        return self._get_object(msg.get('data', 'parent'), model=Runtime)

    def create_module(self, msg):
        """Handle create message."""
        data = msg.get('data')
        if 'apis' not in data:
            data['apis'] = ['wasm', 'wasi']
        if 'filetype' not in data:
            data['filetype'] = FileType.WA

        module = self._object_from_dict(Module, data)
        module.parent = self.__get_runtime_or_schedule(msg, module)

        try:
            module.save()
        except IntegrityError as e:
            if 'UNIQUE constraint' in str(e):
                raise messages.DuplicateUUID(data, obj_type='module')

        return messages.Request(
            "{}/{}".format(msg.topic, module.parent.uuid),
            "create", {"type": "module", **model_to_dict(module)})

    def delete_module(self, msg):
        """Handle delete message."""
        module_id = msg.get('data', 'uuid')
        module = self._get_object(module_id, model=Module)
        uuid_current = module.parent.uuid
        module.alive = False
        module.save()

        return messages.Request(
            "{}/{}".format(msg.topic, uuid_current), "delete", {
                "type": "module", "uuid": module_id})

    def exited_module(self, msg):
        """Remove module from database."""
        module = self._get_object(msg.get('data', 'uuid'), model=Module)
        module.alive = False
        module.save()

    def handle(self, msg):
        """Handle per-module control message."""
        # arts_resp -> is a message we sent, should be ignored
        msg_type = msg.get('type')
        if msg_type == 'arts_resp':
            return None

        self._log.info(msg.payload)

        if msg_type == 'runtime_resp':
            return self.create_module_ack(msg)
        elif msg_type == 'arts_req':
            action = msg.get('action')
            if action == 'create':
                return self.create_module(msg)
            elif action == 'delete':
                return self.delete_module(msg)
            elif action == 'exited':
                return self.exited_module(msg)
            else:
                raise messages.InvalidArgument('action', action)
        else:
            raise messages.InvalidArgument('type', msg_type)
