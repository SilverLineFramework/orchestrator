from django.apps import AppConfig
import pubsub.listener as listener
from django.conf import settings 
import os


class ArtsCoreConfig(AppConfig):
    name = 'arts_core'

    def ready(self):
       
        # check if we are running the main process; start mqtt listener
        if os.environ.get('RUN_MAIN', None) == 'true':

            import pubsub.pubsubctl as ctl
            # instantiate the mqtt ctl class; interacts with the scheduler
            self.mqtt_ctl = ctl.ARTSMQTTCtl()

            # instantiate mqtt listener (routes messages to the mqtt ctl)
            self.mqtt_listener = listener.MqttListener(self.mqtt_ctl, pubsub_config=settings.PUBSUB, jwt_config=settings.PUBSUB)

            # instantiate scheduler
            #import scheduler.rr as sched
            import scheduler.lmf as sched
            self.scheduler = sched.LeastModulesFirst(self.mqtt_listener)

            # tell the mqtt ctl class about the scheduler;
            # it interacts with the scheduler when a new module is requested
            self.mqtt_ctl.set_scheduler(self.scheduler)

            # import signal handlers
            import arts_core.signals
