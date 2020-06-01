# Generated by Django 3.0.3 on 2020-02-13 16:35

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('wasm_files', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='wasmfiles',
            name='id',
        ),
        migrations.AddField(
            model_name='wasmfiles',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
        ),
    ]