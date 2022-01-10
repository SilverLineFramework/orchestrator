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
            from profile import Collector

            # instantiate scheduler
            from scheduler import LeastModulesFirst
            scheduler = LeastModulesFirst()
            profiler = Collector(dir=settings.DATA_DIR)

            # instantiate mqtt listener (routes messages to the mqtt ctl)
            self.mqtt_listener = MQTTListener(
                ARTSHandler(scheduler, profiler), jwt_config=settings.JWT_AUTH)
