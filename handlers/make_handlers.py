"""Handler entry point."""

from .registration import Registration
from .control import Control
from .keepalive import Keepalive


def message_handlers():
    """Create message handlers."""
    # scheduler = LeastModulesFirstScheduler()
    scheduler = None
    return {
        "reg": Registration(),
        "control": Control(scheduler),
        "keepalive": Keepalive(),
    }
