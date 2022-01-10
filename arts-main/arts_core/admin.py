from django.contrib import admin
from .models import Runtime, Module, File

admin.site.register(Runtime)
admin.site.register(Module)
admin.site.register(File)
