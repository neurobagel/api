"""Main app."""

import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from .api import utility as util
from .api.routers import query

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
        os.environ.get(util.GRAPH_USERNAME.name) is None
        or os.environ.get(util.GRAPH_PASSWORD.name) is None
    ):
        raise RuntimeError(
            f"The application was launched but could not find the {util.GRAPH_USERNAME.name} and / or {util.GRAPH_PASSWORD.name} environment variables."
        )


app.include_router(query.router)

# Automatically start uvicorn server on execution of main.py
if __name__ == "__main__":
    uvicorn.run("app.main:app", port=8000, reload=True)
