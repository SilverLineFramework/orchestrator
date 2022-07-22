# Runtime Orchestrator

## APIs

- ```reg```: runtime registration
- ```control```: control messages (create/delete modules, exit notifications, etc)
- ```keepalive```: module keepalive

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

- ```server.json```: server configuration. Default values:
    ```JSON
    {
        "host": "localhost",
        "debug": true
    }
    ```

## Running the Orchestrator

### Execute
- ```make run```: alias for ```env/bin/activate; python manage.py runserver```

### UIs
- Admin: `http://localhost:8000/admin/`
- Vizualize: `http://localhost:8000/static/index.html`

## Documentation

The Orchestrator is documented with [Sphinx](https://www.sphinx-doc.org/en/master/index.html) using
Numpy-style docstrings parsed by [Napoleon](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/).

Run ```./build.sh``` to build.
