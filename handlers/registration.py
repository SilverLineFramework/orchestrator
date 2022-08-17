"""Runtime registration."""

import logging
from django.forms.models import model_to_dict

from pubsub import messages
from api.models import Runtime, Module

from .base import BaseHandler


class Registration(BaseHandler):
    """Runtime registration."""

    def __init__(self):
        self._log = logging.getLogger("registration")

    def create_runtime(self, msg):
        """Create or resurrect runtime."""
        # Runtime UUID already exists -> resurrect
        try:
            rt_uuid = msg.get('data', 'uuid')
            runtime = Runtime.objects.get(uuid=rt_uuid)
            runtime.alive = True
            runtime.save()

            modules = Module.objects.filter(parent=runtime, respawn=True)
            self._log.warn("Dead runtime resurrected: {}".format(rt_uuid))
            self._log.warn("Respawning {} modules.".format(len(modules)))

            # Respawn dead modules
            for mod in modules:
                mod.alive = True
                mod.respawn = False
                mod.save()
            return [
                messages.Request(
                    "{}/{}".format(msg.topic, runtime.uuid),
                    "create", {"type": "module", **model_to_dict(mod)})
                for mod in modules]

        # Doesn't exist -> create new
        except Runtime.DoesNotExist:
            runtime = self._object_from_dict(Runtime, msg.get('data'))
            runtime.save()
        return messages.Response(
            msg.topic, msg.get('object_id'), model_to_dict(runtime))

    def delete_runtime(self, msg):
        """Delete runtime."""
        runtime = self._get_object(msg.get('data', 'uuid'), model=Runtime)
        runtime.alive = False
        runtime.save()

        # Also mark all related modules as dead, but with respawn enabled
        for mod in Module.objects.filter(parent=runtime):
            mod.alive = False
            mod.respawn = True
            mod.save()

        return messages.Response(
            msg.topic, msg.get('object_id'), model_to_dict(runtime))

    def handle(self, msg):
        """Handle registration message."""
        if msg.get('type') == 'arts_resp':
            return None

        self._log.info(msg.payload)

        action = msg.get('action')
        if action == 'create':
            return self.create_runtime(msg)
        elif action == 'delete':
            return self.delete_runtime(msg)
        else:
            raise messages.InvalidArgument("action", msg.get('action'))
