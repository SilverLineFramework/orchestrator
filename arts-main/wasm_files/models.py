from django.db import models
from django.conf import settings
import uuid
import os

from . import file_handler 

class WASMFiles(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)    
    description = models.CharField(max_length=255, blank=True)
    wasm_file = models.FileField(upload_to=file_handler.get_file_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)
