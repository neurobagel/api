"""Main app."""

from contextlib import asynccontextmanager
import os
import warnings
from pathlib import Path
from tempfile import TemporaryDirectory

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.responses import ORJSONResponse, RedirectResponse

from .api import utility as util
from .api.routers import attributes, query

app = FastAPI(
    default_response_class=ORJSONResponse, docs_url=None, redoc_url=None
)
favicon_url = "https://raw.githubusercontent.com/neurobagel/documentation/main/docs/imgs/logo/neurobagel_favicon.png"

app.add_middleware(
    CORSMiddleware,
    allow_origins=util.parse_origins_as_list(util.ALLOWED_ORIGINS.val),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Load and set up resources before the application starts receiving requests.
    Clean up resources after the application finishes handling requests.
    """
    # to store a temporary directory object and its corresponding path. These data are local to the instance and will be recreated on every app launch (i.e. not persisted).
    vocab_dir = TemporaryDirectory()  
    try:
        # Check if username and password environment variables are set
        if (
            # TODO: Check if this error is still raised when variables are empty strings
            os.environ.get(util.GRAPH_USERNAME.name) is None
            or os.environ.get(util.GRAPH_PASSWORD.name) is None
        ):
            raise RuntimeError(
                f"The application was launched but could not find the {util.GRAPH_USERNAME.name} and / or {util.GRAPH_PASSWORD.name} environment variables."
            )

        # Raises warning if allowed origins environment variable has not been set or is an empty string.
        if os.environ.get(util.ALLOWED_ORIGINS.name, "") == "":
            warnings.warn(
                f"The API was launched without providing any values for the {util.ALLOWED_ORIGINS.name} environment variable. "
                "This means that the API will only be accessible from the same origin it is hosted from: https://developer.mozilla.org/en-US/docs/Web/Security/Same-origin_policy. "
                f"If you want to access the API from tools hosted at other origins such as the Neurobagel query tool, explicitly set the value of {util.ALLOWED_ORIGINS.name} to the origin(s) of these tools (e.g. http://localhost:3000). "
                "Multiple allowed origins should be separated with spaces in a single string enclosed in quotes. "
            )

        # Fetch and store vocabularies to a temporary directory
        # We use Starlette's ability (FastAPI is Starlette underneath) to store arbitrary state on the app instance (https://www.starlette.io/applications/#storing-state-on-the-app-instance)
        vocab_dir_path = Path(vocab_dir.name)

        # TODO: Maybe store these paths in one dictionary on the app instance instead of separate variables?
        app.cogatlas_term_lookup_path = (
            vocab_dir_path / "cogatlas_task_term_labels.json"
        )
        app.snomed_term_lookup_path = (
            vocab_dir_path / "snomedct_disorder_term_labels.json"
        )

        util.fetch_and_save_cogatlas(app.cogatlas_term_lookup_path)
        util.create_snomed_term_lookup(app.snomed_term_lookup_path)

        yield
    finally:
        # Clean up the temporary directory created on startup
        vocab_dir.cleanup()


app.include_router(query.router)
app.include_router(attributes.router)

# Automatically start uvicorn server on execution of main.py
if __name__ == "__main__":
    uvicorn.run("app.main:app", port=8000, reload=True)
