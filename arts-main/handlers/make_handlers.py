"""Handler entry point."""

from re import M
from scheduler import LeastModulesFirstScheduler
from profile import Collector
from django.conf import settings

from .registration import Registration
from .control import Control
from .profile import Profile, CPUFreq
from .misc import Keepalive, Debug, Special


def message_handlers():
    """Create message handlers."""
    scheduler = LeastModulesFirstScheduler()
    profiler = Collector(dir=settings.DATA_DIR)

    callbacks = {
        "create_runtime": [profiler.create_runtime],
        "create_module": [profiler.create_module],
        "delete_module": [profiler.delete_module],
        "exited_module": [profiler.delete_module],
        "save": [profiler.save],
        "reset": [profiler.reset],
        "profile": [profiler.update],
        "cpufreq": [profiler.update_cpufreq]
    }

    return {
        "reg": Registration(callbacks),
        "control": Control(scheduler, callbacks),
        "keepalive": Keepalive(callbacks),
        "debug": Debug(callbacks),
        "special": Special(callbacks),
        "profile": Profile(callbacks),
        "cpufreq": CPUFreq(callbacks)
    }
