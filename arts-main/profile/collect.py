"""Data collector."""

import os
import uuid
import atexit
import numpy as np
import json

from arts_core.models import Module, File, Runtime
from .data_store import DataStore


class Collector:
    """Profile data collector.

    Saves data as a csv every ```save_every``` iterations, with structure
    ``[runtime_id]/[module_id]````

    Keyword Args
    ------------
    dir : str
        Directory for saving data.
    """

    DATA_TYPES = {
        'start_time': np.uint64,
        'end_time': np.uint64,
        'runtime': np.uint32,
        'memory': np.uint32,
        'ch_in': np.uint32,
        'ch_out': np.uint32,
        'ch_loopback': np.uint32,
        'opcodes': lambda x: np.array(x, dtype=np.uint64)
    }

    def __init__(self, dir="data"):

        self.dir = dir
        self.data = {}
        atexit.register(self.save)

    def _as_uint8(self, x):
        """Cast string UUID as dense uint8 buffer."""
        return np.frombuffer(uuid.UUID(x).bytes, dtype=np.uint8)

    def update(self, module_id=None, runtime_id=None, data=None):
        """Update profile state."""
        file_id = "file-{}".format(self._module_index(module_id))
        if file_id not in self.data:
            self.data[file_id] = DataStore(
                dir=os.path.join(self.dir, file_id), chunk=256)

        data_tc = {k: v(data[k]) for k, v in self.DATA_TYPES.items()}
        data_tc['module_id'] = self._as_uint8(module_id)
        data_tc['runtime_id'] = self._as_uint8(runtime_id)
        self.data[file_id].update(data_tc)

    def _module_index(self, module_id):
        """Get source file index for module UUID."""
        return Module.objects.get(pk=module_id).source.index

    def save(self):
        """Save chunk and start new."""
        for _, v in self.data.items():
            v.save()

        manifest = {source.name: source.index for source in File.objects.all()}
        with open(os.path.join(self.dir, "manifest.json"), 'w') as f:
            json.dump(manifest, f, indent=4)

        runtimes = {rt.name: str(rt.uuid) for rt in Runtime.objects.all()}
        with open(os.path.join(self.dir, "runtimes.json"), 'w') as f:
            json.dump(runtimes, f, indent=4)
