"""Runtime registration."""

from django.conf import settings
from django.forms.models import model_to_dict

from orchestrator.models import State, Runtime, Module, Manager

from . import messages
from .handler_base import ControlHandler


class Registration(ControlHandler):
    """Runtime registration."""

    NAME = "reg"
    TOPIC = "proc/reg/#"

    def create_runtime(self, msg):
        """Create or resurrect runtime."""
        # Runtime UUID already exists -> resurrect
        try:
            rt_uuid = msg.get('data', 'uuid')
            runtime = Runtime.objects.get(uuid=rt_uuid)
            runtime.status = State.ALIVE
            runtime.save()

            modules = Module.objects.filter(
                parent=runtime, status=State.KILLED)
            self._log.warn("Dead runtime resurrected: {}".format(rt_uuid))
            self._log.warn("Respawning {} modules.".format(len(modules)))

            # Respawn dead modules
            for mod in modules:
                mod.status = State.ALIVE
                mod.save()

            return [
                messages.Response(
                    msg.topic, msg.get('object_id'), model_to_dict(runtime))
            ] + [
                messages.Request(
                    "/".join([settings.REALM, "proc/control", runtime.uuid]),
                    "create", {"type": "module", **model_to_dict(mod)})
                for mod in modules]

        # Doesn't exist -> create new
        except Runtime.DoesNotExist:
            runtime = self._object_from_dict(Runtime, msg.get('data'))
            try:
                mgr_uuid = msg.get('data', 'parent')
                runtime.parent = Manager.objects.get(uuid=mgr_uuid)
            except Manager.DoesNotExist:
                pass
            runtime.save()

            return messages.Response(
                msg.topic, msg.get('object_id'), model_to_dict(runtime))

    def delete_runtime(self, rtid):
        """Delete runtime."""
        runtime = self._get_object(rtid, model=Runtime)
        runtime.status = State.DEAD
        runtime.save()

        # Also mark all related modules as dead, but with respawn enabled
        killed = Module.objects.filter(parent=runtime, status=State.ALIVE)
        for mod in killed:
            mod.status = State.KILLED
            mod.save()
        if len(killed) > 0:
            self.log.warn(
                "Runtime exited, killing {} modules; may be "
                "resurrected.".format(len(killed)))

    def create_manager(self, msg):
        """Create runtime manager."""
        manager = self._object_from_dict(Manager, msg.get('data'))
        manager.save()
        return messages.Response(
            msg.topic, msg.get('object_id'), model_to_dict(manager))

    def delete_manager(self, msg):
        """Delete runtime manager."""
        manager = self._get_object(msg.get('data', 'uuid'), model=Manager)
        manager.status = State.DEAD
        manager.save()

        # Also kill the runtimes
        killed = Runtime.objects.filter(parent=manager, status=State.ALIVE)
        for rt in killed:
            self.delete_runtime(rt.uuid)
        if len(killed) > 0:
            self.log.warn(
                "Manager exited, killing {} runtimes".format(len(killed)))

    def handle(self, msg):
        """Handle registration message."""
        if msg.get('type') == 'arts_resp':
            return None

        self.log.info(msg.payload)
        match (msg.get('action'), msg.get('data', 'type')):
            case ("create", "runtime"):
                return self.create_runtime(msg)
            case ("delete", "runtime"):
                return self.delete_runtime(msg)
            case ("create", "manager"):
                return self.create_manager(msg)
            case ("delete", "manager"):
                return self.delete_manager(msg)
            case unknown:
                raise messages.InvalidArgument("action/type", unknown)
