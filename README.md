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
    - [Environment variables](#set-the-environment-variables)
    - [Docker](#docker)
    - [Python](#python)
- [Testing](#testing)
- [License](#license)


## Quickstart
The API is hosted at https://api.neurobagel.org/ and interfaces with Neurobagel's graph database. Queries of the graph can be run using the `/query` route.

Example: **I want to query for only female participants in the graph.** The URL for such a query would be https://api.neurobagel.org/query/?sex=snomed:248152002, where `snomed:248152002` is a [controlled term from the SNOMED CT database](http://purl.bioontology.org/ontology/SNOMEDCT/248152002) corresponding to female sex.

Interactive documentation for the API is available at https://api.neurobagel.org/docs.

## Local installation
The below instructions assume that you have a local instance of or access to a remotely hosted graph database to be queried. 
If this is not the case and you need to first build a graph from data, refer to our documentation for [getting started locally with a graph backend](https://neurobagel.org/infrastructure/).

### Clone the repo
```bash
git clone https://github.com/neurobagel/api.git
```

### Set the environment variables
Create a `.env` file in the root of the repository to house the environment variables used by the app. 

To run API requests against a graph, at least two environment variables must be set, `NB_GRAPH_USERNAME` and `NB_GRAPH_PASSWORD`.  
The contents of a minimal `.env` file:
```bash
NB_GRAPH_USERNAME=someuser
NB_GRAPH_PASSWORD=somepassword
```

Below are all the possible Neurobagel environment variables that you can set in `.env`, depending on your mode of installation of the API and graph server software.
| Environment variable | Required in .env? | Description                                                                                                                              | Default value                          | Relevant installation mode(s) |
| -------------------- | ----------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------- | ----------------------------- |
| `NB_GRAPH_USERNAME`  | Yes               | Username to access Stardog graph database that API will communicate with                                                                 | -                                      | Docker, Python                |
| `NB_GRAPH_PASSWORD`  | Yes               | Password to access Stardog graph database that API will communicate with                                                                 | -                                      | Docker, Python                |
| `NB_GRAPH_ADDRESS`   | No                | IP address for the graph database (or container name, if graph is hosted locally)                                                        | `206.12.99.17` (`graph`)               | Docker, Python                |
| `NB_GRAPH_DB`        | No                | Name of graph database endpoint to query (e.g., for a Stardog database, this will take the format of `{database_name}/query`)            | `test_data/query`                      | Docker, Python                |
| `NB_RETURN_AGG`      | No                | Whether to return only dataset-level query results (including data locations) and exclude subject-level attributes. One of [true, false] | `true`                                 | Docker, Python                |
| `NB_API_TAG`         | No                | Tag for API Docker image                                                                                                                 | `latest`                               | Docker                        |
| `NB_API_PORT_HOST`   | No                | Port number on the _host machine_ to map the API container port to                                                                       | `8000`                                 | Docker, Python                |
| `NB_API_PORT`        | No                | Port number to use for the _API container_                                                                                               | `8000`                                 | Docker, Python                |
| `NB_GRAPH_IMG`       | No                | Graph server Docker image                                                                                                                | `stardog/stardog:8.2.2-java11-preview` | Docker                        |
| `NB_GRAPH_ROOT_HOST` | No                | Path to directory containing a Stardog license file on the _host machine_                                                                | `~/stardog-home`                       | Docker                        |
| `NB_GRAPH_ROOT_CONT` | No                | Path to directory for graph databases in the _graph server container_                                                                    | `/var/opt/stardog` *                   | Docker                        |
| `NB_GRAPH_PORT_HOST` | No                | Port number on the _host machine_ to map the graph server container port to                                                              | `5820`                                 | Docker                        |
| `NB_GRAPH_PORT`      | No                | Port number used by the _graph server container_                                                                                         | `5820` *                               | Docker                        |

_* These defaults should not be changed if using a Stardog backend._

**NOTE:** To avoid conflicts related to [Docker's environment variable precedence](https://docs.docker.com/compose/environment-variables/envvars-precedence/), 
ensure that any variables defined in your `.env` file are not already set in your current shell environment with **different** values.

If needed, you can export all the variables defined in your `.env` file in one step by running the following:
```bash
export $(cat .env | xargs)
```

The below instructions for Docker and Python assume that you have at least set `NB_GRAPH_USERNAME` and `NB_GRAPH_PASSWORD` in your `.env`.

### Docker
First, [install docker](https://docs.docker.com/get-docker/).

You can then run a Docker container for the API in one of three ways:
#### Option 1 (RECOMMENDED): Use the `docker-compose.yaml` file

First, [install docker compose](https://docs.docker.com/compose/install/).

If needed, update your `.env` file with optional environment variables for the docker compose configuration.

**TIP:** Double check that the environment variables are resolved with your expected values using the command `docker compose config`.

Use Docker Compose to spin up the containers by running the following in the repository root (where the `docker-compose.yml` file is):
```bash
docker compose up -d
```

#### Option 2: Use the latest image from Docker Hub
```bash
export $(cat .env | xargs)  # OPTIONAL: export your environment variables
docker pull neurobagel/api
docker run -d --name=api -p ${NB_API_PORT_HOST:-8000}:${NB_API_PORT:-8000} --env-file=.env neurobagel/api

# NOTE: The argument for the -p flag in the above docker run command, when used as is, 
# will map the value of the variable NB_API_PORT to the value of NB_API_PORT_HOST if 
# either variable has been set in the current shell. If one of the two variables has 
# not been set, a default port number of 8000 will be used instead.
```
#### Option 3: Build the image using the Dockerfile
After cloning the current repository, build the Docker image locally:
```bash
export $(cat .env | xargs)  # OPTIONAL: export your environment variables
docker build -t <image_name> .
docker run -d --name=api -p ${NB_API_PORT_HOST:-8000}:${NB_API_PORT:-8000} --env-file=.env neurobagel/api
```

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

Export the variables defined in your `.env` file:
```bash
export $(cat .env | xargs)
```

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
If you get a 401 response to your API request with an `"Unauthorized: "` error message, your `NB_GRAPH_USERNAME` and `NB_GRAPH_PASSWORD` pair may be incorrect. Verify that these environment variables have been exported and/or have the correct values.

## Testing

Neurobagel API utilizes [Pytest](https://docs.pytest.org/en/7.2.x/) framework for testing.

To run the tests first make sure you're in repository's main directory and in your environment where the dependencies are installed and environment variables are set.

You can then run the tests by executing the following command in your terminal:

```bash
pytest tests
```

### License

Neurobagel API is released under the terms of the [MIT License](LICENSE)