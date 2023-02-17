"""Entry point for the orchestrator main logic."""

from django.apps import AppConfig
from django.conf import settings
import os
from libsilverline import MQTTServer


class orchestratorConfig(AppConfig):
    """Config containing core logic."""

    name = 'orchestrator'

    def ready(self):
        """Initialize MQTT handler."""
        if os.environ.get('RUN_MAIN', None) == 'true':
            from pubsub import Orchestrator

            self.orch = Orchestrator(
                name="orchestrator",
                server=MQTTServer.from_config(settings.CONFIG_PATH)).start()
