#!/usr/bin/python3
import sys
import itertools
import json
import pprint
import logging
from argparse import ArgumentParser, RawTextHelpFormatter
from pathlib import Path
import yaml
from copy import deepcopy
from enum import IntEnum

from manifest import AppManifest, PlatformManifest

def argsort(seq, reverse=False):
    return sorted(range(len(seq)), key=seq.__getitem__, reverse=reverse)


class Policy(IntEnum):
    SEPARATION = 0
    CLUSTERING = 1
    NETWORK_BALANCE = 2
    CPU_BALANCE = 3
    MEM_BALANCE = 4

    @staticmethod
    def strs():
        return ['separation', 'clustering', 'network', 'cpu', 'memory']

class VerifyException(Exception):
    pass

class ModuleMapper:

    def __init__(self, app_manifest, platform_manifest):
        self._app = app_manifest
        self._platform = platform_manifest

    def print_app_info(self, show_graph=False):
        self._app.print_channel_info()
        self._app.print_resource_info()
        if show_graph:
            self._app.show_graph()

    def print_platform_info(self):
        self._platform.print_resource_info()

    def print_initial(self):
        self.print_app_info()
        self.print_platform_info()

    def print_mapping(self):
        print(json.dumps(self._map_pinned, sort_keys=False, indent=4))
        print(json.dumps(self._map_node2module, sort_keys=False,indent=4))
        print(json.dumps(self._map_module2node, sort_keys=False, indent=4))

    # Print state after each pass
    def __print_pass_out(self, count, pass_name):
        print("------ #{} : {} -------".format(count, pass_name))
        self.print_mapping()
        print("-----------------------\n")


    def _map_module_to_nodes(self, module_resources):
        pass


    # Pin a module to a given node, and vice versa
    def __pin(self, pin_node, module):
        self._map_pinned[module] = True
        self._map_node2module[pin_node].append(module)
        self._map_module2node[module] = pin_node

        # Update running resources
        res_info = self._app.resource_info[module]
        if "cpus" in res_info:
            self._node_running_resources[pin_node]["cpus"] -= res_info["cpus"]
        if "memory" in res_info:
            self._node_running_resources[pin_node]["memory"] -= res_info["memory"]


    # Check if node has enough resources to pin a module
    def __pinnable(self, pin_node, module):
        res_info = self._app.resource_info[module]
        has_cpus = "cpus" in res_info
        has_mem = "memory" in res_info

        if (has_cpus and self._node_running_resources[pin_node]["cpus"] < res_info["cpus"]) or\
            (has_mem and self._node_running_resources[pin_node]["memory"] < res_info["memory"]):
            return False
        else:
            return True


    # Return convenient structure for accessing hardware specs in a manifest
    def _construct_hardware_map (self, resource_info, map_type):
        hw_map = {}
        for name, resources in resource_info.items():
            if resources is not None and 'hardware' in resources:
                for hw_item in resources['hardware']:
                    # Resolve dict vs list item
                    if type(hw_item) is dict:
                        hw_category = next(iter(hw_item))
                        unique_ids = hw_item[hw_category]
                    else:
                        hw_category = hw_item
                        unique_ids = None

                    if hw_category not in hw_map:
                        hw_map[hw_category] = {}

                    # Unspecified id for applications are Pool resources
                    # Platforms must specify IDs for any resource
                    if unique_ids is None:
                        if "POOL" not in hw_map[hw_category]:
                            hw_map[hw_category]["POOL"] = []
                        hw_map[hw_category]["POOL"].append(name)
                    else:
                        id_list = unique_ids.split()
                        for unique_id in id_list:
                            # Application format
                            if map_type == "APP":
                                # If ID encountered again, duplicate. Throw warning
                                if "ID" in hw_map[hw_category] and unique_id in hw_map[hw_category]["ID"]:
                                    logging.warning("\'{}\' resource was pinned by multiple modules".format(unique_id)) 
                                else:
                                    if "ID" not in hw_map[hw_category]:
                                        hw_map[hw_category]["ID"] = {}
                                    if unique_id not in hw_map[hw_category]:
                                        hw_map[hw_category]["ID"][unique_id] = []
                                # Register module resource
                                hw_map[hw_category]["ID"][unique_id].append(name)

                            # Platform format
                            else:
                                if unique_id in hw_map[hw_category]:
                                    logging.warning("\'{}\' unique id multiply defined".format(unique_id))
                                else:
                                    hw_map[hw_category][unique_id] = name
                
        return hw_map
        

    # Look at targetted resources in application spec and pin them to specified platform
    def _filter_by_hardware_constraints (self):
        _hw_app_map = self._construct_hardware_map(self._app.resource_info, self._app.get_manifest_type())
        _hw_platform_map = self._construct_hardware_map(self._platform.resource_info, self._platform.get_manifest_type())

        logging.debug("App hardware map: " + json.dumps(_hw_app_map,
        sort_keys=False, indent=4) + "\n\n")
        logging.debug("Platform hardware map: " + json.dumps(_hw_platform_map,
        sort_keys=False, indent=4) + "\n\n")

        for hw_category, app_hw_instances in _hw_app_map.items():
            if "ID" in app_hw_instances:
                # ID Targetted Pinning: Only one module option per node
                for uid, module_list in app_hw_instances["ID"].items():
                    pin_node = _hw_platform_map[hw_category][uid]

                    for module in module_list:
                        # If multiple pinned resources are on separate hardware
                        if self._map_pinned[module] and module not in self._map_node2module[pin_node]:
                            logging.error("Cannot satisfy resource constraint for \'{}\' --> "\
                                "Multiple hardware-pinned resources mapped to different platforms".format(module))
                        
                        # Pin module
                        if not self.__pinnable(pin_node, module):
                            logging.error("Module \'{}\' hardware-pinned to node \'{}\' but cannot satisfy other resource "\
                                "constraints (cpu, mem, etc.)".format(module, pin_node))
                        self.__pin(pin_node, module)

            if "POOL" in app_hw_instances:
                for pool_module in app_hw_instances["POOL"]:
                    # All platform resource are IDed
                    # Get all options for pool resources
                    pool_node_options = list(_hw_platform_map[hw_category].values())

                    # If pool resource not available along with pinned resource for a module, 
                    # cannot satisfy resource constraint
                    if self._map_pinned[pool_module]:
                        if self._map_module2node[pool_module] not in pool_node_options:
                            logging.warning("Cannot satisfy resource constraint for \'{}\' --> "\
                                "\'{}\' pool resource not available on targetted node".format(pool_module, hw_category))
                    
                    # If pool resources cannot be assigned together
                    else:
                        if not self._map_module2node[pool_module]:
                            overlap_nodes = pool_node_options
                        else:
                            overlap_nodes = [node for node in pool_node_options if node in self._map_module2node[pool_module]]
                        logging.debug("Overlap nodes \'{}\' : {}".format(pool_module, overlap_nodes))

                        # If pool resources cannot be guaranteed together, print warning
                        if not overlap_nodes:
                            logging.warning("Cannot satisfy resource constraint for \'{}\' --> "\
                                "All pool resources cannot be guaranteed".format(pool_module))

                        self._map_module2node[pool_module] = overlap_nodes


        # Modules with no constraints can go to any node
        for module, nodes in self._map_module2node.items():
            if not nodes:
                self._map_module2node[module] = self._platform.node_names



    def _filter_by_resource_constraints (self):
        for module, resources in self._app.resource_info.items():
            if not self._map_pinned[module]:
                valid_nodes = [node for node in self._map_module2node[module]
                                    if self.__pinnable(node, module)]
                if not valid_nodes:
                    logging.warning("Cannot satisfy \'{}\' constraint for \'{}\'".format(field, module))

                self._map_module2node[module] = valid_nodes
        


    # Map modules to location with least number of modules running
    def _opt_separation_pass (self):
        for module in self._app.module_names:
            if not self._map_pinned[module]:
                p_nodes = self._map_module2node[module]
                num_mods = [len(mods) for name, mods in self._map_node2module.items() if name in p_nodes]

                # Least count is the pin node
                pin_node_idxs = argsort(num_mods)
                pin_node = None
                for idx in pin_node_idxs:
                    pin_node = p_nodes[idx]
                    if self.__pinnable(pin_node, module):
                        break

                # If no node can be pinned, bin packing was not performed optimally. 
                # Just pin to first available node
                if pin_node == None:
                    pin_node = p_nodes[0]
                    logging.warning("Cannot satisfy mapping \'{}\' on any valid nodes due to lack of \
                        resources. Pinning arbitrarily to \'{}\'".format(module, pin_node))
                
                self.__pin(pin_node, module)


    # Map modules to location with most number of modules running
    def _opt_cluster_pass (self):
        for module in self._app.module_names:
            if not self._map_pinned[module]:
                p_nodes = self._map_module2node[module]
                num_mods = [len(mods) for name, mods in self._map_node2module.items() if name in p_nodes]

                # Most count is the pin node
                pin_node_idxs = argsort(num_mods, reverse=True)
                pin_node = None
                for idx in pin_node_idxs:
                    pin_node = p_nodes[idx]
                    if self.__pinnable(pin_node, module):
                        break

                # If no node can be pinned, bin packing was not performed optimally. 
                # Just pin to first available node
                if pin_node == None:
                    pin_node = p_nodes[0]
                    logging.warning("Cannot satisfy mapping \'{}\' on any valid nodes due to lack of \
                        resources. Pinning arbitrarily to \'{}\'".format(module, pin_node))
                
                self.__pin(pin_node, module)


    '''
    Algorithm: 
        - Map modules in descending resource usage to modules with most free
        resource
        - For modules with no resources provided, use separation criteria
    '''
    def _balance_pack_field (self, modules, nodes, field):
        # Construct a list with the "field" for modules and nodes
        modules_field = [self._app.resource_info[mod][field] if field in self._app.resource_info[mod]
                else 0 for mod in modules]


        # Sort in descending order of field
        mod_sidx = argsort(modules_field, reverse=True)

        for m_idx in mod_sidx:
            nodes_field = [self._node_running_resources[node][field] for node in nodes]
            logging.debug(nodes)
            logging.debug("Nodes field: {}".format(nodes_field))

            pin_module = modules[m_idx]
            pin_node = None
            for n_idx in argsort(nodes_field, reverse=True):
                pin_node = nodes[n_idx]
                # Attempt to pin module to node with largest 
                if self.__pinnable(pin_node, pin_module):
                    break

            if pin_node == None:
                pin_node = nodes[0]
                logging.warning("Cannot satisfy mapping \'{}\' on any valid nodes due to lack of \
                    resources. Pinning arbitrarily to \'{}\'".format(pin_module, pin_node))

            logging.info("Pinning \'{}\' to \'{}\' based on \'{}\'".format(pin_module, pin_node, field))
            self.__pin(pin_node, pin_module)


    # Fancy Bin-Packing
    def _opt_network_pass(self):
        pass

    # Fancy Bin Packing for CPUs
    def _opt_cpu_balance_pass(self):
        unmapped_modules = [mod for mod in self._app.module_names if not self._map_pinned[mod]]
        self._balance_pack_field(unmapped_modules, self._platform.node_names, "cpus")

    # Fancy Bin Packing for Mem
    def _opt_mem_balance_pass(self):
        unmapped_modules = [mod for mod in self._app.module_names if not self._map_pinned[mod]]
        self._balance_pack_field(unmapped_modules, self._platform.node_names, "memory")




    # Verify that the final mapping is schematically correct
    def __verify_mapping(self):
        try:
            for module in self._app.module_names:
                if not self._map_pinned:
                    logging.error("\'{}\': Module not pinned".format(module))
                    raise VerifyException
                elif type(self._map_module2node[module]) is not str:
                    logging.error("\'{}\': Module mapped incorrectly to multiple nodes".format(module))
                    raise VerifyException

                node = self._map_module2node[module]
                if module not in self._map_node2module[node]:
                    logging.error("\'{}\': Node does not contain module \'{}\'".format(node, module))
                    raise VerifyException
            
            for node, resources in self._node_running_resources.items():
                if resources["cpus"] < 0:
                    logging.error("\'{}\': Modules on node cannot satisfy cpu constraint ({})"\
                            .format(node, resources["cpus"]))
                    raise VerifyException

                if resources["memory"] < 0:
                    logging.error("\'{}\': Modules on node cannot satisfy memory constraint ({})"\
                            .format(node, resources["memory"]))
                    raise VerifyException
            
            print("Successful verification of mapping!")

        except VerifyException:
            print("Error in mapping verification")


    # Determine optimal mapping of modules onto nodes
    def map_modules(self, policy):
        self._policy = policy
        opt_passes_fns = [self._opt_separation_pass, 
                         self._opt_cluster_pass,
                         self._opt_network_pass,
                         self._opt_cpu_balance_pass, 
                         self._opt_mem_balance_pass
                         ]

        opt_passes = [(fn.__name__, fn) for fn in opt_passes_fns]
        opt_pass = opt_passes[policy]

        self._map_pinned = {name: False for name in self._app.module_names}
        self._map_node2module = {name: [] for name in self._platform.node_names}
        self._map_module2node = {name: [] for name in self._app.module_names}
        # Update resources as modules get pinned
        self._node_running_resources = deepcopy(self._platform.resource_info)
        
        # Filtering by hardware constraints must always be the first pass
        # Resolution of left over modules must always be the last pass
        map_passes = {
                "(Initial) Hardware Constraint Pass": self._filter_by_hardware_constraints,
                "Resource Constraint Pass": self._filter_by_resource_constraints,
                "(Final) {} ".format(opt_pass[0]): opt_pass[1]
            }
        
        count = 1;
        # Run passes in order
        # TODO: Decide on a good order
        for pass_name, map_pass in map_passes.items():
            map_pass()
            # If only one module left, it can be pinned
            for module, potential_nodes in self._map_module2node.items():
                if not self._map_pinned[module] and len(potential_nodes) == 1:
                    pin_node = potential_nodes[0]
                    self.__pin(pin_node, module)

            if logging.root.level == logging.DEBUG or map_pass == opt_pass[1]:
                self.__print_pass_out(count, pass_name)
            count += 1

        self.__verify_mapping()
              

        



def get_args():
    policy_choices = Policy.strs()
    log_opts = ["debug", "info", "warning", "error", "critical"]

    ''' Module Mapper Argument Parser '''
    parser = ArgumentParser(description='Module Mapper User Configurations',
        formatter_class = RawTextHelpFormatter)

    # Application
    parser.add_argument(
        '--app', help="Path to application manifest", dest="app")
    # Platform
    parser.add_argument(
        '--platform', help="Path to platform manifest", dest="platform")

    # Policy
    parser.add_argument(
        '--policy', default='separation', help="Policy to optimize mapping configuration",
        dest="policy", choices=policy_choices)

    # App Graph
    parser.add_argument(
        '--graph', default=False, help="Display application network graph",
        dest="graph", action='store_true') 

    # Logging Level
    parser.add_argument(
        '--log', default="warning", help="Logging level {Default: warning}",
        dest="loglevel", choices=log_opts) 

    args = parser.parse_args()
    # Mapper uses index for determining policy pass
    args.policy = policy_choices.index(args.policy)
    return args


if __name__ == '__main__':
    args = get_args()

    # Set up logging
    log_numlevel = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(log_numlevel, int):
        raise ValueError("Invalid log level for input: \'{}\'".format(args.loglevel))
    logging.basicConfig(level=log_numlevel, format="[%(levelname)s | %(filename)s:%(lineno)d] %(message)s")

    #with open(Path('sample_manifests') / 'apps' / args.app) as f:
    #    app_dict = yaml.safe_load(f)
    #App = AppManifest(app_dict, is_dict=True)

    App = AppManifest(args.app)
    Platform = PlatformManifest(args.platform)

    Mapper = ModuleMapper(App, Platform)
    Mapper.map_modules(args.policy)

    if args.graph:
        App.show_graph()
