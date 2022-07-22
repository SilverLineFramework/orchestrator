"""Runtime registration."""

from django.forms.models import model_to_dict

from pubsub import messages
from api.models import Runtime

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

            print(runtime.uuid)
            print(model_to_dict(runtime))

            return messages.Response(
                msg.topic, msg.get('object_id'), model_to_dict(runtime))

        elif action == 'delete':
            runtime = self._get_object(msg.get('data', 'uuid'), model=Runtime)
            runtime.alive = False
            runtime.save()
            return messages.Response(
                msg.topic, msg.get('object_id'), model_to_dict(runtime))

        else:
            raise messages.InvalidArgument("action", msg.get('action'))
