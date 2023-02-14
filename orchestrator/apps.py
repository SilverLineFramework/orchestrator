"""Entry point for the orchestrator main logic."""

from django.apps import AppConfig
from django.conf import settings
import os


class orchestratorConfig(AppConfig):
    """Config containing core logic."""

    name = 'orchestrator'

    def ready(self):
        """Initialize MQTT handler."""
        if os.environ.get('RUN_MAIN', None) == 'true':
            from pubsub import Orchestrator, MQTTServer

            self.orch = Orchestrator(name="orchestrator")
            self.orch.start(server=MQTTServer.from_json(settings.CONFIG_PATH))
