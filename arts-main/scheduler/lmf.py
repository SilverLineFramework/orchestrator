"""
 This scheduler returns the runtime with the least modules, checking if module apis match what the runtime supports
"""
from django.core.exceptions import ObjectDoesNotExist
import scheduler.base as sb
from arts_core.models import Runtime, Module

class LeastModulesFirstScheduler(sb.SchedulerBase):

    def __init__(self):
        super(LeastModulesFirstScheduler, self).__init__('LeastModulesFirstScheduler')

    @staticmethod
    def on_new_runtime(runtime_instance):
        print("New runtime: ", runtime_instance)

    @staticmethod
    def schedule_new_module(module_instance):
        """
        Returns runtime with the least modules
        Performs basic checks (nmodules and apis) if the runtime can run the module
        """

        supported_runtime_uuids = []
        for r in Runtime.objects.all():
            # try next one, if this runtime cannot run more modules
            if r.max_nmodules-r.nmodules <= 0: continue
            include = True
            # check if apis needed by module are supported
            if (module_instance.apis):
                for api in module_instance.apis:
                    #print(api, 'in?', r.apis, api in r.apis)
                    if (not api in r.apis):
                        include = False
                        break
            if (include):
                supported_runtime_uuids.append(r.uuid)

        supported_runtimes = Runtime.objects.filter(uuid__in=supported_runtime_uuids)

        #for r in supported_runtimes:
        #    print(apis, 'in runtime', r, r.apis)

        if (supported_runtimes.count() == 0):
            raise Exception('No suitable runtime!')

        least_modules_runtime = supported_runtimes.order_by('nmodules')[0]

        return least_modules_runtime

    @staticmethod
    def on_new_link(sender, **kwargs):
        print("Saved: ", str(kwargs))
