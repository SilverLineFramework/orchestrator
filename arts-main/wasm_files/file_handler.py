""" WASM file handler. """
import os
import base64

from django.conf import settings
from pubsub import messages

def get_file_path(instance, filename):
    """Return unix style file path.

    Parameters
    ------------
    instance : django instance
        Required by django backend. Pass None 
        if unsure.
    filename : str
        target filename

    Returns
    --------
    File path string
    """
    n_filename = "{}/{}".format(os.path.splitext(filename)[0], filename)
    return os.path.join(settings.WASM_DIR, n_filename)

def get_wasm(filename):
    """ Return WASM file if found, else return None """
    fpath = get_file_path(None, filename)
    try:
        print("Opening {}".format(fpath))
        with open(fpath, "rb") as f:
            wasm = base64.b64encode(f.read()).decode('utf-8')
        return wasm
    except FileNotFoundError:
        raise messages.FileNotFound(fpath)
