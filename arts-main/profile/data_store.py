"""Data store classes."""

import os
import numpy as np


class DataStore:
    """Chunked data store.

    Parameters
    ----------
    dir : str
        Target data directory. Should assume all contents belong to this data
        store.
    chunk : str
        Number of data points to store in a single file.
    """

    def __init__(self, dir="data", chunk=1024):
        self.head = {}
        self.index = 0
        self.chunk_index = 0
        self.chunk = chunk
        self.dir = dir
        os.makedirs(self.dir, exist_ok=True)

    def save(self):
        """Save chunk and start new."""
        self.chunk_index += 1
        dst = os.path.join(self.dir, "chunk-{}.npz".format(self.chunk_index))
        head_cropped = {k: v[:self.index] for k, v in self.head.items()}
        np.savez_compressed(dst, size=np.uint32(self.index), **head_cropped)
        self.head = {}
        self.index = 0

    def _generate_array(self, item):
        """Generate new array."""
        return np.zeros([self.chunk] + list(item.shape), dtype=item.dtype)

    def update(self, data):
        """Add row to data store."""
        for k, v in data.items():
            if k not in self.head:
                self.head[k] = self._generate_array(v)
            self.head[k][self.index] = v

        self.index += 1
        if self.index >= self.chunk:
            self.save()
