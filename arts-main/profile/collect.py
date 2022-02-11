"""Data collector."""

import os
import json

from .base import BaseProfiler

from arts_core.models import Module, File


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

        super().__init__(dir=dir)

        self.data = {}

        for file_id in os.listdir(self._path()):
            with open(self._path(file_id)) as f:
                d = json.load(f)
            self.data[os.path.splitext(file_id)[0]] = d

        self.size = 0
        self.save_every = save_every

    def update(self, module_id=None, runtime_id=None, data=None):
        """Update profile state."""
        file_id = str(self._module_index(module_id))

        if file_id not in self.data:
            self.data[file_id] = []

        data['module_id'] = module_id
        data['runtime_id'] = runtime_id
        self.data[file_id].append(data)

        self.size += 1

        print("[Profile] Received: {}:{} @ {}".format(
            self._module_name(module_id), module_id, runtime_id))

    def save(self):
        """Save state to disk."""
        # if self.size % self.save_every == 0:
        # print("[Profile] saving data (n={})...".format(self.size))
        for k, v in self.data.items():
            with open(self._path(k + ".json"), 'w') as f:
                json.dump(v, f)

        super().save()
