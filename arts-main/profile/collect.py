"""Data collector."""

import os
import numpy as np
import pandas as pd


class ProfileCollector:
    """Profile data collector."""

    def __init__(self, dir="data"):
        self.data = {}
        self.dir = dir

    def add(self, msg):
        """Add message to data store."""
        mod = msg.payload['module_id']
        rt = msg.payload['runtime_id']
        if mod not in self.data:
            self.data[mod] = {}
        if rt not in self.data[mod]:
            self.data[mod][rt] = pd.DataFrame()

        self.data[mod][rt].append(msg['data'])

    def save(self):
        """Save data store as CSV."""
        for mod, mod_dict in self.data.items():
            os.makedirs(os.path.join(self.dir, mod), exist_ok=True)
            for rt, rt_df in mod_dict.items():
                rt_df.to_csv(os.path.join(self.dir, mod, rt))
