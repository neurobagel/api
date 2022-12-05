"""Define path operations for API."""

from fastapi import FastAPI, Depends
import uvicorn
from .api import crud
from .api.models import QueryModel

app = FastAPI()


@app.get("/query/", tags=["query"])
async def get_query(query: QueryModel = Depends(QueryModel)):
    """When a GET request is sent, return list of dicts corresponding to subject-level metadata."""
    response = await crud.get(query.sex)
    results = response.json()
    return [
        {k: v["value"] for k, v in res.items()}
        for res in results["results"]["bindings"]
    ]


# Automatically start uvicorn server on execution of main.py
if __name__ == "__main__":
    uvicorn.run("app.main:app", port=8000, reload=True)
