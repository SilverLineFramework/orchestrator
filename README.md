# ARENA Runtime Supervisor (ARTS)

By leveraging a common runtime and carefully integrated resource monitoring, the ARENA Runtime Supervisor (ARTS) can handle very heterogenous compute resources, across compute classes, from small embedded devices to edge servers. It is distinct from several previous frameworks for managing distributed computing in that it focus on adaptation to changing resources and support for highly heterogenous distributed systems found at the edge.

ARTS is responsible for managing computational resources available in an ARENA realm (realms represent a geographically distinct set of resources). It uses WASM modules as a basic compute unit that can run in isolation in a distributed set of available runtimes, which run in, e.g., headsets, phones, laptops, embedded routers or edge servers. Runtimes register in ARTS their availability, resources and host system access APIs implemented.

As applications are started in the ARENA, ARTS decides the best available compute resource(s) to run the application and monitors its execution do adapt to changing resource availability and consumption. This execution-time adaptation is a unique aspect of ARTS that leverages an important feature: live migration of WASM modules.

This repository includes:
- **arts-main**: Runtime manager (ARTS); Accepts registrations from client runtimes and schedules modules to run on them.
- **clauncher**: Module launcher (on a Linux WASM/Python runtime/interpreter).
- **clauncher-js**: Browser-based module launcher.

See the [Runtime Design Notes](https://docs.google.com/presentation/d/1HJaQPFMV_sUyMLoiXciZn9KVTCNXCgQ5LeNxbp_Vf2U/edit?usp=sharing).
