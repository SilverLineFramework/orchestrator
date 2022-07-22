"""Orchestrator REST API."""

import uuid
from django.db import models
from django.forms.models import model_to_dict
from django.http import JsonResponse

from .models import Runtime, Module


def _serialize(model):
    return [
        {k: model_to_dict(obj)[k] for k in model.OUTPUT_SHORT}
        for obj in model.objects.filter(alive=True)]


def list_runtimes(request):
    """List all runtimes; returns only some fields."""
    runtimes = {rt["uuid"]: rt for rt in _serialize(Runtime)}
    for _, rt in runtimes.items():
        rt["children"] = []

    modules = _serialize(Module)
    for mod in modules:
        try:
            runtimes[mod["parent"]]["children"].append(mod)
            del mod["parent"]
        except KeyError:
            pass

    return JsonResponse({"runtimes": list(runtimes.values())})


def list_modules(request):
    """List all modules; returns only some fields."""
    return JsonResponse({"modules": _serialize(Module)})


def _lookup(model, query):
    """Lookup runtime / module."""
    # 1) Specify by UUID (allows dead objects for fetching historical data)
    try:
        return model_to_dict(model.objects.get(uuid=uuid.UUID(query)))
    except (ValueError, model.DoesNotExist):
        pass
    # 2) Specify by name
    try:
        return model_to_dict(model.objects.filter(name=query, alive=True)[0])
    except IndexError:
        pass
    # 3) Specify by last N digits of UUID
    try:
        return model_to_dict(
            model.objects.filter(uuid__endswith=query, alive=True)[0])
    except IndexError:
        # Not found
        return {}


def search_runtime(request, query):
    """Search for runtime."""
    return JsonResponse(_lookup(Runtime, query))


def search_module(request, query):
    """Search for module."""
    return JsonResponse(_lookup(Module, query))
