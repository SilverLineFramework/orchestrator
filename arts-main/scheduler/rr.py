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
    def schedule_new_module():
        """
        Returns the next runtime, ordered by updated date
        everytime a new module is scheduled
        """
        next_runtime = None
        try:
            next_runtime = Runtime.objects.order_by('uuid')[RoundRobinScheduler.next_index]
            RoundRobinScheduler.next_index = RoundRobinScheduler.next_index + 1
        except Exception:
            RoundRobinScheduler.next_index = 0
            next_runtime = Runtime.objects.order_by('uuid')[RoundRobinScheduler.next_index]
            RoundRobinScheduler.next_index = RoundRobinScheduler.next_index + 1
        #print('next:',next_runtime)
        return next_runtime

    @staticmethod
    def on_new_link(sender, **kwargs):
        print("Saved: ", str(kwargs))
