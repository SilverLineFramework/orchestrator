from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid
import json

class FileType(models.TextChoices):   
    WA = 'WA', _('WASM')
    PY = 'PY', _('PYTHON')

    
class Runtime(models.Model):
    # runtime uuid
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # name of the runtime
    name = models.CharField(max_length=255, default='aruntime')
    # last time the runtime was updated/created
    updated_at = models.DateTimeField(auto_now=True)
    # supported APIs
    apis = models.CharField(max_length=500, default=["wasi:snapshot_preview1", "wasi:unstable", "wasi:core", "wasi:clock", "wasi:environ", "wasi:sock", "wasi:args", "wasi:fd", "wasi:path", "wasi:poll", "wasi:proc", "wasi:random", "wasi:sched", "wasi:sock", "python:core"], blank=True)
    # max number of modules
    max_nmodules = models.IntegerField(default=3)
    # current number of modules
    nmodules = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        if (isinstance(self.uuid, uuid.UUID) == False):
            self.uuid = uuid.uuid4()
            
        super(Runtime, self).save(*args, **kwargs)
    
    def __str__(self):
        return str({'uuid':str(self.uuid), 'name': self.name, 'apis': str(self.apis), 'max_nmodules': self.max_nmodules, 'nmodules': self.nmodules})

class Module(models.Model):
    # module uuid
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # name of the module
    name = models.CharField(max_length=255, default='amodule')
    # parent runtime (runtime where the module is installed/running)
    parent = models.ForeignKey('Runtime', on_delete=models.CASCADE, related_name='children', blank=False, null=False)
    # program file (can be a zip with several files; runtime will unzip and to execute filename.[py|wasm] according to the filetype)
    filename = models.CharField(max_length=255, blank=False, default='afile.wasm')
    # file id
    fileid = models.CharField(max_length=255, blank=False, default='afileid')
    #filetype
    filetype = models.CharField(max_length=10, choices=FileType.choices, default=FileType.WA)
    # arguments to pass to the module at startup
    args = models.CharField(max_length=255, blank=True, default='')
    
    def save(self, *args, **kwargs):
        if (self.parent.nmodules >= self.parent.max_nmodules):
            raise Exception('Parent reached maximimum number of modules ({})'.format(self.parent.max_nmodules))
        super(Module, self).save(*args, **kwargs)
            
    def __str__(self):
        return str({ 'uuid':str(self.uuid), 'name': self.name, 'parent': self.parent, 'filename': self.filename, 'fileid': self.fileid, 'filetype': self.filetype, 'args': self.args })
    
class Link(models.Model):
    # link uuid
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)    
    link_from = models.ForeignKey('Module', on_delete=models.CASCADE, related_name='link_from')   
    link_to = models.ForeignKey('Module', on_delete=models.CASCADE, related_name='link_to')

    #def __str__(self):
    #    return "{}: {} - {}".format(self.uuid, self.link_from, self.link_to)
    

# class APIs():   
#     WASI_SP1 = 'wasi:snapshot_preview1'
#     WASI_UNSTBL = 'wasi:unstable'
#     WASI_CORE = 'wasi:core'
#     WASI_CLOCK = 'wasi:clock'
#     WASI_ENV = 'wasi:environ'
#     WASI_SOCK = 'wasi:sock'
#     WASI_ARGS = 'wasi:args'
#     WASI_FD = 'wasi:fd'
#     WASI_PATH = 'wasi:path'
#     WASI_POLL = 'wasi:poll'
#     WASI_PROC = 'wasi:proc'
#     WASI_RND = 'wasi:random'
#     WASI_SCHED = 'wasi:sched'    