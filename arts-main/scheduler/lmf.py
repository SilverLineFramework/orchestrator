"""
 This scheduler returns the runtime with the least modules, checking if module apis match what the runtime supports
"""
from django.core.exceptions import ObjectDoesNotExist
import scheduler.base as sb
from arts_core.models import Runtime, Module

class LeastModulesFirst(sb.SchedulerBase):

    def __init__(self):
        super(LeastModulesFirst, self).__init__('LeastModulesFirst')

    next_index = 0

    @staticmethod
    def on_new_runtime(runtime_instance):
        print("New runtime: ", runtime_instance)

    @staticmethod
    def schedule_new_module(module_instance):
        """
        Returns runtime with the least modules, out of the set of runtimes with apis that match the module
        """
        supportedRuntimes = Runtime.objects.all()
        for r in supportedRuntimes:
            print(r)

        if (module_instance.apis):
            for api in module_instance.apis:
                print(api)
                supportedRuntimes = supportedRuntimes.filter(apis__contains=api)

        if (supportedRuntimes.count() == 0):
            raise Exception('No suitable runtime!')

        #for r in supportedRuntimes:
        #    print(r)

        leastModulesRuntime = supportedRuntimes.order_by('nmodules')[0]

        return leastModulesRuntime

    @staticmethod
    def on_new_link(sender, **kwargs):
        print("Saved: ", str(kwargs))
