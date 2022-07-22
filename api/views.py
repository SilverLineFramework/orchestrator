"""Orchestrator REST API."""

import uuid
from django.core import serializers
from django.http import JsonResponse

from .models import Runtime, Module


def list_runtimes(request):
    """List all runtimes; returns only some fields."""
    return JsonResponse(serializers.serialize(
        'json', Runtime.objects.all(), fields=Runtime.OUTPUT_ATTRS))


def list_modules(request):
    """List all modules; returns only some fields."""
    return JsonResponse(serializers.serialize(
        'json', Module.objects.all(), fields=Module.OUTPUT_ATTRS))


def _lookup(model, query):
    """Lookup runtime / module."""
    # 1) Specify by UUID (allows dead objects for fetching historical data)
    try:
        return model.objects.get(uuid=uuid.UUID(query))
    except (ValueError, model.DoesNotExist):
        pass
    # 2) Specify by name
    try:
        return model.objects.filter(name=query, alive=True)[0]
    except IndexError:
        pass
    # 3) Specify by last N digits of UUID
    try:
        return model.objects.filter(uuid__endswith=query, alive=True)[0]
    except IndexError:
        # Not found
        return {}


def search_runtime(request, query):
    """Search for runtime."""
    return JsonResponse(serializers.serialize('json', _lookup(Runtime, query)))


def search_module(request, query):
    """Search for module."""
    return JsonResponse(serializers.serialize('json', _lookup(Module, query)))
