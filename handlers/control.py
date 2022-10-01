"""Handler for module control messages."""

import logging

from django.db import IntegrityError
from django.conf import settings
from django.forms.models import model_to_dict

from pubsub import messages
from orchestrator.models import FileType, State, Runtime, Module

from .base import ControlHandler


class Control(ControlHandler):
    """Runtime control messages."""

    # if parent is not given will default to schedule on this runtime
    __DFT_RUNTIME_NAME="pyruntime"
    
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
        try:
            parent_id = msg.get('data', 'parent')
        except messages.MissingField:
            return self._get_object(Control.__DFT_RUNTIME_NAME, model=Runtime)
            
        return self._get_object(parent_id, model=Runtime)

    def create_module(self, msg):
        """Handle create message."""
        data = msg.get('data')
        if 'apis' not in data:
            data['apis'] = ['wasm', 'wasi']
        if 'filetype' not in data:
            data['filetype'] = FileType.WA

        module_id = msg.get('data', 'uuid') 

        module = None
        try: 
            module = self._get_object(module_id, model=Module)
            if module.status == State.ALIVE:
                # module is running, will error out with a duplicate UUID
                raise messages.DuplicateUUID(data, obj_type='module')
            else: 
                module.delete()
        except messages.UUIDNotFound:        
            # ok, will create a new one
            pass 
        
        module = self._object_from_dict(Module, data)          
        module.parent = self.__get_runtime_or_schedule(msg, module)
        
        try:
            module.save()
        except IntegrityError as e:
            if 'UNIQUE constraint' in str(e):
                raise messages.DuplicateUUID(data, obj_type='module') # should not happen!

        return messages.Request(
            "{}/{}".format(msg.topic, module.parent.uuid),
            "create", {"type": "module", **model_to_dict(module)})

    def delete_module(self, msg):
        """Handle delete message."""
        module_id = msg.get('data', 'uuid')
        module = self._get_object(module_id, model=Module)
        uuid_current = module.parent.uuid
        module.status = State.EXITING
        module.save()

        return messages.Request(
            "{}/{}".format(msg.topic, uuid_current), "delete",
            {"type": "module", "uuid": module_id})

    def exited_module(self, msg):
        """Remove module from database."""
        module_id = msg.get('data', 'uuid')
        module = self._get_object(module_id, model=Module)
        module.status = State.DEAD
        module.save()

        return messages.Request(
            settings.MQTT_NOTIF, "exited",
            {"type": "module", "uuid": module_id})

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
