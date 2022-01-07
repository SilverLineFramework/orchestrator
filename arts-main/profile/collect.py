"""Data collector."""

import os
import numpy as np
import pandas as pd


class ProfileCollector:
    """Profile data collector."""

    def __init__(self, dir="data", save_every=10):
        self.data = {}
        self.dir = dir

        self.size = 0
        self.save_every = save_every

    def add(self, msg):
        """Add message to data store."""
        mod = msg['module_id']
        rt = msg['runtime_id']
        if mod not in self.data:
            self.data[mod] = {}
        if rt not in self.data[mod]:
            self.data[mod][rt] = pd.DataFrame()

        self.data[mod][rt] = self.data[mod][rt].append(
            msg['data'], ignore_index=True)
        self.size += 1

    def save(self):
        """Save data store as CSV."""
        if self.size % self.save_every == 0:
            print("[Profile] saving data (n={})...".format(self.size))
            for mod, mod_dict in self.data.items():
                os.makedirs(os.path.join(self.dir, mod), exist_ok=True)
                for rt, rt_df in mod_dict.items():
                    rt_df.to_csv(os.path.join(self.dir, mod, rt + ".csv"))
