"""Profile data collection."""

import numpy as np

from pubsub import messages
from .base import BaseHandler


class Profile(BaseHandler):
    """Profiling messages."""

    @staticmethod
    def decode(msg):
        """Decode binary profiling message.

        See corresponding code in `runtime-linux/profile/send.c`:
        ```
        *size = (
            UUID_SIZE           // runtime_id : char[40]
            + UUID_SIZE         // module_id : char[40]
            + sizeof(uint32_t)  // number of profiling entries
            + p->num_entries * dim * sizeof(uint64_t));
                                // profiling data (+ opcodes if present)
        ```
        """
        entries = int.from_bytes(msg.payload[80:84], 'little')
        return messages.Message(msg.topic, {
            "runtime_id": msg.payload[:40].decode().rstrip('\0'),
            "module_id": msg.payload[40:80].decode().rstrip('\0'),
            "data": np.frombuffer(
                msg.payload[84:], dtype=np.int64).reshape([entries, -1])
        })

    def handle(self, msg):
        """Save profiling data."""
        self.callback("profile", msg.payload)
