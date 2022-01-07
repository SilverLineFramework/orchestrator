"""Core Models."""

from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid
import json


class FileType(models.TextChoices):
    """File type enum."""

    WA = 'WA', _('WASM')
    PY = 'PY', _('PYTHON')


class Runtime(models.Model):
    """Available ARENA runtimes."""

    INPUT_KEYS = [
        "uuid", "name", "apis", "runtime_type", "max_nmodules",
        "ka_interval_sec", "page_size"]

    uuid = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False,
        help_text="Runtime UUID.")
    name = models.CharField(
        max_length=255, default='runtime',
        help_text="Runtime short name (len <= 255).")
    updated_at = models.DateTimeField(
        auto_now=True, help_text="Last time the runtime was updated/created")
    apis = models.CharField(
        max_length=500, blank=True, help_text="Supported APIs.",
        default=(
            "wasi:snapshot_preview1 wasi:unstable wasi:core wasi:clock "
            "wasi:environ wasi:sock wasi:args wasi:fd wasi:path wasi:poll "
            "wasi:proc wasi:random wasi:sched wasi:sock python:python3"))
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

    @property
    def type(self):
        return "runtime"

    def save(self, *args, **kwargs):
        """Save override to check for UUID validity."""
        if not isinstance(self.uuid, uuid.UUID):
            self.uuid = uuid.uuid4()

        super(Runtime, self).save(*args, **kwargs)

    def __str__(self):
        """Debug information."""
        return str({
            'type': self.type, 'uuid': str(self.uuid), 'name': self.name,
            'apis': str(self.apis), 'max_nmodules': self.max_nmodules,
            'nmodules': self.nmodules, 'ka_ts': str(self.ka_ts)
        })


class Module(models.Model):
    """Currently running modules."""

    INPUT_KEYS = [
        "uuid", "name", "filename", "fileid", "filetype", "apis", "args",
        "env", "channels", "peripherals"]

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
    filename = models.CharField(
        max_length=255, blank=False, help_text="Program file (required).")
    fileid = models.CharField(
        max_length=255, blank=False, help_text="File ID (required).")
    filetype = models.CharField(
        max_length=16, choices=FileType.choices, default=FileType.WA,
        help_text="File type (PY, WA)")
    apis = models.TextField(
        default='["wasi:snapshot_preview1"]', blank=True,
        help_text="APIs required by the module.")
    args = models.TextField(
        default='[]', blank=True,
        help_text="Arguments to pass to the module at startup.")
    env = models.TextField(
        default='[]', blank=True,
        help_text="Environment path to pass to the module at startup.")
    channels = models.TextField(
        default='[]', blank=True, help_text="Channels to open at startup.")
    peripherals = models.TextField(
        default='[]', blank=True, help_text="Required peripherals.")

    @property
    def type(self):
        return "module"

    def __str__(self):
        """Debug information."""
        return str({
            'type': self.type, 'uuid': str(self.uuid), 'name': self.name,
            'parent': self.parent, 'filename': self.filename,
            'apis': self.apis, 'fileid': self.fileid,
            'filetype': self.filetype, 'args': self.args, 'env': self.env,
            'channels': self.channels
        })
