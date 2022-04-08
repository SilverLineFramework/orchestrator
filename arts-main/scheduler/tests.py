from django.test import TestCase
from django.core.exceptions import ObjectDoesNotExist
from arts_core.models import Runtime, Module
from scheduler import LeastModulesFirstScheduler
from scheduler import RoundRobinScheduler
import uuid

class SchedulerTests(TestCase):

    def setUp(self):
        # 3 wasm runtimes with sequential uuids (round robin scheduler sorts by uuid)
        Runtime.objects.create(uuid=uuid.UUID('{00010203-0405-0607-0809-0a0b0c0d0e01}'), name = 'runtime1', apis =  ["wasi:unstable"], max_nmodules = 10, nmodules = 1)
        Runtime.objects.create(uuid=uuid.UUID('{00010203-0405-0607-0809-0a0b0c0d0e02}'), name = 'runtime2', apis =  ["wasi:unstable"], max_nmodules = 10, nmodules = 1)
        Runtime.objects.create(uuid=uuid.UUID('{00010203-0405-0607-0809-0a0b0c0d0e03}'), name = 'runtime3', apis =  ["wasi:unstable"], max_nmodules = 10, nmodules = 1)
        # 3 python runtimes
        Runtime.objects.create(name = 'python_runtime1', apis =  ["python:python3"], max_nmodules = 4, nmodules = 2)
        Runtime.objects.create(name = 'python_runtime2', apis =  ["python:python3"], max_nmodules = 10, nmodules = 3)
        Runtime.objects.create(name = 'python_runtime3', apis =  ["python:python3"], max_nmodules = 2, nmodules = 2)

        self.lmf_scheduler = LeastModulesFirstScheduler()
        self.rr_scheduler = RoundRobinScheduler()

    def test_least_modules_runtime(self):
        """"""
        mod = Module.objects.create(name = 'test_module', filename = "test.py", filetype = "PY", apis = ["python:python3"])

        runtime = self.lmf_scheduler.schedule_new_module(mod)
        self.assertEqual(runtime.name, 'python_runtime1')

    def test_next_runtime(self):
        """"""
        mod = Module.objects.create(name = 'test_module', filename = "test.wasm", filetype = "WA", apis = ["wasi:unstable"])

        runtime = self.rr_scheduler.schedule_new_module(mod)
        self.assertEqual(runtime.name, 'runtime1')

        runtime = self.rr_scheduler.schedule_new_module(mod)
        self.assertEqual(runtime.name, 'runtime2')

        runtime = self.rr_scheduler.schedule_new_module(mod)
        self.assertEqual(runtime.name, 'runtime3')

        runtime = self.rr_scheduler.schedule_new_module(mod)
        self.assertEqual(runtime.name, 'runtime1')
