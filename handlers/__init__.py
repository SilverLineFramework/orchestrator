"""Pubsub message handlers."""

from .registration import Registration
from .control import Control
from .keepalive import Keepalive

__all__ = ['HANDLERS', 'Registration', 'Control', 'Keepalive']

HANDLERS = {
    'reg': Registration,
    'control': Control,
    'keepalive': Keepalive
}
