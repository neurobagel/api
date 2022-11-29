"""Define path operations for API."""

from fastapi import FastAPI, Depends, HTTPException
from fastapi import Query
import uvicorn
from .api import crud

app = FastAPI()


class NBQuery:
    """Dependency for API that stores the query parameters to be accepted and validated."""

    def __init__(
        self, sex: str = Query(default=None, min_length=4, max_length=6)
    ):
        self.sex = sex


@app.get("/query/")
async def get_query(query: NBQuery = Depends(NBQuery)):
    """When a GET request is sent, return list of dicts corresponding to subject-level metadata."""
    if query.sex in ["male", "female", None]:
        response = await crud.get(query.sex)
        results = response.json()
        return [
            {k: v["value"] for k, v in res.items()}
            for res in results["results"]["bindings"]
        ]

    raise HTTPException(
        status_code=422, detail=f"{query.sex} is not a valid sex"
    )


if __name__ == "__main__":
    uvicorn.run("app.main:app", port=8000, reload=True)
