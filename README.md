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
    - [Docker](#docker)
    - [Python](#python)
- [Testing](#testing)
- [License](#license)


## Quickstart
The API is hosted at https://api.neurobagel.org/ and interfaces with Neurobagel's graph database. Queries of the graph can be run using the `/query` route.

Example: **I want to query for only female participants in the graph.** The URL for such a query would be https://api.neurobagel.org/query/?sex=snomed:248152002, where `snomed:248152002` is a [controlled term from the SNOMED CT database](http://purl.bioontology.org/ontology/SNOMEDCT/248152002) corresponding to female sex.

Interactive documentation for the API is available at https://api.neurobagel.org/docs.

NOTE: Currently, to access the API, you must be connected to the McGill network.

## Local installation
The below instructions assume that you have a local instance of or access to a remotely hosted graph database to be queried. If this is not the case and you need to first build a graph from data, refer to the instructions for getting started locally with [Stardog Studio](https://docs.stardog.com/stardog-applications/dockerized_access#stardog-studio).

### Clone the repo
```bash
git clone https://github.com/neurobagel/api.git
```

### Set the environment variables
Create a `.env` file in the root of the repository to house the environment variables used by the app. To run the API, at least two environment variables must be set, `USERNAME` and `PASSWORD`.  
The contents of a minimal `.env` file:
```bash
USERNAME=someuser
PASSWORD=somepassword
```
Optional environment variables for the API may also be defined in `.env`:
- `GRAPH_ADDRESS`: to use a different IP address for the graph database
- `RETURN_AGG`: whether to return only dataset-level query results (including file paths) and exclude subject-level attributes. Should be one of [true, false], true by default.

To export all the variables in your `.env` file in one step, run the following:
```bash
export $(cat .env | xargs)
```

The below instructions for Docker and Python assume that you have at least set `USERNAME` and `PASSWORD` in your current environment.

### Docker
First, [install docker](https://docs.docker.com/get-docker/).

 You can then run a Docker container for the API in one of three ways:
#### Option 1: Use the `docker-compose.yaml` file

First, [install docker-compose](https://docs.docker.com/compose/install/).

If needed, update your `.env` file with optional environment variables for the docker-compose configuration:
- `API_TAG`: Tag for API Docker image (default: `latest`)
- `GRAPH_ADDRESS`: container name or IP address for the graph database (default: `graph`)
- `GRAPH_DB`: name of existing graph database to query (default: `test_data`)
- `STARDOG_TAG`: Tag for Stardog Docker image (default: `8.2.2-java11-preview`)
- `STARDOG_ROOT`: Path to directory on host machine containing a Stardog license file (default: `~/stardog-home`)

NOTE: To avoid conflicts related to [Docker's environment variable precedence](https://docs.docker.com/compose/environment-variables/envvars-precedence/), ensure that any variables defined in your `.env` file are not already set in your current shell environment with **different** values.

Use Docker Compose to spin up the containers by running the following in the repository root (where the `docker-compose.yml` file is):
```bash
docker compose up -d
```

#### Option 2: Use the latest image from Docker Hub
```bash
source .env # set your environment variables 
docker pull neurobagel/api
docker run -d --name api -p 8000:8000 --env USERNAME --env PASSWORD neurobagel/api
```
#### Option 3: Build the image using the Dockerfile
After cloning the current repository, build the Docker image locally:
```bash
source .env # set your environment variables
docker build -t <image_name> .
docker run -d --name api -p 8000:8000 --env USERNAME --env PASSWORD neurobagel/api
```

For Options 2 or 3, if you wish to also set `GRAPH_ADDRESS`, make sure to pass it to the container in the `docker run` command using the `--env` flag.

NOTE: In case you're connecting to the McGill network via VPN and you started the container before connecting to the VPN, make sure to configure your VPN client to allow local (LAN) access when using the VPN.

#### Send a test query to the API
By default, after running the above steps, the API should be served at localhost, http://127.0.0.1:8000/query, on the machine where you launched the Dockerized app. To check that the API is running and can access the knowledge graph as expected, you can navigate to the interactive API docs in your local browser (http://127.0.0.1:8000/docs) and enter a sample query, or send an HTTP request in your terminal using `curl`:
``` bash
# example: query for female subjects in graph
curl -L http://127.0.0.1:8000/query/?sex=snomed:248152002 
```
The response should be a list of dictionaries containing info about datasets with participants matching the query.

### Python
#### Install dependencies

After cloning the repository, install the dependencies outlined in the requirements.txt file. For convenience, you can use Python's `venv` package to install dependencies in a virtual environment. You can find the instructions on creating and activating a virtual environment in the official [documentation](https://docs.python.org/3.10/library/venv.html). After setting up and activating your environment, you can install the dependencies by running the following command in your terminal:

```bash
$ pip install -r requirements.txt
```

#### Launch the API

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

### Troubleshooting
If you get a 401 response to your API request with an `"Unauthorized: "` error message, your `USERNAME` and `PASSWORD` pair may be incorrect. Verify that these environment variables have been exported and/or have the correct values.

## Testing

Neurobagel API utilizes [Pytest](https://docs.pytest.org/en/7.2.x/) framework for testing.

To run the tests first make sure you're in repository's main directory and in your environment where the dependencies are installed and environment variables are set.

You can then run the tests by executing the following command in your terminal:

```bash
pytest tests
```

### License

Neurobagel API is released under the terms of the [MIT License](LICENSE)