<div align="center">

# Neurobagel API
    
[![Tests](https://img.shields.io/github/actions/workflow/status/neurobagel/api/test.yaml?color=BDB76B&label=test&style=flat-square)](https://github.com/neurobagel/api/actions/workflows/test.yaml)
[![Coverage](https://img.shields.io/coverallsCoverage/github/neurobagel/api?style=flat-square&color=8FBC8F)](https://coveralls.io/github/neurobagel/api)
[![Python](https://img.shields.io/badge/python-3.10-4682B4?style=flat-square)](https://www.python.org/)
[![License](https://img.shields.io/github/license/neurobagel/api?color=CD5C5C&style=flat-square)](LICENSE)

</div>

The Neurobagel API is a REST API, developed in [Python](https://www.python.org/) using [FastAPI](https://fastapi.tiangolo.com/) and [Pydantic](https://docs.pydantic.dev/).

Please refer to our [**official documentation**](https://neurobagel.org/api/) for more information on how to use the API.

- [Quickstart](#quickstart)
- [Local installation](#local-installation)
    - [Environment variables](#set-the-environment-variables)
    - [Docker (recommended)](#docker)
    - [Python](#python)
- [Testing](#testing)
- [The default Neurobagel SPARQL query](#the-default-neurobagel-sparql-query)
- [License](#license)


## Quickstart
The API is hosted at https://api.neurobagel.org/ and interfaces with Neurobagel's graph database. Queries of the graph can be run using the `/query` route.

Example: **I want to query for only female participants in the graph.** 
The URL for such a query would be https://api.neurobagel.org/query?sex=snomed:248152002, where `snomed:248152002` is a [controlled term from the SNOMED CT database](http://purl.bioontology.org/ontology/SNOMEDCT/248152002) corresponding to female sex.

Interactive documentation for the API is available at https://api.neurobagel.org/docs.

## Local installation
The below instructions assume that you have a local instance of or access to a remotely hosted graph database to be queried. 
If this is not the case and you need to first build a graph from data, refer to our documentation for [getting started locally with a graph backend](https://neurobagel.org/getting_started/).

### Clone the repo
```bash
git clone https://github.com/neurobagel/api.git
```

### Set the environment variables
Create a file called `.env` in the root of the repository to store the environment variables used by the app. 
See the Neurobagel recipes repo for a [template `.env` file](https://github.com/neurobagel/recipes/blob/main/template.env) you can copy and edit.

To run API requests against a graph, at least two environment variables must be set: `NB_GRAPH_USERNAME` and `NB_GRAPH_PASSWORD`.

**See our [official documentation](https://neurobagel.org/config/#environment-variables) for all the possible Neurobagel environment variables that you can set in `.env`, and to check which variables are relevant for your specific installation and setup.**

> :warning: **Important:** 
> - Variables set in the shell environment where the API is launched **_should not be used as a replacement for the `.env` file_** to configure options for the API or graph server software.
> - To avoid conflicts related to [Docker's environment variable precedence](https://docs.docker.com/compose/environment-variables/envvars-precedence/), 
> also ensure that any variables defined in your `.env` are not already set in your current shell environment with **different** values.

The below instructions for Docker and Python assume that you have at least set `NB_GRAPH_USERNAME` and `NB_GRAPH_PASSWORD` in your `.env`.

### Docker
First, [install Docker](https://docs.docker.com/get-docker/).

You can then run a Docker container for the API in one of three ways:
#### Option 1 (RECOMMENDED): Use the Neurobagel Docker Compose recipe

Follow the instructions in our [official documentation](https://neurobagel.org/getting_started/) for using the template configuration files provided in our [recipes](https://github.com/neurobagel/recipes) repository to spin up a local Neurobagel API and graph backend using [Docker Compose](https://docs.docker.com/compose/install/).

**TIP:** Double check that Neurobagel environment variables are resolved with your expected values using the command `docker compose config`.

#### Option 2: Use the latest image from Docker Hub
```bash
docker pull neurobagel/api
docker run -d --name=api -p 8000:8000 --env-file=.env neurobagel/api
```
**NOTE:** The above `docker run` command uses recommended default values for `NBI_API_PORT_HOST` and `NB_API_PORT` in the `-p` flag.
If you wish to set different port numbers, modify your `.env` file accordingly and run the below commands instead:
```bash
export $(cat .env | xargs)  # export your .env file to expose your set port numbers to the -p flag of docker run
docker run -d --name=api -p ${NB_API_PORT_HOST}:${NB_API_PORT} --env-file=.env neurobagel/api
```
> :warning: **IMPORTANT:** If using the above command, do not wrap any values for variables in the `.env` file in quotation marks, as they will be interpreted literally and may lead to [issues](https://github.com/docker/for-linux/issues/1208).

#### Option 3: Build the image using the Dockerfile
After cloning the current repository, build the Docker image locally:
```bash
docker build -t neurobagel/api .
docker run -d --name=api -p 8000:8000 --env-file=.env neurobagel/api
```
**NOTE:** The above `docker run` command uses recommended default values for `NBI_API_PORT_HOST` and `NB_API_PORT` in the `-p` flag. 
If you wish to set different port numbers, modify your `.env` file accordingly and run the below commands instead:
```bash
docker build -t neurobagel/api .
export $(cat .env | xargs)  # export your .env file to expose your set port numbers to the -p flag of docker run
docker run -d --name=api -p ${NB_API_PORT_HOST}:${NB_API_PORT} --env-file=.env neurobagel/api
```
> :warning: **IMPORTANT:** If using the above command, do not wrap any values for variables in the `.env` file in quotation marks, as they will be interpreted literally and may lead to [issues](https://github.com/docker/for-linux/issues/1208).

#### Send a test query to the API
By default, after running the above steps, the API should be served at localhost, http://127.0.0.1:8000/query, on the machine where you launched the Dockerized app. To check that the API is running and can access the knowledge graph as expected, you can navigate to the interactive API docs in your local browser (http://127.0.0.1:8000/docs) and enter a sample query, or send an HTTP request in your terminal using `curl`:
``` bash
# example: query for female subjects in graph
curl http://127.0.0.1:8000/query?sex=snomed:248152002 
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

To run the tests, first ensure you're in the repository's root directory and in the environment where the dependencies are installed.

Install the submodules used by the tests:
```bash
git submodule init
git submodule update
```

You can then run the tests by executing the following command in your terminal:

```bash
pytest tests
```

To run the integration tests of SPARQL queries (skipped by default), also launch the test graph store:

```bash
docker compose up -d test_graph
```

_NOTE: Don't have a `.env` file in the root directory as it will conflict with the environment variable configuration of the docker compose file, 
since docker compose will try to use `.env` by default._

Then, run all tests using:
```bash
pytest -m "integration or not integration"
# OR
pytest -m ""
```

Or, to run only the integration tests:
```bash
pytest -m "integration"
```

Once you are done with testing, you can stop and remove the test graph container:
```bash
docker compose stop test_graph
docker compose rm -f test_graph
```

## The default Neurobagel SPARQL query

[`docs/default_neurobagel_query.rq`](docs/default_neurobagel_query.rq) contains a sample default SPARQL query sent by the Neurobagel API to a graph database to retrieve all available phenotypic and imaging data.
This file is mainly intended for reference because in normal operations, 
the API will always talk to the graph on behalf of the user.

(For developers) 
To regenerate this sample query when the API query template is updated, run the following commands from the repository root in an interactive Python terminal:

```python
from app.api.utility import create_query

with open("docs/default_neurobagel_query.rq", "w") as file:
    file.write(create_query(return_agg=False))
```

### License

Neurobagel API is released under the terms of the [MIT License](LICENSE)
