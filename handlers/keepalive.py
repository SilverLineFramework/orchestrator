"""Keepalive handler."""

from django.conf import settings
from .base import ControlHandler


class Keepalive(ControlHandler):
    """Keepalive message."""

    def __init__(self):
        self.topic = settings.MQTT_KEEPALIVE

    def handle(self, msg):
        """Handle keepalive message."""
        # Currently unused
        return None
