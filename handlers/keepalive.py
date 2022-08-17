"""Keepalive handler."""

from django.conf import settings
from .base import BaseHandler


class Keepalive(BaseHandler):
    """Keepalive message."""

    def __init__(self):
        self.topic = settings.MQTT_KEEPALIVE

    def handle(self, msg):
        """Handle keepalive message."""
        # Currently unused
        return None
