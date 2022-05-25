"""Miscellaneous handlers."""

import numpy as np

from pubsub import messages

from .base import BaseHandler


class Keepalive(BaseHandler):
    """Keepalive message."""

    def handle(self, msg):
        """Handle keepalive message."""
        # Currently unused
        return None


class Debug(BaseHandler):
    """Debug message."""

    def handle(self, msg):
        """Print out debug message."""
        print("[Debug]", str(msg.payload))


class Special(BaseHandler):
    """Special instructions."""

    def handle(self, msg):
        """Special instructions."""
        action = msg.get('action')

        if action in {"save", "reset"}:
            payload = msg.get('data')
            if not isinstance(payload, dict):
                payload = {"metadata": payload}
            if action == "save":
                self.callback("save", payload)
            else:
                self.callback("reset", payload)
        elif action == "echo":
            return messages.Message("realm/proc/echo", msg.payload)
        else:
            raise messages.InvalidArgument('action', action)
