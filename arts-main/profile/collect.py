"""Data collector."""

import os
import pandas as pd
import json
from datetime import datetime

from django.conf import settings

from arts_core.models import Module
from pubsub.messages import InvalidArgument
from .data_store import DataStore


class Collector:
    """Profile data collector.

    Parameters
    ----------
    dir : str
        Directory for saving data; will be saved as a subdirectory with the
        datetime, i.e. "data/%Y-%m-%d_%H-%M-%S".
    """

    def __init__(self, dir="data"):
        self.base_dir = dir

        # Runtime id cache is never reset.
        self.runtimes = {}

        self._init()

    def _init(self):
        """Attributes cleared on every reset call."""
        self.dir = os.path.join(
            self.base_dir, datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
        self.manifest = []
        self.data = {}
        self.modules = {}

    def _chunk_size(self, data):
        # Long rows -> includes opcodes -> use INTERP_CHUNK_SIZE
        if data.shape[1] > 16:
            return settings.INTERP_CHUNK_SIZE
        else:
            return settings.AOT_CHUNK_SIZE

    def _module_index(self, module_id):
        """Get source file index for module UUID."""
        try:
            file = Module.objects.get(pk=module_id).source
            return file.index, file.name
        except Module.DoesNotExist:
            raise InvalidArgument("module_id", module_id)

    def update(self, data):
        """Update profile state."""
        module_id = data.get('module_id')
        runtime_id = data.get('runtime_id')
        buffer = data.get('data')

        if module_id not in self.data:
            file_id, file = self._module_index(module_id)
            file_id = "file-{}".format(file_id)

            path = os.path.join(self.dir, file_id, module_id)
            self.data[module_id] = DataStore(
                path, chunk=self._chunk_size(buffer))
            self.manifest.append({
                "runtime_id": runtime_id,
                "runtime": self.runtimes.get(runtime_id),
                "module_id": module_id,
                "module": self.modules.get(module_id),
                "file_id": file_id,
                "file": file
            })

        self.data[module_id].update(buffer)

    def create_runtime(self, runtime):
        """Register runtime name to lookup table."""
        self.runtimes[str(runtime.uuid)] = runtime.name

    def create_module(self, module):
        """Register module name to lookup table."""
        self.modules[str(module.uuid)] = module.name

    def delete_module(self, module):
        """Delete module: close out data store; should free up memory."""
        self.data.pop(str(module.uuid)).save()

    def save(self, metadata):
        """Save current chunks and start new."""
        for _, ds in self.data.items():
            ds.save()

        with open(os.path.join(self.dir, "metadata.json"), 'w') as f:
            json.dump(metadata, f)
        pd.DataFrame(self.manifest).to_csv(
            os.path.join(self.dir, "manifest.csv"), index=False)

    def reset(self, metadata):
        """Reset profiling data and save to new directory."""
        self.save(metadata)
        self._init()
