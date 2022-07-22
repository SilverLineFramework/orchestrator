from django.apps import AppConfig
from django.conf import settings
import os


class apiConfig(AppConfig):
    """Config containing core logic."""

    name = 'api'

    def ready(self):
        """Initialize MQTT handler."""
        # check if we are running the main process; start mqtt listener
        if os.environ.get('RUN_MAIN', None) == 'true':

            from pubsub import MQTTListener
            from handlers import message_handlers

            # instantiate mqtt listener (routes messages to the mqtt ctl)
            self.mqtt_listener = MQTTListener(
                message_handlers(), jwt_config=settings.JWT_AUTH)
