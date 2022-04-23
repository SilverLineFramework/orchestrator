from pathlib import Path
from igraph import *
import sys
import itertools
import json
import pprint
import logging
import yaml

class Manifest:

    def __init__(self, manifest_type, fobj, is_dict=False):
        self.__manifest_type = manifest_type
        if self.__manifest_type == "APP":
            manifest_path = 'apps'
        elif self.__manifest_type == "PLATFORM":
            manifest_path = 'platforms'
        else:
            logging.error("Wrong manifest type: Must be either APP or PLATFORM")
            sys.exit()

        if is_dict:
            self._manifest = fobj
        else:
            manifest_path = Path('sample_manifests') /  manifest_path /  fobj
            with open(manifest_path) as f:
                self._manifest = yaml.safe_load(f)

    def print_raw(self):
        print(json.dumps(self._manifest, sort_keys=False, indent=4))


    def get_manifest_type(self):
        return self.__manifest_type

    def print_resource_info (self):
        print("\n---- {} RESOURCE INFO ----".format(self.__manifest_type))
        print(json.dumps(self.resource_info, sort_keys=False, indent=4))
        print("-------------------------")


class AppManifest(Manifest):

    # Public variables:
    #   app_name
    #   resource_info
    #   channel_info
    #   module_names

    def __init__(self, manifest_file, is_dict=False):
        super().__init__('APP', manifest_file, is_dict)
        self._parse_manifest()
        logging.info("Parsed application manifest file \'{}\'".format(manifest_file))

    # Add mod_name to all channel_names
    def __populate_channel_entries(self, mod_name, channel_names, channel_type, tag):
        # Populate nodes on the channel
        for channel_name in channel_names:
            channel_entry = self.channel_info[channel_name]
            if tag in channel_type:
                if tag not in channel_entry:
                    channel_entry[tag] = []
                if mod_name not in channel_entry[tag]:
                    channel_entry[tag].append(mod_name)


    # Add channel information to class object
    def __add_channel (self, channel):
        channel_name, channel_entry = next(iter(channel.items()))
        self.channel_info[channel_name] = channel_entry

        if "max_latency" not in channel_entry:
            channel_entry["max_latency"] = None
        if "min_bandwidth" not in channel_entry:
            channel_entry["min_bandwidth"] = None

        # Add modules for global channels if they exist
        if 'global' in channel_entry:
            channel_type = channel_entry['global']
            for mod_name in self.module_names:
                self.__populate_channel_entries(mod_name, [channel_name], channel_type, 'sub')
                self.__populate_channel_entries(mod_name, [channel_name], channel_type, 'pub')


    def _parse_manifest (self):
        self.app_name = self._manifest['app-name']
        self._modules = self._manifest['modules']
        
        # Vertices of app graph
        self.module_names = list(self._modules.keys())
        self.resource_info = {}

        # Edges of graph: Convert to convenient format
        self.channel_info = {}

        # Add channel list to channel_info
        if 'channels' in self._manifest:
            for channel in self._manifest['channels']:
                self.__add_channel(channel)

        # Add local channels and resources of all modules. along with their constraints
        for name, props in self._modules.items():
            if props is not None:
                if 'channels' in props:
                    for channel_type, channel_names in props['channels'].items():
                        self.__populate_channel_entries(name, channel_names, channel_type, 'sub')
                        self.__populate_channel_entries(name, channel_names, channel_type, 'pub')
                if 'resources' in props:
                    self.resource_info[name] = props['resources']
                else:
                    self.resource_info[name] = None
            else:
                self.resource_info[name] = None
        


    def print_channel_info (self):
        print("\n---- APP CHANNEL INFO ----")
        print(json.dumps(self.channel_info, sort_keys=False, indent=4))
        print("------------------------")


    def show_graph (self):
        g = Graph(directed=True)
        # Vertices
        g.add_vertices(len(self.module_names))
        g.vs["name"] = self.module_names
        g.vs["label"] = g.vs["name"]
        # Edges
        es_label = []
        for channel_name, info in self.channel_info.items():
            pub_idx = [self.module_names.index(mod) for mod in info['pub']]
            sub_idx = [self.module_names.index(mod) for mod in info['sub']]
            edge_list = list(itertools.product(pub_idx, sub_idx))
            g.add_edges(edge_list)
            module_name_rep = [channel_name] * len(edge_list)
            es_label.extend(module_name_rep)

        g.es["label"] = es_label

        # Styling
        g.es["curved"] = 0.2
        visual_style = {}
        visual_style["vertex_size"] = 80
        visual_style["bbox"] = (1000, 700)
        visual_style["margin"] = 60

        logging.debug(g)
        layout = g.layout("kk")
        plot(g, **visual_style, layout=layout)


    def get_module (self, name):
        return self._modules[name]


class PlatformManifest(Manifest):

    # Public variables:
    #   platform_name
    #   resource_info
    #   pings
    #   node_names

    def __init__(self, manifest_file, is_dict=False):
        super().__init__('PLATFORM', manifest_file, is_dict)
        self._parse_manifest()
        logging.info("Parsed platform manifest file \'{}\'".format(manifest_file))


    def _parse_manifest (self):
        self.platform_name = self._manifest['platform-name']
        self._nodes = self._manifest['nodes']
        
        # Vertices of platform graph
        self.node_names = list(self._nodes.keys())
        #print(self._node_names)
        
        self.resource_info = {}
        self.pings = {}

        for name, props in self._nodes.items():
            self.pings[name] = props['ping']
            self.resource_info[name] = props['resources']



    def add_node (self, name, uuid, ping, resources):
        if name in self._nodes:
            return
        self._nodes[name] = {}
        self._nodes[name]['uuid'] = uuid
        self._nodes[name]['ping'] = ping
        self._nodes[name]['resources'] = resources

        self.resource_info[name] = resources
        self.pings[name] = ping
        self.node_names.append(name)

    def remove_node (self, name):
        if name in self._nodes:
            self._nodes.pop(name)
            self.resource_info.pop(name)
            self.pings.pop(name)
            self.node_names.remove(name)

    def get_node (self, name):
        return self._nodes[name]








