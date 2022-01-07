from django.apps import AppConfig
from django.conf import settings
import os

class ArtsCoreConfig(AppConfig):
    """Config containing ARTS core logic."""

    name = 'arts_core'

    def ready(self):
        """Initialize MQTT handler."""
        # check if we are running the main process; start mqtt listener
        if os.environ.get('RUN_MAIN', None) == 'true':

            from pubsub import MQTTListener, ARTSHandler
            from profile import ProfileCollector

            # instantiate scheduler
            import scheduler.lmf as sched
            scheduler = sched.LeastModulesFirst()
            profiler = ProfileCollector(dir=settings.DATA_DIR)

            # instantiate mqtt listener (routes messages to the mqtt ctl)
            self.mqtt_listener = MQTTListener(
                ARTSHandler(scheduler, profiler),
                pubsub_config=settings.PUBSUB, jwt_config=settings.PUBSUB)
