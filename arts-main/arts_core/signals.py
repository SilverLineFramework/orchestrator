"""
*TL;DR
Routes app signals from; Place to write all app's signal receivers
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.apps import apps
from .models import Runtime, Module, Link

##########
#TODO: make adding modules using rest also create modules at remote runtimes (pass part of the logic in pubsub.views to the module signal handlers)
#########

@receiver(post_save, sender=Runtime)
def post_save_runtime(sender, instance, created, **kwargs):
    # forward the signal to the scheduler
    if created:
        apps.get_app_config('arts_core').scheduler.on_new_runtime(instance)

@receiver(post_save, sender=Module)
def post_save_module(sender, instance, created, **kwargs):
    # increase number of modules in the runtime
    try:
        instance.parent.nmodules += 1
        instance.parent.save(update_fields=['nmodules'])
    except Exception as err:
        print("Error increasing nmodules", err)
        
@receiver(post_delete, sender=Module)
def post_delete_module(sender, instance, **kwargs):
    # decrease number of modules in the runtime
    try:
        instance.parent.nmodules -= 1
        instance.parent.save(update_fields=['nmodules'])
    except Exception as err:
        print("Error decreasing nmodules", err)
