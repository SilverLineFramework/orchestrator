from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Runtime, Module, Link
import json

class ModuleListingField(serializers.RelatedField):
    def to_representation(self, value):
        return { 'type': value.type, 'parent': { 'uuid': str(value.parent.uuid) }, 'name': value.name, 'uuid': str(value.uuid), 'filename': value.filename}

class RuntimeSerializer(serializers.ModelSerializer):
    """
    Serializes the runtime data
    """
    children = ModuleListingField(many=True, read_only=True)
    
    class Meta:
        model = Runtime
        fields = ("type", "uuid", "name", "apis", "max_nmodules", "nmodules", "children")

class ParentListingField(serializers.RelatedField):
    def to_representation(self, value):
        return {'uuid': str(value.uuid)}
    
class ModuleSerializer(serializers.ModelSerializer):
    """
    Serializes the module data
    """
    # parent = serializers.SlugRelatedField(
    #     many=False,
    #     read_only=True,
    #     slug_field='uuid'
    # )
    parent = ParentListingField(many=False, read_only=True)
    
    class Meta:
        model = Module
        fields = ("type", "uuid", "name", "parent", "filename", "fileid", "filetype", "args", "channels")
        
class LinkSerializer(serializers.ModelSerializer):
    """
    Serializes the link data
    """
    link_from = serializers.StringRelatedField(many=False)
    link_to = serializers.StringRelatedField(many=False)
    
    class Meta:
        model = Link
        fields = ("uuid", "link_from", "link_to")
        
class TokenSerializer(serializers.Serializer):
    """
    This serializer serializes the token data
    """
    token = serializers.CharField(max_length=255)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("username", "email")        