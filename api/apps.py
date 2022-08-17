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
            from handlers import Registration, Control, Keepalive

            # instantiate mqtt listener (routes messages to the mqtt ctl)
            self.mqtt_listener = MQTTListener(
                cid="orchestrator",
                mqtt=settings.MQTT_HOST, mqtt_port=settings.MQTT_PORT,
                realm=settings.REALM, pwd=settings.MQTT_PASSWORD_FILE,
                mqtt_username=settings.MQTT_USERNAME,
                use_ssl=settings.MQTT_SSL, connect=True)

            for handler in [Registration(), Control(), Keepalive()]:
                self.mqtt_listener.register_callback(
                    handler.topic, self.mqtt_listener.handle_message(handler))
