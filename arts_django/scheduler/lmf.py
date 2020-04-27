from django.core.exceptions import ObjectDoesNotExist
import scheduler.base as sb
from arts_core.models import Runtime, Module, Link

class RoundRobinScheduler(sb.SchedulerBase):

    def __init__(self, mqtt_client):
        super(RoundRobinScheduler, self).__init__(mqtt_client)

    next_index = 0
    
    @staticmethod        
    def on_new_runtime(runtime_instance):        
        print("New runtime: ", runtime_instance)

    @staticmethod
    def schedule_new_module():
        """
        Return the runtime (parent) where the module it to be executed
        This scheduler returns the runtime with the least modules
        """        
        lm_runtime = Runtime.objects.order_by('nmodules')[0]
        return lm_runtime

    @staticmethod        
    def on_new_link(sender, **kwargs):
        print("Saved: ", str(kwargs))
        
    