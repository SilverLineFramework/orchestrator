"""
 This scheduler returns the runtime with the least modules, checking if module apis match what the runtime supports
""" 
from django.core.exceptions import ObjectDoesNotExist
import scheduler.base as sb
from arts_core.models import Runtime, Module, Link

class LeastModulesFirst(sb.SchedulerBase):

    def __init__(self, mqtt_client):
        super(LeastModulesFirst, self).__init__(mqtt_client)

    next_index = 0
    
    @staticmethod        
    def on_new_runtime(runtime_instance):        
        print("New runtime: ", runtime_instance)

    @staticmethod
    def schedule_new_module(module_instance):
        """
        Returns runtime with the least modules, out of the set of runtimes with apis that match the module
        """ 
        supportedRuntimes = None      
        if (module_instance.apis):
            supportedRuntimes = Runtime.objects.filter(apis__contains=module_instance.apis) # TODO: check each api individually
        else: 
            supportedRuntimes = Runtime.objects.all()
        
        if (supportedRuntimes.count() == 0):
            raise Exception('No suitable runtime!')
        
        #for r in supportedRuntimes:
        #    print(r)

        leastModulesRuntime = supportedRuntimes.order_by('nmodules')[0]
            
        return leastModulesRuntime

    @staticmethod        
    def on_new_link(sender, **kwargs):
        print("Saved: ", str(kwargs))
        
    