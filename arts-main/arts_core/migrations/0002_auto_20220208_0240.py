# Generated by Django 3.1.14 on 2022-02-08 02:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('arts_core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='module',
            name='wasm',
            field=models.TextField(blank=True, default='', help_text='WASM file contents to send to runtime'),
        ),
        migrations.AddField(
            model_name='runtime',
            name='aot_target',
            field=models.CharField(blank=True, default='{}', help_text='AOT target details, including CPU architecture, target ISA and ABI.', max_length=500),
        ),
    ]
