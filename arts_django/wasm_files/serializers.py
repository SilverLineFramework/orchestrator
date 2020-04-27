from rest_framework import serializers
from .models import WASMFiles

class FilesSerializer(serializers.ModelSerializer):
    """
    Serializes the files data
    """
    
    class Meta:
        model = WASMFiles
        fields = ("uuid", "description")