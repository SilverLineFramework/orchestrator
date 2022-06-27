"""Object serialization."""

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Runtime, Module


class ModuleListingField(serializers.RelatedField):
    """Module nested representation; omits most fields."""

    def to_representation(self, value):
        return {
            'type': value.type,
            'parent': {'uuid': str(value.parent.uuid)},
            'name': value.name,
            'uuid': str(value.uuid),
            'filename': value.filename
        }


class RuntimeSerializer(serializers.ModelSerializer):
    """Runtime full serialization."""

    children = ModuleListingField(many=True, read_only=True)

    class Meta:
        model = Runtime
        fields = (
            "type", "uuid", "name", "apis", "runtime_type",
            "ka_interval_sec", "children", "aot_target", "platform")


class ParentListingField(serializers.RelatedField):
    def to_representation(self, value):
        return {'uuid': str(value.uuid)}


class ModuleSerializer(serializers.ModelSerializer):
    """Module standalone serialization."""
    parent = ParentListingField(many=False, read_only=True)

    class Meta:
        model = Module
        fields = (
            "type", "uuid", "name", "parent", "filename", "filetype", "wasm",
            "apis", "args", "env", "channels", "peripherals", "resources")


class TokenSerializer(serializers.Serializer):
    """JWT Serialization."""

    token = serializers.CharField(max_length=255)


class UserSerializer(serializers.ModelSerializer):
    """User Serialization."""

    class Meta:
        model = User
        fields = ("username", "email")
