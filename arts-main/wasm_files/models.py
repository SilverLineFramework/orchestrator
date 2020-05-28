from django.db import models
import uuid
import os

def get_file_path(instance, filename):
    n_filename = "%s_%s" % (uuid.uuid4(), filename)
    return os.path.join('wasm_files/uploads', n_filename)

class WASMFiles(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)    
    description = models.CharField(max_length=255, blank=True)
    wasm_file = models.FileField(upload_to=get_file_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)