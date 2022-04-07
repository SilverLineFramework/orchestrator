"""
 This scheduler returns the runtime with the least modules, checking if module apis match what the runtime supports
"""
from django.core.exceptions import ObjectDoesNotExist
import scheduler.base as sb
from arts_core.models import Runtime, Module

class LeastModulesFirst(sb.SchedulerBase):

    def __init__(self):
        super(LeastModulesFirst, self).__init__('LeastModulesFirst')

    @staticmethod
    def on_new_runtime(runtime_instance):
        print("New runtime: ", runtime_instance)

    @staticmethod
    def schedule_new_module(module_instance):
        """
        Returns runtime with the least modules, out of the set of runtimes with apis that match the module
        """

        apis = ''
        if (module_instance.apis):
            #supportedRuntimes=Runtime.objects.none()
            supported_runtime_uuids = []
            apis = module_instance.apis
            for r in Runtime.objects.all():
                include = True
                for api in module_instance.apis:
                    print(api, 'in?', r.apis, api in r.apis)
                    if (not api in r.apis):
                        include = False
                        break
                if (include):
                    supported_runtime_uuids.append(r.uuid)
            supported_runtimes = Runtime.objects.filter(uuid__in=supported_runtime_uuids)
        else:
            supported_runtimes = Runtime.objects.all()

        for r in supported_runtimes:
            print(apis, 'in runtime', r, r.apis)

        if (supported_runtimes.count() == 0):
            raise Exception('No suitable runtime!')

        leastModulesRuntime = supported_runtimes.order_by('nmodules')[0]

        return leastModulesRuntime

    @staticmethod
    def on_new_link(sender, **kwargs):
        print("Saved: ", str(kwargs))
