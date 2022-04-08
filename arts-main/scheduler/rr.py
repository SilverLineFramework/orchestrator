"""
 This is a very simple round-robin scheduler example
"""
from django.core.exceptions import ObjectDoesNotExist
import scheduler.base as sb
from arts_core.models import Runtime, Module

class RoundRobinScheduler(sb.SchedulerBase):

    def __init__(self):
        super(RoundRobinScheduler, self).__init__('RoundRobinScheduler')

    next_index = 0

    @staticmethod
    def on_new_runtime(runtime_instance):
        print("New runtime: ", runtime_instance)

    @staticmethod
    def schedule_new_module(module_instance):
        """
        Returns the next runtime, ordered by uuid
        Performs basic checks (nmodules and apis) if the runtime can run the module
        """
        next_runtime = None
        start_index = RoundRobinScheduler.next_index
        while next_runtime == None:
            try:
                next_runtime = Runtime.objects.order_by('uuid')[RoundRobinScheduler.next_index]
                RoundRobinScheduler.next_index = RoundRobinScheduler.next_index + 1
            except Exception:
                RoundRobinScheduler.next_index = 0
                next_runtime = Runtime.objects.order_by('uuid')[RoundRobinScheduler.next_index]
                RoundRobinScheduler.next_index = RoundRobinScheduler.next_index + 1
            # next_runtime is our candidate runtime to run the module
            if next_runtime:
                # next_runtime can have more modules ?
                if next_runtime.max_nmodules-next_runtime.nmodules > 0:
                    # next_runtime supports apis needed by module ?
                    for api in module_instance.apis:
                        #print(api, 'in?', r.apis, api in r.apis)
                        if (not api in next_runtime.apis):
                            next_runtime = None
                            break
                else: next_runtime = None
            # did we just try all runtimes ?
            if start_index == RoundRobinScheduler.next_index:
                next_runtime = None
                break;

        if (next_runtime == None):
            raise Exception('No suitable runtime!')

        return next_runtime

    @staticmethod
    def on_new_link(sender, **kwargs):
        print("Saved: ", str(kwargs))
