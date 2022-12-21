"""Router for query path operations."""

from fastapi import APIRouter, Depends

from .. import crud
from ..models import QueryModel

router = APIRouter(prefix="/query", tags=["query"])


@router.get("/")
async def get_query(query: QueryModel = Depends(QueryModel)):
    """When a GET request is sent, return list of dicts corresponding to subject-level metadata."""
    response = await crud.get(
        query.age_min,
        query.age_max,
        query.sex,
        query.diagnosis,
        query.is_control,
        query.image_modal,
    )

    return response
