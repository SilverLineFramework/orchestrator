"""Data store classes."""

import os
import numpy as np


class DataStore:
    """Chunked data store.

    Parameters
    ----------
    dir : str
        Target data directory. Chunks will be stored as
        ```{dir}_{n}.npz```
        for base directory `dir`, 0-indexed chunk number `n`.
    chunk : str
        Number of data points to store in a single file.
    """

    def __init__(self, dir="data", chunk=10000):
        self.head = []
        self.size = 0
        self.chunk_index = 0
        self.chunk = chunk
        self.dir = dir
        os.makedirs(os.path.dirname(self.dir), exist_ok=True)

    def save(self):
        """Save chunk and start new."""
        dst = self.dir + "_{}.npz".format(self.chunk_index)
        np.savez_compressed(dst, data=np.vstack(self.head))
        self.head = []
        self.size = 0
        self.chunk_index += 1

    def update(self, data):
        """Add rows to data store.

        Triggers save and re-chunk when the data size exceeds the set
        threshold. Note that since multiple rows are written at once, the
        maximum chunk size may exceed the threshold.

        Parameters
        ----------
        data : np.array with shape (n, d)
            Will be stacked along the (n) axis and saved.
        """
        self.head.append(data)
        self.size += data.shape[0]
        if self.size >= self.chunk:
            self.save()
