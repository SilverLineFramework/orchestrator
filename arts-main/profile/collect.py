"""Data collector."""

import os
import uuid
import atexit
import numpy as np
import json
from django.conf import settings
from datetime import datetime

from arts_core.models import Module, File
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
        'wall_time': np.uint64,
        'cpu_time': np.uint64,
        'memory': np.uint32,
        'ch_in': np.uint32,
        'ch_out': np.uint32,
        'ch_loopback': np.uint32,
    }

    def __init__(self, dir="data"):
        self.base_dir = dir
        self._init()

    def _init(self):

        self.dir = os.path.join(
            self.base_dir, datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
        self.data = {}
        self.runtimes = {}
        self.modules = {}
        self._files = {}

    def _as_uint8(self, x):
        """Cast string UUID as dense uint8 buffer."""
        return np.frombuffer(uuid.UUID(x).bytes, dtype=np.uint8)

    def _chunk_size(self, data):
        if "opcodes" in data:
            return settings.INTERP_CHUNK_SIZE
        else:
            return settings.AOT_CHUNK_SIZE

    def update(self, module_id=None, runtime_id=None, data=None):
        """Update profile state."""
        file_id = "file-{}".format(self._module_index(module_id))
        if file_id not in self.data:
            self.data[file_id] = DataStore(
                dir=os.path.join(self.dir, file_id),
                chunk=self._chunk_size(data))

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
        if module_id not in self._files:
            self._files[module_id] = (
                Module.objects.get(pk=module_id).source.index)
        return self._files[module_id]

    def save(self, metadata):
        """Save chunk and start new."""
        for _, v in self.data.items():
            v.save()

        files = {source.name: source.index for source in File.objects.all()}
        with open(os.path.join(self.dir, "manifest.json"), 'w') as f:
            json.dump({
                "files": files,
                "runtimes": self.runtimes,
                "modules": self.modules,
                **metadata
            }, f, indent=4)

    def reset(self, metadata):
        """Reset profiling data and save to new directory."""
        self.save(metadata)
        self._init()
