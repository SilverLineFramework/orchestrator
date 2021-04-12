# ARENA Runtime Supervisor (ARTS)

By leveraging a common runtime and carefully integrated resource monitoring, the ARENA Runtime Supervisor (ARTS) can handle very heterogenous compute resources, across compute classes, from small embedded devices to edge servers. It is distinct from several previous frameworks for managing distributed computing in that it focus on adaptation to changing resources and support for highly heterogenous distributed systems found at the edge.

ARTS is responsible for managing computational resources available in an ARENA realm (realms represent a geographically distinct set of resources). It uses WASM modules as a basic compute unit that can run in isolation in a distributed set of available runtimes, which run in, e.g., headsets, phones, laptops, embedded routers or edge servers. Runtimes register in ARTS their availability, resources and host system access APIs implemented.

As applications are started in the ARENA, ARTS decides the best available compute resource(s) to run the application and monitors its execution do adapt to changing resource availability and consumption. This execution-time adaptation is a unique aspect of ARTS that leverages an important feature: live migration of WASM modules.

This repository includes:
- **arts-main**: Runtime supervisor (ARTS); Accepts registrations from client runtimes and schedules modules to run on them.
- **wasm-apps**: Example/test WASM applications.

You can use the issue tracker to start discussions, suggestions, etc.

## Runtime environments

We currently have three runtime environments being worked on to interact with ARTS:
 - [Embedded Runtime](https://github.com/conix-center/arena-runtime-zephyr)
 - [Linux Runtime](https://github.com/conix-center/arena-runtime-linux)
 - [Browser Runtime](https://github.com/conix-center/arena-runtime-browser)

We also maintain a [simulated runtime](https://github.com/conix-center/arena-runtime-simulated) for prototyping.

See the [Documentation Folder](docs/).
