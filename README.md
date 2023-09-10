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
    - [Docker (recommended)](#docker)
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
Create a file called `.env` in the root of the repository to store the environment variables used by the app. 
This repository contains a [template `.env` file](/.template-env) that you can copy and edit.

To run API requests against a graph, at least two environment variables must be set: `NB_GRAPH_USERNAME` and `NB_GRAPH_PASSWORD`.

**See our [official documentation](https://neurobagel.org/infrastructure/#set-the-environment-variables) for all the possible Neurobagel environment variables that you can set in `.env`, and to check which variables are relevant for your specific installation and setup.**

> :warning: **Important:** 
> - Variables set in the shell environment where the API is launched **_should not be used as a replacement for the `.env` file_** to configure options for the API or graph server software.
> - To avoid conflicts related to [Docker's environment variable precedence](https://docs.docker.com/compose/environment-variables/envvars-precedence/), 
> also ensure that any variables defined in your `.env` are not already set in your current shell environment with **different** values.

The below instructions for Docker and Python assume that you have at least set `NB_GRAPH_USERNAME` and `NB_GRAPH_PASSWORD` in your `.env`.

### Docker
First, [install docker](https://docs.docker.com/get-docker/).

You can then run a Docker container for the API in one of three ways:
#### Option 1 (RECOMMENDED): Use the `docker-compose.yaml` file

First, [install docker compose](https://docs.docker.com/compose/install/).

If needed, update your `.env` file with optional environment variables for the docker compose configuration.

**TIP:** Double check that the environment variables are resolved with your expected values using the command `docker compose config`.

> :information_source: **Note: Deploying the Neurobagel query tool**
>
> When you locally deploy the API with `docker compose`, you will also deploy a local version of the [Neurobagel graphical query tool](https://github.com/neurobagel/query-tool). 
> By default you can reach your local query tool at http://localhost:3000 once it is running.
> Similarly, the `.template-env` file in this repo also assumes you want to allow API requests from a query tool hosted at a specific port on `localhost`.

Use Docker Compose to spin up the containers by running the following in the repository root (where the `docker-compose.yml` file is):
```bash
docker compose up -d
```
If you want to ensure you have the latest images use the command below:

```bash
docker compose pull && docker compose up -d
```

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