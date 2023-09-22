"""Router for query path operations."""

from typing import List

from fastapi import APIRouter, Depends

from .. import crud
from ..models import CohortQueryResponse, QueryModel

router = APIRouter(prefix="/query", tags=["query"])


@router.get("/", response_model=List[CohortQueryResponse])
async def get_query(query: QueryModel = Depends(QueryModel)):
    """When a GET request is sent, return list of dicts corresponding to subject-level metadata aggregated by dataset."""
    response = await crud.get(
        query.min_age,
        query.max_age,
        query.sex,
        query.diagnosis,
        query.is_control,
        query.min_num_sessions,
        query.assessment,
        query.image_modal,
    )

    return response


@router.get("/attributes/{attribute_URI}")
async def get_terms(attribute_URI: str):
    """When a GET request is sent, return a dict with the only key corresponding to controlled term of a neurobagel class and value corresponding to all the available terms."""
    response = await crud.get_terms(attribute_URI)

    return response
