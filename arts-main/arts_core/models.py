"""Core Models."""

import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _


class FileType(models.TextChoices):
    """File type enum."""

    WA = 'WA', _('WASM')
    PY = 'PY', _('PYTHON')


def _default_apis():
    return [
        "wasi:snapshot_preview1", "wasi:unstable", "wasi:core",
        "wasi:clock", "wasi:environ", "wasi:sock", "wasi:args", "wasi:fd",
        "wasi:path", "wasi:poll", "wasi:proc", "wasi:random", "wasi:sched",
        "wasi:sock", "python:python3"]


def _emptylist():
    return []


class Runtime(models.Model):
    """Available ARENA runtimes."""

    INPUT_ATTRS = [
        "type", "name", "apis", "runtime_type", "max_nmodules", "page_size",
        "aot_target"
    ]

    uuid = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False,
        help_text="Runtime UUID.")
    name = models.CharField(
        max_length=255, default='runtime',
        help_text="Runtime short name (len <= 255).")
    updated_at = models.DateTimeField(
        auto_now=True, help_text="Last time the runtime was updated/created")
    apis = models.JSONField(
        max_length=500, blank=True, help_text="Supported APIs.",
        default=_default_apis)
    runtime_type = models.CharField(
        max_length=16, default="linux",
        help_text="Runtime type (browser, linux, embedded)")
    max_nmodules = models.IntegerField(
        default=3, help_text="Maximum number of modules (todo: replace)")
    nmodules = models.IntegerField(
        default=0, help_text="Current number of modules (todo: replace)")
    ka_interval_sec = models.IntegerField(
        default=60, help_text="Keepalive interval (seconds)")
    ka_ts = models.DateTimeField(
        auto_now_add=True, help_text="Last keepalive timestamp")
    page_size = models.IntegerField(
        default=65536, help_text=(
            "WASM pagesize. Default = 64KiB. Memory-constrained embedded "
            "runtimes can use smaller page size of 4KiB."))
    aot_target = models.CharField(
        max_length=500, default="{}", blank=True, help_text=(
            "AOT target details, including CPU architecture, target ISA "
            "and ABI."))

    @property
    def type(self):
        """Model name for serializers."""
        return "runtime"

    def save(self, *args, **kwargs):
        """Save override to check for UUID validity."""
        if not isinstance(self.uuid, uuid.UUID):
            self.uuid = uuid.uuid4()

        super().save(*args, **kwargs)

    def __str__(self):
        """Debug information."""
        return "[{}] {}:{}".format(
            self.name, self.runtime_type, str(self.uuid))


class Module(models.Model):
    """Currently running modules."""

    INPUT_ATTRS = [
        "type", "name", "filename", "filetype", "apis", "args", "env",
        "channels", "peripherals"]

    uuid = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False,
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
        max_length=16, choices=FileType.choices, default=FileType.WA,
        help_text="File type (PY, WA)")
    source = models.ForeignKey(
        'File', on_delete=models.PROTECT, blank=True, null=True,
        help_text="Source file identifier (for profile tracking)")
    wasm = models.TextField(default="", blank=True,
        help_text="WASM file contents to send to runtime")
    apis = models.JSONField(
        default=_emptylist, blank=True,
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
    runtime = models.IntegerField(
        default=100000, help_text="sched_deadline runtime (microseconds).")
    period = models.IntegerField(
        default=1000000, help_text="sched_deadline period (microseconds).")
    affinity = models.IntegerField(
        default=2, help_text="sched_deadline affinity.")

    @property
    def type(self):
        """Model name for serializers."""
        return "module"

    def __str__(self):
        """Django admin page display row."""
        return "[{}] {}:{}".format(
            self.name, self.source.name, str(self.uuid))


class File(models.Model):
    """Module source code."""

    index = models.BigAutoField(primary_key=True, help_text="File ID.")
    name = models.TextField(blank=False, help_text="Program file.")
    type = models.CharField(
        max_length=16, choices=FileType.choices, default=FileType.WA,
        help_text="Program file type.")
    # hash = models.BinaryField(help_text="File hash.")
    # Todo: add hashing infrastructure

    def __str__(self):
        """Django admin page display row."""
        return "[{}] {}:{}".format(self.index, self.type, self.name)
