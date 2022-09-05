"""Core Models."""

import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _


class FileType(models.TextChoices):
    """File type enum."""

    WA = 'WA', _('WASM')
    PY = 'PY', _('PYTHON')
    EXT = 'EXT'


class State(models.TextChoices):
    """Module state enum."""

    ALIVE = 'A', _('ALIVE')
    DEAD = 'D', _('DEAD')
    EXITING = 'E', _('EXITING')
    KILLED = 'K', _('KILLED')


class FaultCrash(models.TextChoices):
    """Crash fault tolerance enum."""

    IGNORE = 'ignore'
    RESTART = 'restart'


def _default_runtime_apis():
    return ["wasm", "wasi"]


def _default_required_apis():
    return ["wasm", "wasi"]


def _emptylist():
    return []


def _uuidstr():
    return str(uuid.uuid4())


class Runtime(models.Model):
    """Available SilverLine runtimes."""

    TYPE = "Runtime"

    INPUT_ATTRS = [
        "uuid", "name", "apis", "runtime_type", "max_nmodules", "page_size",
        "aot_target", "platform", "metadata"]
    OUTPUT_SHORT = ["uuid", "name", "runtime_type", "aot_target"]

    uuid = models.CharField(primary_key=True, max_length=64, default=_uuidstr)
    "Runtime UUID."

    name = models.CharField(max_length=255, default='runtime')
    "Runtime short name (len <= 255)."

    updated_at = models.DateTimeField(auto_now=True)
    "Last time the runtime was updated/created"

    apis = models.JSONField(blank=True, default=_default_runtime_apis)
    "Supported APIs."

    runtime_type = models.CharField(max_length=16, default="linux")
    "Runtime type (browser, linux, embedded, special)"

    ka_interval_sec = models.IntegerField(default=60)
    "Keepalive interval (seconds)"

    ka_ts = models.DateTimeField(auto_now_add=True)
    "Last keepalive timestamp"

    max_nmodules = models.IntegerField(default=100)
    "Max number of modules suppoprted by runtime"

    page_size = models.IntegerField(default=65536)
    "WASM pagesize. Default = 64KiB. Memory-constrained embedded runtimes can "
    "use smaller page size of 4KiB."

    aot_target = models.CharField(max_length=500, default="{}", blank=True)
    "AOT target details, including CPU architecture, target ISA and ABI, i.e. "
    "x86_64.tigerlake"

    metadata = models.JSONField(blank=True, null=True)
    "Optional metadata"

    platform = models.JSONField(blank=True, null=True)
    "Platform manifest"

    status = models.CharField(max_length=8, default=State.ALIVE)
    "Runtime state (A=Alive, D=Dead)."

    def natural_key(self):
        """Makes objects with RT as foreign key use UUID when serialized."""
        return self.uuid

    def __str__(self):
        """Debug information."""
        return "[{}] {}:{}".format(
            self.name, self.runtime_type, str(self.uuid))


class Module(models.Model):
    """Currently running modules."""

    TYPE = "Module"

    INPUT_ATTRS = [
        "uuid", "name", "filename", "filetype", "apis", "args", "env",
        "channels", "peripherals", "resources", "fault_crash", "metadata"]
    OUTPUT_SHORT = ["uuid", "name", "parent", "filename"]

    uuid = models.CharField(primary_key=True, max_length=64, default=_uuidstr)
    "Module UUID."

    name = models.CharField(max_length=255, default='module')
    "Module short name (len < 255)."

    parent = models.ForeignKey(
        'Runtime', on_delete=models.CASCADE, related_name='children',
        blank=True, null=True)
    "Parent runtime (runtime where the module is running"

    filename = models.TextField(blank=False)
    "Program file (required)."

    filetype = models.CharField(max_length=8, default=FileType.WA)
    "File type (PY, WA, EXT)"

    apis = models.JSONField(default=_default_required_apis, blank=True)
    "APIs required by the module."

    args = models.JSONField(default=_emptylist, blank=True)
    "Arguments to pass to the module at startup."

    env = models.JSONField(default=_emptylist, blank=True)
    "Environment path to pass to the module at startup."

    channels = models.JSONField(default=_emptylist, blank=True)
    "Channels to open at startup."

    peripherals = models.JSONField(default=_emptylist, blank=True)
    "Required peripherals."

    resources = models.JSONField(blank=True, null=True)
    "Resource reservation (runtime/period with SCHED_DEADLINE)"

    fault_crash = models.CharField(max_length=16, default=FaultCrash.IGNORE)
    "Fault handling behavior on crash (ignore or restart)."

    status = models.CharField(max_length=8, default=State.ALIVE)
    "Module state (A=Alive, D=Dead, E=Exiting, K=Killed). Killed modules "
    "respawn if the parent is resurrected."

    def __str__(self):
        """Django admin page display row."""
        return "[{}] {}:{}".format(
            self.name, self.source.name, str(self.uuid))
