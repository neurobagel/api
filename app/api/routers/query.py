from fastapi import APIRouter, Depends

from .. import crud
from ..models import QueryModel

router = APIRouter(prefix="/query", tags=["query"])


@router.get("/")
async def get_query(query: QueryModel = Depends(QueryModel)):
    """When a GET request is sent, return list of dicts corresponding to subject-level metadata."""
    response = await crud.get(query.sex)
    results = response.json()
    return [
        {k: v["value"] for k, v in res.items()}
        for res in results["results"]["bindings"]
    ]
