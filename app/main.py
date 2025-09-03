"""Main app."""

import json
import warnings
from contextlib import asynccontextmanager
from pathlib import Path
from tempfile import TemporaryDirectory

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.responses import HTMLResponse, ORJSONResponse, RedirectResponse

from .api import utility as util
from .api.config import Settings, settings
from .api.routers import (
    assessments,
    attributes,
    datasets,
    diagnoses,
    pipelines,
    query,
    subjects,
)
from .api.security import check_client_id

BACKUP_VOCAB_DIR = (
    Path(__file__).absolute().parents[1] / "vocab/backup_external"
)
NEUROBAGEL_CONFIGS_API_URL = (
    "https://api.github.com/repos/neurobagel/communities/contents/configs"
)


def fetch_available_neurobagel_configs(config_dir_url: str) -> list[str]:
    response = util.request_data(
        config_dir_url, "Failed to fetch available Neurobagel configurations."
    )
    config_names = [
        item["name"] for item in response if item.get("type") == "dir"
    ]

    return config_names


def validate_environment_variables():
    """
    Check that all required environment variables are set, and exits the app if any are missing or invalid.
    """
    if settings.graph_username is None or settings.graph_password is None:
        raise RuntimeError(
            f"The application was launched but could not find the {Settings.model_fields['graph_username'].alias} and / or {Settings.model_fields['graph_password'].alias} environment variables."
        )

    if settings.allowed_origins is None:
        warnings.warn(
            f"The API was launched without providing any values for the {Settings.model_fields['allowed_origins'].alias} environment "
            f"variable."
            "This means that the API will only be accessible from the same origin it is hosted from: "
            "https://developer.mozilla.org/en-US/docs/Web/Security/Same-origin_policy."
            f"If you want to access the API from tools hosted at other origins such as the Neurobagel query tool, "
            f"explicitly set the value of {Settings.model_fields['allowed_origins'].alias} to the origin(s) of these tools (e.g. "
            f"http://localhost:3000)."
            "Multiple allowed origins should be separated with spaces in a single string enclosed in quotes."
        )

    available_configs = fetch_available_neurobagel_configs(
        NEUROBAGEL_CONFIGS_API_URL
    )
    if settings.config not in available_configs:
        raise RuntimeError(
            f"'{settings.config}' is not a recognized Neurobagel configuration. "
            f"Available configurations: {', '.join(available_configs)}"
        )


def fetch_vocabularies(configs_url: str, config_name: str):
    customizable_vocab_vars = ["Assessment", "Diagnosis"]
    config_dir_url = f"{configs_url}/{config_name}"

    config = util.request_data(
        f"{config_dir_url}/config.json",
        f"Failed to fetch the {config_name if config_name != 'Neurobagel' else 'base'} configuration for Neurobagel.",
    )
    # TODO: For now we only consider the first entry in config.json since
    # we only support a single namespace for standardized variables (the Neurobagel vocab)
    # - refactor once we support custom standardized variables from potentially >1 namespaces
    config = config[0]

    app.state.vocab_dir = TemporaryDirectory()
    app.state.vocab_dir_path = Path(app.state.vocab_dir.name)
    all_vocab_paths = {}
    for var_id in customizable_vocab_vars:
        var_uri = f"{config['namespace_prefix']}:{var_id}"
        terms_file_name = next(
            (
                var["terms_file"]
                for var in config["standardized_variables"]
                if var["id"] == var_id
            ),
            None,
        )
        if terms_file_name:
            terms_file = util.request_data(
                f"{config_dir_url}/{terms_file_name}",
                f"Failed to fetch vocabulary for {var_uri}.",
            )

            with open(app.state.vocab_dir_path / terms_file_name, "w") as f:
                f.write(json.dumps(terms_file, indent=2))

            all_vocab_paths[var_uri] = (
                app.state.vocab_dir_path / terms_file_name
            )

    app.state.all_vocab_paths = all_vocab_paths


# TODO: Remove function
def initialize_vocabularies():
    """
    Create and store on the app instance a temporary directory for vocabulary term lookup JSON files
    (each of which contain key-value pairings of IDs to human-readable names of terms),
    and then fetch vocabularies using their respective native APIs and save them to the temporary directory for reuse.
    """
    # We use Starlette's ability (FastAPI is Starlette underneath) to store arbitrary state on the app instance (https://www.starlette.io/applications/#storing-state-on-the-app-instance)
    # to store a temporary directory object and its corresponding path. These data are local to the instance and will be recreated on every app launch (i.e. not persisted).

    app.state.vocab_dir = TemporaryDirectory()
    app.state.vocab_dir_path = Path(app.state.vocab_dir.name)

    app.state.vocab_lookup_paths = {
        "snomed_assessment": app.state.vocab_dir_path
        / "snomedct_assessment_term_labels.json",
        "snomed_disorder": app.state.vocab_dir_path
        / "snomedct_disorder_term_labels.json",
    }

    util.reformat_snomed_terms_for_lookup(
        input_terms_path=BACKUP_VOCAB_DIR / "snomedct_assessment.json",
        output_terms_path=app.state.vocab_lookup_paths["snomed_assessment"],
    )
    util.reformat_snomed_terms_for_lookup(
        input_terms_path=BACKUP_VOCAB_DIR / "snomedct_disorder.json",
        output_terms_path=app.state.vocab_lookup_paths["snomed_disorder"],
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events.

    On startup:
    - Validates required environment variables.
    - Performs authentication checks.
    - Initializes temporary directories for vocabulary lookups.

    On shutdown:
    - Cleans up temporary directories to free resources.
    """
    # Validate environment variables
    validate_environment_variables()

    # Authentication check
    check_client_id()

    # Initialize vocabularies
    fetch_vocabularies(NEUROBAGEL_CONFIGS_API_URL, settings.config)

    yield

    # Shutdown logic
    app.state.vocab_dir.cleanup()


app = FastAPI(
    root_path=settings.root_path,
    lifespan=lifespan,
    default_response_class=ORJSONResponse,
    docs_url=None,
    redoc_url=None,
    redirect_slashes=False,
)

favicon_url = "https://raw.githubusercontent.com/neurobagel/documentation/main/docs/imgs/logo/neurobagel_favicon.png"

app.add_middleware(
    CORSMiddleware,
    allow_origins=util.parse_origins_as_list(settings.allowed_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    """
    Display a welcome message and a link to the API documentation.
    """
    return f"""
    <html>
        <body>
            <h1>Welcome to the Neurobagel REST API!</h1>
            <p>Please visit the <a href="{request.scope.get('root_path', '')}/docs">API documentation</a> to view available API endpoints.</p>
        </body>
    </html>
    """


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """
    Overrides the default favicon with a custom one.

    NOTE: When the API is behind a reverse proxy that has a stripped path prefix (and root_path is defined),
    the custom favicon doesn't appear to work correctly for any API paths other than the docs,
    as the path in the favicon request isn't automatically adjusted to include the root path prefix.
    """
    return RedirectResponse(url=favicon_url)


@app.get("/docs", include_in_schema=False)
def overridden_swagger(request: Request):
    """
    Overrides the Swagger UI HTML for the "/docs" endpoint.
    """
    return get_swagger_ui_html(
        openapi_url=f"{request.scope.get('root_path', '')}/openapi.json",
        title="Neurobagel API",
        swagger_favicon_url=favicon_url,
    )


@app.get("/redoc", include_in_schema=False)
def overridden_redoc(request: Request):
    """
    Overrides the Redoc HTML for the "/redoc" endpoint.
    """
    return get_redoc_html(
        openapi_url=f"{request.scope.get('root_path', '')}/openapi.json",
        title="Neurobagel API",
        redoc_favicon_url=favicon_url,
    )


app.include_router(query.router)
app.include_router(datasets.router)
app.include_router(subjects.router)
app.include_router(attributes.router)
app.include_router(assessments.router)
app.include_router(diagnoses.router)
app.include_router(pipelines.router)

# Automatically start uvicorn server on execution of main.py
if __name__ == "__main__":
    uvicorn.run("app.main:app", port=8000, reload=True)
