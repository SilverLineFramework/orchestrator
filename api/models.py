"""Core Models."""

import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _


class FileType(models.TextChoices):
    """File type enum."""

    WA = 'WA', _('WASM')
    PY = 'PY', _('PYTHON')
    EXT = 'EXT'


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

    uuid = models.CharField(
        primary_key=True, max_length=64, default=_uuidstr,
        help_text="Runtime UUID.")
    name = models.CharField(
        max_length=255, default='runtime',
        help_text="Runtime short name (len <= 255).")
    updated_at = models.DateTimeField(
        auto_now=True, help_text="Last time the runtime was updated/created")
    apis = models.JSONField(
        blank=True, help_text="Supported APIs.", default=_default_runtime_apis)
    runtime_type = models.CharField(
        max_length=16, default="linux",
        help_text="Runtime type (browser, linux, embedded, special)")
    ka_interval_sec = models.IntegerField(
        default=60, help_text="Keepalive interval (seconds)")
    ka_ts = models.DateTimeField(
        auto_now_add=True, help_text="Last keepalive timestamp")
    max_nmodules = models.IntegerField(
        default=100, help_text="Max number of modules suppoprted by runtime")    
    page_size = models.IntegerField(
        default=65536, help_text=(
            "WASM pagesize. Default = 64KiB. Memory-constrained embedded "
            "runtimes can use smaller page size of 4KiB."))
    aot_target = models.CharField(
        max_length=500, default="{}", blank=True, help_text=(
            "AOT target details, including CPU architecture, target ISA "
            "and ABI, i.e. x86_64.tigerlake"))
    metadata = models.JSONField(
        blank=True, null=True, help_text="Optional metadata")
    platform = models.JSONField(
        blank=True, null=True, help_text="Platform manifest")
    alive = models.BooleanField(
        default=True, help_text="Set to False after runtime exits.")

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
        "channels", "peripherals", "resources", "metadata"]
    OUTPUT_SHORT = ["uuid", "name", "parent", "filename"]

    uuid = models.CharField(
        primary_key=True, max_length=64, default=_uuidstr,
        help_text="Module UUID.")
    name = models.CharField(
        max_length=255, default='module',
        help_text="Module short name (len < 255).")
    parent = models.ForeignKey(
        'Runtime', on_delete=models.CASCADE, related_name='children',
        blank=True, null=True,
        help_text="Parent runtime (runtime where the module is running")
    filename = models.TextField(
        blank=False, help_text="Program file (required).")
    filetype = models.CharField(
        max_length=8, default=FileType.WA,
        help_text="File type (PY, WA, EXT)")
    apis = models.JSONField(
        default=_default_required_apis, blank=True,
        help_text="APIs required by the module.")
    args = models.JSONField(
        default=_emptylist, blank=True,
        help_text="Arguments to pass to the module at startup.")
    env = models.JSONField(
        default=_emptylist, blank=True,
        help_text="Environment path to pass to the module at startup.")
    channels = models.JSONField(
        default=_emptylist, blank=True,
        help_text="Channels to open at startup.")
    peripherals = models.JSONField(
        default=_emptylist, blank=True, help_text="Required peripherals.")
    resources = models.JSONField(
        blank=True, null=True,
        help_text="Resource reservation (runtime/period with SCHED_DEADLINE)")
    alive = models.BooleanField(
        default=True, help_text="Set to False after runtime exits.")

    def __str__(self):
        """Django admin page display row."""
        return "[{}] {}:{}".format(
            self.name, self.source.name, str(self.uuid))
