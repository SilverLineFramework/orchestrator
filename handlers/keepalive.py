"""Keepalive handler."""

from .base import BaseHandler


class Keepalive(BaseHandler):
    """Keepalive message."""

    def handle(self, msg):
        """Handle keepalive message."""
        # Currently unused
        return None
