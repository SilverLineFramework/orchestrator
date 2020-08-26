
class SchedulerBase():
    mqtt_client = None
    
    def __init__(self, mqtt_client):
        SchedulerBase.mqtt_client = mqtt_client
        
    # New runtime notification handler; Some schedulers might need want to know when a new runtime appears
    @staticmethod
    def on_new_runtime(runtime_instance):
        raise NotImplementedError        

    # Called when we need to schedule a new runtime; Returns the runtime (parent) where the module it to be executed
    @staticmethod
    def schedule_new_module(module_instance=None):
        raise NotImplementedError        
