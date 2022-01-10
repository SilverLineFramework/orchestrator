"""Data collector."""

import os
import pandas as pd

from .base import BaseProfiler


class Collector(BaseProfiler):
    """Profile data collector.

    Saves data as a csv every ```save_every``` iterations, with structure
    ``[runtime_id]/[module_id]````

    Keyword Args
    ------------
    dir : str
        Directory for saving data.
    save_every : int
        How often to write data.
    """

    def __init__(self, dir="data", save_every=10):
        self.data = {}

        self.size = 0
        self.save_every = save_every

        super().__init__(dir=dir)

    def update(self, module_id=None, runtime_id=None, data=None):
        """Update profile state."""
        if runtime_id not in self.data:
            self.data[runtime_id] = {}
        if module_id not in self.data[runtime_id]:
            self.data[runtime_id][module_id] = pd.DataFrame()

        self.data[runtime_id][module_id] = (
            self.data[runtime_id][module_id].append(data, ignore_index=True))
        self.size += 1

    def save(self):
        """Save state to disk."""
        if self.size % self.save_every == 0:
            print("[Profile] saving data (n={})...".format(self.size))
            for outer, outer_dict in self.data.items():
                os.makedirs(self._path(outer), exist_ok=True)
                for inner, inner_df in outer_dict.items():
                    inner_df.to_csv(self._path(outer, inner + ".csv"))
            super().save()
