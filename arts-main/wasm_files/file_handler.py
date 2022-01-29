import os
import base64

from django.conf import settings

def get_file_path(instance, filename):
    """ Return unix style complete file path. 
    First arg required by django model backend. 
    Pass None for this argument if unsure """
    n_filename = "%s/%s" % (os.path.splitext(filename)[0], filename)
    return os.path.join(settings.WASM_DIR, n_filename)

def get_wasm(filename):
    "Return WASM file if found, else return None"
    try:
        fpath = get_file_path(None, filename)
        print("Opoening {}".format(fpath))
        with open(fpath, "rb") as f:
            wasm = base64.b64encode(f.read()).decode('utf-8')
        return wasm
    except Exception as e:
        return None

