"""Data collector."""

import os
import uuid
import atexit
import numpy as np
import json
from datetime import datetime

from arts_core.models import Module, File, Runtime
from .data_store import DataStore


class Collector:
    """Profile data collector.

    Keyword Args
    ------------
    dir : str or None
        Directory for saving data; will be saved as a subdirectory with the
        datetime, i.e. "data/%Y-%m-%d_%H-%M-%S".
    """

    DATA_TYPES = {
        'start_time': np.uint64,
        'end_time': np.uint64,
        'runtime': np.uint32,
        'memory': np.uint32,
        'ch_in': np.uint32,
        'ch_out': np.uint32,
        'ch_loopback': np.uint32,
    }

    def __init__(self, dir="data"):

        self.dir = os.path.join(
            dir, datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
        self.data = {}
        self.runtimes = {}
        self.modules = {}
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

        if "opcodes" in data:
            data_tc["opcodes"] = np.array(data["opcodes"], dtype=np.uint64)

        self.data[file_id].update(data_tc)

    def register_runtime(self, runtime_id, runtime_name):
        """Register runtime."""
        self.runtimes[runtime_id] = runtime_name

    def register_module(self, module_id, module_name):
        """Register module."""
        self.modules[module_id] = module_name

    def _module_index(self, module_id):
        """Get source file index for module UUID."""
        return Module.objects.get(pk=module_id).source.index

    def save(self):
        """Save chunk and start new."""
        for _, v in self.data.items():
            v.save()

        files = {source.name: source.index for source in File.objects.all()}
        with open(os.path.join(self.dir, "manifest.json"), 'w') as f:
            json.dump({
                "files": files,
                "runtimes": self.runtimes,
                "modules": self.modules
            }, f, indent=4)
