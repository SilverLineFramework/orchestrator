"""Orchestrator REST API.

Modules and runtimes can be specified (lookup) in 3 ways, with the following
priority:

1. Specify by full UUID in standard encoding. Dead modules and runtimes
   can be retrieved when referenced by UUID; their responses will specify
   ``{"status": "D"}`` (dead) instead of ``"A"`` (alive).
2. Specify by short name. If multiple matches are found (i.e. multiple modules
   with the same name), the first one found is returned.
3. Specify by last ``n`` hex digits (characters) of UUID; searches for
   ``uuid__endswith=query``.
"""

import uuid
from django.forms.models import model_to_dict
from django.http import JsonResponse
from django.http import HttpResponseNotFound

from .models import State, Runtime, Module


def _serialize(model):
    return [
        {k: model_to_dict(obj)[k] for k in model.OUTPUT_SHORT}
        for obj in model.objects.filter(status=State.ALIVE)]


def list_runtimes(request):
    """List all runtimes; returns only some fields.

    URL pattern::

        <server>/api/runtimes/

    Example
    -------
    ::

        {
            count: 1,
            start: 0,
            "results": [
                {
                    "uuid": "02d1991b-6951-4137-8b54-312998ffeb4c",
                    "name": "test",
                    "runtime_type": "linux",
                    "aot_target": "x86_64.tigerlake",
                    "children": [
                        {
                            "uuid": "413f3dc8-49d8-47d7-810d-9a3ac0d1720c",
                            "name": "module",
                            "filename": "wasm/polybench/2mm_s.wasm"
                        }
                    ]
                }
            ]
        }

    """
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

    rt_list = list(runtimes.values())
    return JsonResponse(
        {"count": len(rt_list), "start": 0, "results": rt_list})


def list_modules(request):
    """List all modules; returns only some fields.

    URL Pattern::

        <server>/api/modules/

    Example
    -------
    ::

        {
            count: 1,
            start: 0,
            "modules": [
                {
                    "uuid": "54c0d836-a23f-4ef7-8c64-4b6f5082b7a7",
                    "name": "module",
                    "parent": "43a664a6-5c99-4b08-9d00-eeabc0d1f7f7",
                    "filename": "wasm/polybench/2mm_s.wasm"
                }
            ]
        }

    """
    mod_list = _serialize(Module)
    return JsonResponse(
        {"count": len(mod_list), "start": 0, "results": mod_list})


def _lookup(model, query):
    """Lookup runtime / module."""
    # 1) Specify by UUID (allows dead objects for fetching historical data)
    try:
        return model_to_dict(model.objects.get(uuid=uuid.UUID(query)))
    except (ValueError, model.DoesNotExist):
        pass
    # 2) Specify by name
    try:
        return model_to_dict(
            model.objects.filter(name=query, status=State.ALIVE)[0])
    except IndexError:
        pass
    # 3) Specify by last N digits of UUID; throw exception if fails
    return model_to_dict(
        model.objects.filter(uuid__endswith=query, status=State.ALIVE)[0])


def search_runtime(request, query):
    """Retrieve runtime details.

    URL Pattern::

        <server>/api/runtimes/<uuid>/

    NOTE: returns 404 if no runtime is found.

    Example
    -------
    ::

        {
            "uuid": "02d1991b-6951-4137-8b54-312998ffeb4c",
            "name": "test",
            "apis": ["wasm", "wasi"],
            "runtime_type": "linux",
            "ka_interval_sec": 60,
            "max_nmodules": 128,
            "metadata": null,
            "platform": {
                "cpu": {
                    "arch": "X86_64",
                    "cores": 8,
                    "class": "tigerlake",
                    "qos": {"rt": 0, "cfs": 0},
                    "cpufreq": 3368621
                },
                "mem": {
                    "l1i_size": 131072,
                    "l1d_size": 196608,
                    "l2_size": 5242880,
                    "l2_line": 256,
                    "l2_assoc": 7,
                    "l3_size": 12582912,
                    "total": 8154243072
                }
            },
            "status": "A",
            "children": [
                {
                    "uuid": "413f3dc8-49d8-47d7-810d-9a3ac0d1720c",
                    "name": "module",
                    "filename": "wasm/polybench/2mm_s.wasm"
                }
            ]
        }
    """
    try:
        runtime = _lookup(Runtime, query)
    except IndexError:
        return HttpResponseNotFound()

    runtime['children'] = [
        model_to_dict(module) for module in
        Module.objects.filter(parent=runtime['uuid'], status=State.ALIVE)]

    return JsonResponse(runtime)


def search_module(request, query):
    """Retrieve module details.

    URL Pattern::

        <server>/api/modules/<uuid>/

    NOTE: returns 404 if no matching module is found.

    Example
    -------
    ::

        {
            "uuid": "413f3dc8-49d8-47d7-810d-9a3ac0d1720c",
            "name": "module",
            "parent": "02d1991b-6951-4137-8b54-312998ffeb4c",
            "filename": "wasm/polybench/2mm_s.wasm",
            "filetype": "WA",
            "apis": ["wasm", "wasi"],
            "args": ["wasm/polybench/2mm_s.wasm"],
            "env": [],
            "channels": [],
            "peripherals": [],
            "resources": null,
            "fault_crash": "ignore",
            "status": "A"
        }

    """
    try:
        return JsonResponse(_lookup(Module, query))
    except IndexError:
        return HttpResponseNotFound()
