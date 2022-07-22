# Generated by Django 4.0.6 on 2022-07-21 21:31

import api.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Runtime',
            fields=[
                ('uuid', models.CharField(default=api.models._uuidstr, editable=False, help_text='Runtime UUID.', max_length=64, primary_key=True, serialize=False)),
                ('name', models.CharField(default='runtime', help_text='Runtime short name (len <= 255).', max_length=255)),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Last time the runtime was updated/created')),
                ('apis', models.JSONField(blank=True, default=api.models._default_runtime_apis, help_text='Supported APIs.')),
                ('runtime_type', models.CharField(default='linux', help_text='Runtime type (browser, linux, embedded, special)', max_length=16)),
                ('ka_interval_sec', models.IntegerField(default=60, help_text='Keepalive interval (seconds)')),
                ('ka_ts', models.DateTimeField(auto_now_add=True, help_text='Last keepalive timestamp')),
                ('page_size', models.IntegerField(default=65536, help_text='WASM pagesize. Default = 64KiB. Memory-constrained embedded runtimes can use smaller page size of 4KiB.')),
                ('aot_target', models.CharField(blank=True, default='{}', help_text='AOT target details, including CPU architecture, target ISA and ABI, i.e. x86_64.tigerlake', max_length=500)),
                ('metadata', models.JSONField(blank=True, help_text='Optional metadata', null=True)),
                ('alive', models.BooleanField(default=True, help_text='Set to False after runtime exits.')),
            ],
        ),
        migrations.CreateModel(
            name='Module',
            fields=[
                ('uuid', models.UUIDField(default=api.models._uuidstr, editable=False, help_text='Module UUID.', primary_key=True, serialize=False)),
                ('name', models.CharField(default='module', help_text='Module short name (len < 255).', max_length=255)),
                ('filename', models.TextField(help_text='Program file (required).')),
                ('filetype', models.CharField(default='WA', help_text='File type (PY, WA, EXT)', max_length=8)),
                ('apis', models.JSONField(blank=True, default=api.models._default_required_apis, help_text='APIs required by the module.')),
                ('args', models.JSONField(blank=True, default=api.models._emptylist, help_text='Arguments to pass to the module at startup.')),
                ('env', models.JSONField(blank=True, default=api.models._emptylist, help_text='Environment path to pass to the module at startup.')),
                ('channels', models.JSONField(blank=True, default=api.models._emptylist, help_text='Channels to open at startup.')),
                ('peripherals', models.JSONField(blank=True, default=api.models._emptylist, help_text='Required peripherals.')),
                ('resources', models.JSONField(blank=True, help_text='Resource reservation (runtime/period with SCHED_DEADLINE)', null=True)),
                ('alive', models.BooleanField(default=True, help_text='Set to False after runtime exits.')),
                ('parent', models.ForeignKey(blank=True, help_text='Parent runtime (runtime where the module is running', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='api.runtime')),
            ],
        ),
    ]
