""" Data structure to hold configurations for all 
platform resource details connected to ARTS"""

class PlatformConfig():

    def __init__(self):
        self._platform = {}

    def add(self, name, resources):
        if name in self._platform:
            return
        self._platform[name] = resources

    def remove(self, name):
        if name in self._platform:
            self._platform.pop(name)

    def print(self):
        print(self._platform)
 

