"""Main app."""

import os
import warnings
from pathlib import Path
from tempfile import TemporaryDirectory
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.responses import HTMLResponse, ORJSONResponse, RedirectResponse

from app.api import utility as util
from app.api.routers import assessments, attributes, diagnoses, pipelines, query
from app.api.security import check_client_id


def validate_environment_variables():
    """Validate required environment variables."""
    if os.environ.get(util.GRAPH_USERNAME.name) is None or os.environ.get(util.GRAPH_PASSWORD.name) is None:
        raise RuntimeError(
            f"The application was launched but could not find the {util.GRAPH_USERNAME.name} and/or {util.GRAPH_PASSWORD.name} environment variables."
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown logic."""
    try:
        # Validate environment variables
        validate_environment_variables()

        # Authentication check
        check_client_id()

        # Create and store temporary directories
        app.state.vocab_dir = TemporaryDirectory()
        app.state.vocab_dir_path = Path(app.state.vocab_dir.name)

        app.state.vocab_lookup_paths = {
            "snomed_assessment": app.state.vocab_dir_path / "snomedct_assessment_term_labels.json",
            "snomed_disorder": app.state.vocab_dir_path / "snomedct_disorder_term_labels.json"
        }

        # Create vocabulary lookups
        util.create_snomed_assessment_lookup(app.state.vocab_lookup_paths["snomed_assessment"])
        util.create_snomed_disorder_lookup(app.state.vocab_lookup_paths["snomed_disorder"])

    except Exception as e:
        raise RuntimeError(f"Startup failed: {str(e)}")

    yield

    # Shutdown logic
    try:
        app.state.vocab_dir.cleanup()
    except Exception as e:
        warnings.warn(f"Failed to clean up temporary directory: {str(e)}")


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
    return f"""
    <html>
        <body>
            <h1>Welcome to the Neurobagel REST API!</h1>
            <p>Please visit the <a href="{request.scope.get('root_path', '')}/docs">API documentation</a> to view 
            available API endpoints.</p> </body> </html>"""


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return RedirectResponse(url=favicon_url)


@app.get("/docs", include_in_schema=False)
def overridden_swagger(request: Request):
    return get_swagger_ui_html(
        openapi_url=f"{request.scope.get('root_path', '')}/openapi.json",
        title="Neurobagel API",
        swagger_favicon_url=favicon_url,
    )


@app.get("/redoc", include_in_schema=False)
def overridden_redoc(request: Request):
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

if __name__ == "__main__":
    uvicorn.run("app.main:app", port=8000, reload=True)
