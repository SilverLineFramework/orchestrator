"""Data collection base class."""

import os
import json

from arts_core.models import Module, File


class BaseProfiler:
    """Base class for profiling.

    Keyword Args
    ------------
    dir : str
        Directory for saving checkpoints.
    """

    def __init__(self, dir="data"):
        self.dir = dir

    def _path(self, *args):
        """Compute checkpoint filepath."""
        return os.path.join(self.dir, *args)

    def _module_index(self, module_id):
        """Get source file index for module UUID."""
        return Module.objects.get(pk=module_id).source.index

    def update(self, module_id=None, runtime_id=None, data=None):
        """Update profile state with a single observation.

        Parameters
        ----------
        module_id : str
            Module ID
        runtime_id : str
            Runtime ID
        data : dict
            Profiling data
        """
        raise NotImplementedError()

    def distill(self):
        """Data distillation/summarization step; called externally.

        This method can comsume arbitrarily many system resources, and should
        be called on a separate thread.
        """
        pass

    def save(self):
        """Save manifest of files to disk."""
        res = {}
        for source in File.objects.all():
            modules = Module.objects.filter(source=source)
            res[source.name] = {
                str(mod.uuid): str(mod.parent.uuid) for mod in modules}

        with open(self._path("manifest.json"), 'w') as f:
            json.dump(res, f, indent=4)

    def load(self):
        """Load state from disk."""
        pass
