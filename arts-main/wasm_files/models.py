from django.db import models
import uuid

from . import file_handler 

class WASMFiles(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)    
    description = models.CharField(max_length=255, blank=True)
    wasm_file = models.FileField(upload_to=file_handler.get_file_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)
