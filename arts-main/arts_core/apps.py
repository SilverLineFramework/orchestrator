from django.apps import AppConfig
import pubsub.listener as listener
from django.conf import settings
import os


class ArtsCoreConfig(AppConfig):
    name = 'arts_core'

    def ready(self):
        # check if we are running the main process; start mqtt listener
        if os.environ.get('RUN_MAIN', None) == 'true':

            # instantiate scheduler
            # could import another scheduler; e.g.: import scheduler.rr as sched
            import scheduler.lmf as sched
            self.scheduler = sched.LeastModulesFirst()

            import pubsub.pubsubctl as ctl
            # instantiate the mqtt ctl class;
            # interacts with the scheduler when a new module is requested
            # inject the scheduler into the mqtt ctl class
            self.mqtt_ctl = ctl.ARTSMQTTCtl(self.scheduler)

            # instantiate mqtt listener (routes messages to the mqtt ctl)
            self.mqtt_listener = listener.MqttListener(self.mqtt_ctl, pubsub_config=settings.PUBSUB, jwt_config=settings.PUBSUB)

            # import signal handlers
            import arts_core.signals
