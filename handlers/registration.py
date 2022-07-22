"""Runtime registration."""

from django.forms.models import model_to_dict

from pubsub import messages
from api.models import Runtime, Module

from .base import BaseHandler


class Registration(BaseHandler):
    """Runtime registration."""

    def handle(self, msg):
        """Handle registration message."""
        if msg.get('type') == 'arts_resp':
            return None

        print("[Registration] {}".format(msg.payload))

        action = msg.get('action')
        if action == 'create':
            runtime = self._object_from_dict(Runtime, msg.get('data'))
            runtime.save()
            return messages.Response(
                msg.topic, msg.get('object_id'), model_to_dict(runtime))

        elif action == 'delete':
            runtime = self._get_object(msg.get('data', 'uuid'), model=Runtime)
            runtime.alive = False
            runtime.save()

            # Also mark all related modules as dead
            for mod in Module.objects.filter(parent=runtime):
                mod.alive = False
                mod.save()

            return messages.Response(
                msg.topic, msg.get('object_id'), model_to_dict(runtime))

        else:
            raise messages.InvalidArgument("action", msg.get('action'))
