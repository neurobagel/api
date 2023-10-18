"""Main app."""

import os
import warnings
from pathlib import Path
from tempfile import TemporaryDirectory

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from .api import utility as util
from .api.routers import attributes, query

app = FastAPI(default_response_class=ORJSONResponse)

app.add_middleware(
    CORSMiddleware,
    allow_origins=util.parse_origins_as_list(util.ALLOWED_ORIGINS.val),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def auth_check():
    """Checks whether username and password environment variables are set."""
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
    Create and store on the app instance a temporary directory for vocabulary term lookup files,
    and then fetch vocabularies using their respective native APIs and save them to the temporary directory for reuse.
    """
    # We use Starlette's ability (FastAPI is Starlette underneath) to store arbitrary state on the app instance (https://www.starlette.io/applications/#storing-state-on-the-app-instance)
    # to store a temporary directory object and its corresponding path. These data are local to the instance and will be recreated on every app launch (i.e. not persisted).
    app.state.vocab_dir = TemporaryDirectory()
    app.state.vocab_dir_path = Path(app.state.vocab_dir.name)

    app.state.cogatlas_term_lookup_path = (
        app.state.vocab_dir_path / "cogatlas_task_term_labels.json"
    )

    util.fetch_and_save_cogatlas(app.state.cogatlas_term_lookup_path)


@app.on_event("shutdown")
async def cleanup_temp_vocab_dir():
    """Clean up the temporary directory created on startup."""
    app.state.vocab_dir.cleanup()


app.include_router(query.router)
app.include_router(attributes.router)

# Automatically start uvicorn server on execution of main.py
if __name__ == "__main__":
    uvicorn.run("app.main:app", port=8000, reload=True)
