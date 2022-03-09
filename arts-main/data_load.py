"""Data loader."""

import os
import numpy as np
import pandas as pd
import uuid


class TraceLoader:
    """Loader corresponding to the DataStore class for profiling data.

    Note that numpy arrays are 'lazy-loaded', and do not actually populate in
    memory until referenced.
    """

    def __init__(self, dir="data", prefix="aot"):

        self.sources = [s for s in os.listdir(dir) if s.startswith(prefix)]
        self.sources.sort()
        self.chunks = [np.load(os.path.join(dir, s)) for s in self.sources]
        self.size = sum(s['size'] for s in self.chunks)
        self.data = None

        self.uuids = None

    def arrays(self):
        """Load as dictionary of arrays."""
        if self.data is None:

            self.data = {
                k: np.zeros([self.size] + list(v.shape)[1:], dtype=v.dtype)
                for k, v in self.chunks[0].items() if k != 'size'
            }

            idx = 0
            for c in self.chunks:
                size = c['size']
                for k in self.data:
                    self.data[k][idx:idx + size] = c[k][:size]
                idx += size

        return self.data

    def _to_uuid_str(self, column):
        return [str(uuid.UUID(bytes=x.tobytes())) for x in column]

    def _get_uuids(self):
        if self.uuids is None:
            self.uuids = [
                self._to_uuid_str(self.arrays()[s])
                for s in ['module_id', 'runtime_id']]
        return self.uuids

    def dataframe(self):
        """Load as dataframe."""
        raw = self.arrays()

        data = {
            k: v for k, v in raw.items()
            if k not in {'opcodes', 'runtime_id', 'module_id'}
        }
        data['module_id'], data['runtime_id'] = self._get_uuids()
        return pd.DataFrame(data)

    def filter(self, **kwargs):
        """Load dataframe with given filters."""
        df = self.dataframe()
        for k, v in kwargs.items():
            df = df[df[k] == v]
        return df
