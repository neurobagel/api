"""Router for query path operations."""

from typing import List

from fastapi import APIRouter, Depends

from .. import crud
from ..models import AggDatasetResponse, QueryModel

router = APIRouter(prefix="/query", tags=["query"])


@router.get("/", response_model=List[AggDatasetResponse])
async def get_query(query: QueryModel = Depends(QueryModel)):
    """When a GET request is sent, return list of dicts corresponding to subject-level metadata aggregated by dataset."""
    response = await crud.get(
        query.age_min,
        query.age_max,
        query.sex,
        query.diagnosis,
        query.is_control,
        query.min_num_sessions,
        query.image_modal,
    )

    return response
