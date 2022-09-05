"""Runtime registration."""

import logging
from django.conf import settings
from django.forms.models import model_to_dict

from pubsub import messages
from orchestrator.models import State, Runtime, Module

from .base import ControlHandler


class Registration(ControlHandler):
    """Runtime registration."""

    def __init__(self):
        self.topic = settings.MQTT_REG
        self._log = logging.getLogger("registration")

    def create_runtime(self, msg):
        """Create or resurrect runtime."""
        # Runtime UUID already exists -> resurrect
        try:
            rt_uuid = msg.get('data', 'uuid')
            runtime = Runtime.objects.get(uuid=rt_uuid)
            runtime.status = State.ALIVE
            runtime.save()

            modules = Module.objects.filter(
                parent=runtime, status=State.KILLED)
            self._log.warn("Dead runtime resurrected: {}".format(rt_uuid))
            self._log.warn("Respawning {} modules.".format(len(modules)))

            # Respawn dead modules
            for mod in modules:
                mod.status = State.ALIVE
                mod.save()

            return [
                messages.Response(
                    msg.topic, msg.get('object_id'), model_to_dict(runtime))
            ] + [
                messages.Request(
                    "{}/{}".format(settings.MQTT_CONTROL, runtime.uuid),
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
        runtime.status = State.DEAD
        runtime.save()

        # Also mark all related modules as dead, but with respawn enabled
        killed = Module.objects.filter(parent=runtime, status=State.ALIVE)
        for mod in killed:
            mod.status = State.KILLED
            mod.save()
        if len(killed) > 0:
            self._log.warn(
                "Runtime exited, killing {} modules; may be "
                "resurrected.".format(len(killed)))

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
