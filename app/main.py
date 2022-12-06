"""Define path operations for API."""

import os

import uvicorn
from fastapi import FastAPI

from .api.routers import query

app = FastAPI()


@app.on_event("startup")
async def auth_check():
    if os.environ.get("USER") is None or os.environ.get("PASSWORD") is None:
        raise RuntimeError(
            "The application was launched but could not find the USER and / or PASSWORD environment variables."
        )


app.include_router(query.router)

# Automatically start uvicorn server on execution of main.py
if __name__ == "__main__":
    uvicorn.run("app.main:app", port=8000, reload=True)
