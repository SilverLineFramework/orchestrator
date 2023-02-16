"""Core Models."""

import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _


class State(models.TextChoices):
    """Module state enum."""

    QUEUED = 'Q', _('QUEUED')
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


class Manager(models.Model):
    """SilverLine runtime managers."""

    TYPE = "Manager"

    INPUT_ATTRS = ['uuid', 'name']
    OUTPUT_SHORT = ['uuid', 'name']

    uuid = models.CharField(primary_key=True, max_length=64, default=_uuidstr)
    "Manager UUID."

    name = models.CharField(max_length=255, default="manager")
    "Manager short name (len < 255)."

    status = models.CharField(max_length=8, default=State.ALIVE)
    "Manager state (A=Alive, D=Dead)."


class Runtime(models.Model):
    """Available SilverLine runtimes."""

    TYPE = "Runtime"

    INPUT_ATTRS = [
        "uuid", "name", "runtime_type", "max_nmodules", "apis", "platform",
        "metadata"]
    OUTPUT_SHORT = ["uuid", "name", "runtime_type"]

    uuid = models.CharField(primary_key=True, max_length=64, default=_uuidstr)
    "Runtime UUID."

    name = models.CharField(max_length=255, default='runtime')
    "Runtime short name (len <= 255)."

    runtime_type = models.CharField(max_length=16, default="linux")
    "Runtime type"

    max_nmodules = models.IntegerField(default=1)
    "Maximum number of modules supported by the runtime"

    apis = models.JSONField(blank=True, default=_default_runtime_apis)
    "Supported APIs"

    platform = models.JSONField(blank=True, null=True)
    "Platform manifest"

    metadata = models.JSONField(blank=True, null=True)
    "Optional metadata"

    ka_interval_sec = models.IntegerField(default=60)
    "Keepalive interval (seconds)"

    ka_ts = models.DateTimeField(auto_now_add=True)
    "Last keepalive timestamp"

    updated_at = models.DateTimeField(auto_now=True)
    "Last time the runtime was updated/created"

    status = models.CharField(max_length=2, default=State.ALIVE)
    "Runtime state (A=Alive, D=Dead)"

    parent = models.ForeignKey(Manager, on_delete=models.CASCADE, null=True)
    "Runtime manager, if applicable."

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

    INPUT_ATTRS = ["uuid", "name", "file", "apis", "args", "channels"]
    OUTPUT_SHORT = ["uuid", "name", "parent", "file"]

    index = models.AutoField(primary_key=True)
    "Auto-incrementing primary key used for queuing."

    uuid = models.CharField(max_length=64, default=_uuidstr)
    "Module UUID."

    name = models.CharField(max_length=255, default='module')
    "Module short name (len < 255)."

    parent = models.ForeignKey(
        'Runtime', on_delete=models.CASCADE, related_name='children',
        blank=True, null=True)
    "Parent runtime (runtime where the module is running"

    file = models.TextField(blank=False)
    "Program file (required)."

    apis = models.JSONField(default=_default_required_apis, blank=True)
    "APIs required by the module."

    args = models.JSONField(default=_emptylist, blank=True)
    "Arguments (argv, environment variables, etc) to pass to the module."

    channels = models.JSONField(default=_emptylist, blank=True)
    "Channels to open at startup."

    status = models.CharField(max_length=2, default=State.ALIVE)
    "Module state (Q=Queued, A=Alive, D=Dead, E=Exiting, K=Killed). Killed "
    "modules respawn if the parent is resurrected."

    def __str__(self):
        """Django admin page display row."""
        return "[{}] {}:{}".format(
            self.name, self.parent, str(self.uuid))
