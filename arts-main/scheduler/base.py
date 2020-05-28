
class SchedulerBase():
    mqtt_client = None
    
    def __init__(self, mqtt_client):
        SchedulerBase.mqtt_client = mqtt_client
        
    @staticmethod
    def on_new_runtime(runtime_instance):
        raise NotImplementedError        

    @staticmethod
    def schedule_new_module():
        raise NotImplementedError        
