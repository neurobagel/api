"""Main app."""

import os
import warnings
from pathlib import Path
from tempfile import TemporaryDirectory

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.responses import HTMLResponse, ORJSONResponse, RedirectResponse

from .api import utility as util
from .api.routers import assessments, attributes, diagnoses, pipelines, query
from .api.security import check_client_id

app = FastAPI(
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
def root():
    """
    Display a welcome message and a link to the API documentation.
    """
    return """
    <html>
        <body>
            <h1>Welcome to the Neurobagel REST API!</h1>
            <p>Please visit the <a href="/docs">documentation</a> to view available API endpoints.</p>
        </body>
    </html>
    """


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """
    Overrides the default favicon with a custom one.
    """
    return RedirectResponse(url=favicon_url)


@app.get("/docs", include_in_schema=False)
def overridden_swagger():
    """
    Overrides the Swagger UI HTML for the "/docs" endpoint.
    """
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="Neurobagel API",
        swagger_favicon_url=favicon_url,
    )


@app.get("/redoc", include_in_schema=False)
def overridden_redoc():
    """
    Overrides the Redoc HTML for the "/redoc" endpoint.
    """
    return get_redoc_html(
        openapi_url="/openapi.json",
        title="Neurobagel API",
        redoc_favicon_url=favicon_url,
    )


@app.on_event("startup")
async def auth_check():
    """
    Checks whether authentication has been enabled for API queries and whether the
    username and password environment variables for the graph backend have been set.

    TODO: Refactor once startup events have been replaced by lifespan event
    """
    check_client_id()

    if (
        # TODO: Check if this error is still raised when variables are empty strings
        os.environ.get(util.GRAPH_USERNAME.name) is None
        or os.environ.get(util.GRAPH_PASSWORD.name) is None
    ):
        raise RuntimeError(
            f"The application was launched but could not find the {util.GRAPH_USERNAME.name} and / or {util.GRAPH_PASSWORD.name} environment variables."
        )


@app.on_event("startup")
async def allowed_origins_check():
    """Raises warning if allowed origins environment variable has not been set or is an empty string."""
    if os.environ.get(util.ALLOWED_ORIGINS.name, "") == "":
        warnings.warn(
            f"The API was launched without providing any values for the {util.ALLOWED_ORIGINS.name} environment variable. "
            "This means that the API will only be accessible from the same origin it is hosted from: https://developer.mozilla.org/en-US/docs/Web/Security/Same-origin_policy. "
            f"If you want to access the API from tools hosted at other origins such as the Neurobagel query tool, explicitly set the value of {util.ALLOWED_ORIGINS.name} to the origin(s) of these tools (e.g. http://localhost:3000). "
            "Multiple allowed origins should be separated with spaces in a single string enclosed in quotes. "
        )


@app.on_event("startup")
async def fetch_vocabularies_to_temp_dir():
    """
    Create and store on the app instance a temporary directory for vocabulary term lookup JSON files
    (each of which contain key-value pairings of IDs to human-readable names of terms),
    and then fetch vocabularies using their respective native APIs and save them to the temporary directory for reuse.
    """
    # We use Starlette's ability (FastAPI is Starlette underneath) to store arbitrary state on the app instance (https://www.starlette.io/applications/#storing-state-on-the-app-instance)
    # to store a temporary directory object and its corresponding path. These data are local to the instance and will be recreated on every app launch (i.e. not persisted).
    app.state.vocab_dir = TemporaryDirectory()
    app.state.vocab_dir_path = Path(app.state.vocab_dir.name)

    app.state.vocab_lookup_paths = {}
    app.state.vocab_lookup_paths["cogatlas"] = (
        app.state.vocab_dir_path / "cogatlas_task_term_labels.json"
    )
    app.state.vocab_lookup_paths["snomed"] = (
        app.state.vocab_dir_path / "snomedct_disorder_term_labels.json"
    )

    util.fetch_and_save_cogatlas(app.state.vocab_lookup_paths["cogatlas"])
    util.create_snomed_term_lookup(app.state.vocab_lookup_paths["snomed"])


@app.on_event("shutdown")
async def cleanup_temp_vocab_dir():
    """Clean up the temporary directory created on startup."""
    app.state.vocab_dir.cleanup()


app.include_router(query.router)
app.include_router(attributes.router)
app.include_router(assessments.router)
app.include_router(diagnoses.router)
app.include_router(pipelines.router)

# Automatically start uvicorn server on execution of main.py
if __name__ == "__main__":
    uvicorn.run("app.main:app", port=8000, reload=True)
