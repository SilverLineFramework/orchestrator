"""Keepalive handler."""

from .handler_base import ControlHandler


class Keepalive(ControlHandler):
    """Keepalive message."""

    NAME = "ka"
    TOPIC = "proc/keepalive/#"

    def handle(self, msg):
        """Handle keepalive message."""
        # Currently unused
        return None
