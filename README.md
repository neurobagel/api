<div align="center">

# Bagel API

    
<div>
    <a href="https://github.com/neurobagel/bagelapi/actions/workflows/test.yaml">
        <img src="https://img.shields.io/github/actions/workflow/status/neurobagel/bagelapi/test.yaml?color=BDB76B&label=test&style=flat-square">
    </a>
    <a href="https://coveralls.io/github/neurobagel/bagelapi">
        <img src="https://img.shields.io/coverallsCoverage/github/neurobagel/bagelapi?style=flat-square&color=8FBC8F">
    </a>
    <a href="https://www.python.org/">
        <img src="https://img.shields.io/badge/python-3.10-4682B4?style=flat-square" alt="Python">
    </a>
    <a href="LICENSE">
        <img src="https://img.shields.io/github/license/neurobagel/bagelapi?color=CD5C5C&style=flat-square" alt="GitHub license">
    </a>
</div>
<br>

Bagel API is a REST API, developed in [Python](https://www.python.org/) using [FastAPI](https://fastapi.tiangolo.com/) and [pydantic](https://docs.pydantic.dev/).

[Getting started](#getting-started) |
[Testing](#testing) |
[License](#license)

</div>

## Quickstart
The API is hosted at https://api.neurobagel.org/ and interfaces with Neurobagel's graph database. Queries of the graph can be run using the `/query` route.

Interactive documentation for the API is available at https://api.neurobagel.org/docs.

Note: Currently, to access the API, you must be connected to the McGill network.

## Local Installation

### Install Dependencies

You'll need to install the dependencies outlined in the requirements.txt file. For convenience, you can use Python's venv package to install dependencies in a virtual environment. You can find the instructions on creating and activating a virtual environment in the official [documentation](https://docs.python.org/3.10/library/venv.html). After setting up and activating your environment, you can install the dependencies by running the following command in your terminal:

```bash
$ pip install -r requirements.txt
```

### Set the Environment Variables

To run the API, at least two environment variables must be set, `USER` and `PASSWORD`. An optional third environment variable `DOG_ROOT` may be set to use a different IP address for the graph database.

To set environment variables in macOS and Linux distributions use the following command:

```bash
$ export KEY=value

# For example
$ export USER=someuser
```

To set environment variables in Windows from CMD use the following command:

```bash
$ set KEY=value

# For example
$ set USER=someuser
```

### Launch the Bagel API

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

Bagel API utilizes [Pytest](https://docs.pytest.org/en/7.2.x/) framework for testing.

To run the tests first make sure you're in repository's main directory and in your environment where the dependencies are installed and environment variables are set.

You can then run the tests by executing the following command in your terminal:

```bash
pytest tests
```

### License

The Bagel API is released under the terms of the [MIT License](LICENSE)