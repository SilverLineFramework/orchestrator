from django.apps import AppConfig
import pubsub.listener as listener
from django.conf import settings
import os

from pubsub import MQTTListener, ARTSHandler


class ArtsCoreConfig(AppConfig):
    """Config containing ARTS core logic."""

    name = 'arts_core'

    def ready(self):
        """Initialize MQTT handler."""
        # check if we are running the main process; start mqtt listener
        if os.environ.get('RUN_MAIN', None) == 'true':

            # instantiate scheduler
            import scheduler.lmf as sched
            scheduler = sched.LeastModulesFirst()

            # instantiate mqtt listener (routes messages to the mqtt ctl)
            self.mqtt_listener = MQTTListener(
                ARTSHandler(scheduler),
                pubsub_config=settings.PUBSUB, jwt_config=settings.PUBSUB)
