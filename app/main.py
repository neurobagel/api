"""Main app."""

import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from .api.routers import query

app = FastAPI(default_response_class=ORJSONResponse)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def auth_check():
    """Checks whether USERNAME and PASSWORD environment variables are set."""
    if (
        os.environ.get("USERNAME") is None
        or os.environ.get("PASSWORD") is None
    ):
        raise RuntimeError(
            "The application was launched but could not find the USERNAME and / or PASSWORD environment variables."
        )


app.include_router(query.router)

# Automatically start uvicorn server on execution of main.py
if __name__ == "__main__":
    uvicorn.run("app.main:app", port=8000, reload=True)
