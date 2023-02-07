<div align="center">

# Neurobagel API
    
<div>
    <a href="https://github.com/neurobagel/api/actions/workflows/test.yaml">
        <img src="https://img.shields.io/github/actions/workflow/status/neurobagel/api/test.yaml?color=BDB76B&label=test&style=flat-square">
    </a>
    <a href="https://coveralls.io/github/neurobagel/api">
        <img src="https://img.shields.io/coverallsCoverage/github/neurobagel/api?style=flat-square&color=8FBC8F">
    </a>
    <a href="https://www.python.org/">
        <img src="https://img.shields.io/badge/python-3.10-4682B4?style=flat-square" alt="Python">
    </a>
    <a href="LICENSE">
        <img src="https://img.shields.io/github/license/neurobagel/api?color=CD5C5C&style=flat-square" alt="GitHub license">
    </a>
</div>
<br>
</div>

The Neurobagel API is a REST API, developed in [Python](https://www.python.org/) using [FastAPI](https://fastapi.tiangolo.com/) and [pydantic](https://docs.pydantic.dev/).

- [Quickstart](#quickstart)
- [Local installation](#local-installation)
- [Testing](#testing)
- [License](#license)


## Quickstart
The API is hosted at https://api.neurobagel.org/ and interfaces with Neurobagel's graph database. Queries of the graph can be run using the `/query` route (e.g., the URL for a query for only female participants would be https://api.neurobagel.org/query/?sex=female).

Interactive documentation for the API is available at https://api.neurobagel.org/docs.

NOTE: Currently, to access the API, you must be connected to the McGill network.

## Local installation

### Set the environment variables
To run the API, at least two environment variables must be set, `USER` and `PASSWORD`. An optional third environment variable `DOG_ROOT` may be set to use a different IP address for the graph database.

To set environment variables in macOS and Linux distributions:

```bash
$ export KEY=value

# For example
$ export USER=someuser
```

To set environment variables in Windows from CMD:

```bash
$ set KEY=value

# For example
$ set USER=someuser
```
The below instructions for Docker and Python assume that you have already set `USER` and `PASSWORD` in your current environment.

### Docker
Follow the [official documentation](https://docs.docker.com/get-docker/) for installing Docker. You can then run a Docker container for the API in two ways:
#### Option 1: Pull the latest image from Docker Hub
```bash
docker pull neurobagel/api
docker run --name api -p 8000:8000 --env USER --env PASSWORD neurobagel/api
```
#### Option 2: Build the image using the Dockerfile
After cloning the current repository, build the Docker image locally:
```bash
docker build -t neurobagel/api .
docker run --name api -p 8000:8000 --env USER --env PASSWORD neurobagel/api
```
For either option, if you wish to also set `DOG_ROOT`, make sure to pass it to the container in the `docker run` command using the `--env` flag.

NOTE: In case you're connecting to the McGill network via VPN and you started the container before connecting to the VPN, make sure to configure your VPN client to allow local (LAN) access when using the VPN.

### **Python**
### Install dependencies

After cloning the repository, install the dependencies outlined in the requirements.txt file. For convenience, you can use Python's `venv` package to install dependencies in a virtual environment. You can find the instructions on creating and activating a virtual environment in the official [documentation](https://docs.python.org/3.10/library/venv.html). After setting up and activating your environment, you can install the dependencies by running the following command in your terminal:

```bash
$ pip install -r requirements.txt
```

### Launch the API

To launch the API make sure you're in repository's main directory and in your environment where the dependencies are installed and environment variables are set.

You can then launch the API by running the following command in your terminal:

```bash
$ python -m app.main
```

```bash
INFO:     Will watch for changes in these directories: ['home/usr/directory/']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12683] using StatReload
INFO:     Started server process [12685]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
...
```
You can verify the API is running once you receive info messages similar to the above in your terminal.

## Testing

Neurobagel API utilizes [Pytest](https://docs.pytest.org/en/7.2.x/) framework for testing.

To run the tests first make sure you're in repository's main directory and in your environment where the dependencies are installed and environment variables are set.

You can then run the tests by executing the following command in your terminal:

```bash
pytest tests
```

### License

Neurobagel API is released under the terms of the [MIT License](LICENSE)