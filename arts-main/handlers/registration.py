"""Runtime registration."""

from pubsub import messages
from arts_core.serializers import RuntimeSerializer
from arts_core.models import Runtime

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
            self.callback("create_runtime", runtime)
            return messages.Response(
                msg.topic, msg.get('object_id'),
                RuntimeSerializer(runtime, many=False).data)

        elif action == 'delete':
            runtime = self._get_object(msg.get('data', 'uuid'), model=Runtime)
            body = RuntimeSerializer(runtime, many=False).data
            runtime.delete()
            self.callback("delete_runtime", runtime)
            return messages.Response(msg.topic, msg.get('object_id'), body)

        else:
            raise messages.InvalidArgument("action", msg.get('action'))
