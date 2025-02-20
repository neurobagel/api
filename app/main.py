"""Main app."""

import os
import warnings
from contextlib import asynccontextmanager
from pathlib import Path
from tempfile import TemporaryDirectory

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.responses import HTMLResponse, ORJSONResponse, RedirectResponse

from app.api import utility as util
from app.api.routers import (
    assessments,
    attributes,
    diagnoses,
    pipelines,
    query,
)
from app.api.security import check_client_id


def validate_environment_variables():
    """
    Check that all required environment variables are set.

    Ensures that the username and password for the graph database are provided.
    If not, raises a RuntimeError to prevent the application from running without valid credentials.

    Also checks that ALLOWED_ORIGINS is properly set. If missing, a warning is issued, but the app continues running.
    """
    if (
        os.environ.get(util.GRAPH_USERNAME.name) is None
        or os.environ.get(util.GRAPH_PASSWORD.name) is None
    ):
        raise RuntimeError(
            f"The application was launched but could not find the {util.GRAPH_USERNAME.name} and / or {util.GRAPH_PASSWORD.name} environment variables."
        )

    if os.environ.get(util.ALLOWED_ORIGINS.name, "") == "":
        warnings.warn(
            f"The API was launched without providing any values for the {util.ALLOWED_ORIGINS.name} environment "
            f"variable."
            "This means that the API will only be accessible from the same origin it is hosted from: "
            "https://developer.mozilla.org/en-US/docs/Web/Security/Same-origin_policy."
            f"If you want to access the API from tools hosted at other origins such as the Neurobagel query tool, "
            f"explicitly set the value of {util.ALLOWED_ORIGINS.name} to the origin(s) of these tools (e.g. "
            f"http://localhost:3000)."
            "Multiple allowed origins should be separated with spaces in a single string enclosed in quotes."
        )


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

    util.create_snomed_assessment_lookup(
        app.state.vocab_lookup_paths["snomed_assessment"]
    )
    util.create_snomed_disorder_lookup(
        app.state.vocab_lookup_paths["snomed_disorder"]
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
    initialize_vocabularies()

    yield

    # Shutdown logic
    app.state.vocab_dir.cleanup()


app = FastAPI(
    root_path=util.ROOT_PATH.val,
    lifespan=lifespan,
    default_response_class=ORJSONResponse,
    docs_url=None,
    redoc_url=None,
    redirect_slashes=False,
)

favicon_url = "https://raw.githubusercontent.com/neurobagel/documentation/main/docs/imgs/logo/neurobagel_favicon.png"

app.add_middleware(
    CORSMiddleware,
    allow_origins=util.parse_origins_as_list(util.ALLOWED_ORIGINS.val),
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
            <p>Please visit the <a href="{request.scope.get('root_path', '')}/docs">API documentation</a> to view
            available API endpoints.</p> </body> </html>"""


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
app.include_router(attributes.router)
app.include_router(assessments.router)
app.include_router(diagnoses.router)
app.include_router(pipelines.router)

# Automatically start uvicorn server on execution of main.py
if __name__ == "__main__":
    uvicorn.run("app.main:app", port=8000, reload=True)
