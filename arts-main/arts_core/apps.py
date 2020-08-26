from django.apps import AppConfig
import pubsub.listner as listner
import os


class ArtsCoreConfig(AppConfig):
    name = 'arts_core'
    
    def ready(self):
        # check if we are running the main process; start mqtt listner 
        if os.environ.get('RUN_MAIN', None) == 'true':
            
            import pubsub.pubsubctl as ctl
            # instanciate the mqtt ctl class; interacts with the scheduler
            self.mqtt_ctl = ctl.ARTSMQTTCtl()
                    
            # instanciate mqtt listner (routes messages to the mqtt ctl)
            self.mqtt_listner = listner.MqttListner(self.mqtt_ctl)            

            # instanciate scheduler            
            #import scheduler.rr as sched
            import scheduler.lmf as sched
            self.scheduler = sched.LeastModulesFirst(self.mqtt_listner)

            # tell the mqtt ctl class about the scheduler; 
            # it interacts with the scheduler when a new module is requested
            self.mqtt_ctl.set_scheduler(self.scheduler)

            # import signal handlers 
            import arts_core.signals

