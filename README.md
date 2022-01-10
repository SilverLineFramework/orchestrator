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
<!-- markdown-link-check-disable-next-line -->
 - [Embedded Runtime](https://github.com/conix-center/arena-runtime-zephyr)
<!-- markdown-link-check-disable-next-line -->
 - [Linux Runtime](https://github.com/conix-center/arena-runtime-linux)
<!-- markdown-link-check-disable-next-line -->
 - [Browser Runtime](https://github.com/conix-center/arena-runtime-browser)

We also maintain a [native runtime](https://github.com/conix-center/arena-runtime-native) for prototyping.

See the [wiki](https://github.com/conix-center/arts/wiki) for additional documentation.

## Setup

### Dependencies
python 3, pip3, virtualenv (and requirements.txt; check if path in Makefile is correct)

### Setup

Enter the ```arts-main``` directory.
- Create db: ```make migrate```
- Start the virtualenv: ```source env/bin/activate```
- (*Optional*) Create admin user: ```python manage.py createsuperuser --email admin@example.com --username admin```

### Config

**NOTE**: Configuration files are not required for local execution (must also have ```debug=True```).

- ```key.json``` (**secret**): secret key for Django. Should be generated locally (i.e. ```secrets.token_urlsafe(64)```), and only used locally. Schema:
    ```json
    {
        "key": "put_your_secret_key_here"
    }
    ```

- ```credentials.json``` (**secret**): MQTT login credentials. Default values:
    ```json
    {
        "username": "ARTS",
        "password": ""
    }
    ```

- ```mqtt.json```: pubsub server addresses and topic names. Default values:
    ```json
    {
        "realm": "realm",
        "host": "localhost",
        "port": 1883
    }
    ```

## Running ARTS

### Execute
- ```make run```: alias for ```env/bin/activate; python manage.py runserver```

### UIs
- Admin: `http://localhost:8000/admin/`
- Vizualize: `http://localhost:8000/static/index.html`

## Documentation

ARTS is documented with [Sphinx](https://www.sphinx-doc.org/en/master/index.html) using
Numpy-style docstrings parsed by [Napoleon](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/).

Run ```./build.sh``` to build.
