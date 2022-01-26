# Generated by Django 3.1.14 on 2022-01-26 15:55

import arts_core.models
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='File',
            fields=[
                ('index', models.BigAutoField(help_text='File ID.', primary_key=True, serialize=False)),
                ('name', models.TextField(help_text='Program file.')),
                ('type', models.CharField(choices=[('WA', 'WASM'), ('PY', 'PYTHON')], default='WA', help_text='Program file type.', max_length=16)),
            ],
        ),
        migrations.CreateModel(
            name='Runtime',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, help_text='Runtime UUID.', primary_key=True, serialize=False)),
                ('name', models.CharField(default='runtime', help_text='Runtime short name (len <= 255).', max_length=255)),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Last time the runtime was updated/created')),
                ('apis', models.JSONField(blank=True, default=arts_core.models._default_apis, help_text='Supported APIs.', max_length=500)),
                ('runtime_type', models.CharField(default='linux', help_text='Runtime type (browser, linux, embedded)', max_length=16)),
                ('max_nmodules', models.IntegerField(default=3, help_text='Maximum number of modules (todo: replace)')),
                ('nmodules', models.IntegerField(default=0, help_text='Current number of modules (todo: replace)')),
                ('ka_interval_sec', models.IntegerField(default=60, help_text='Keepalive interval (seconds)')),
                ('ka_ts', models.DateTimeField(auto_now_add=True, help_text='Last keepalive timestamp')),
                ('page_size', models.IntegerField(default=65536, help_text='WASM pagesize. Default = 64KiB. Memory-constrained embedded runtimes can use smaller page size of 4KiB.')),
            ],
        ),
        migrations.CreateModel(
            name='Module',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, help_text='Module UUID.', primary_key=True, serialize=False)),
                ('name', models.CharField(default='module', help_text='Module short name (len < 255).', max_length=255)),
                ('filename', models.TextField(help_text='Program file (required).')),
                ('filetype', models.CharField(choices=[('WA', 'WASM'), ('PY', 'PYTHON')], default='WA', help_text='File type (PY, WA)', max_length=16)),
                ('apis', models.JSONField(blank=True, default=arts_core.models._emptylist, help_text='APIs required by the module.')),
                ('args', models.JSONField(blank=True, default=arts_core.models._emptylist, help_text='Arguments to pass to the module at startup.')),
                ('env', models.JSONField(blank=True, default=arts_core.models._emptylist, help_text='Environment path to pass to the module at startup.')),
                ('channels', models.JSONField(blank=True, default=arts_core.models._emptylist, help_text='Channels to open at startup.')),
                ('peripherals', models.JSONField(blank=True, default=arts_core.models._emptylist, help_text='Required peripherals.')),
                ('runtime', models.IntegerField(default=100000, help_text='sched_deadline runtime (microseconds).')),
                ('period', models.IntegerField(default=1000000, help_text='sched_deadline period (microseconds).')),
                ('affinity', models.IntegerField(default=2, help_text='sched_deadline affinity.')),
                ('parent', models.ForeignKey(blank=True, help_text='Parent runtime (runtime where the module is running', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='arts_core.runtime')),
                ('source', models.ForeignKey(blank=True, help_text='Source file identifier (for profile tracking)', null=True, on_delete=django.db.models.deletion.PROTECT, to='arts_core.file')),
            ],
        ),
    ]
