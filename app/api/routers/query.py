"""Router for query path operations."""

from typing import List

from fastapi import APIRouter, Depends
from pydantic import constr

from .. import crud
from ..models import CONTROLLED_TERM_REGEX, CohortQueryResponse, QueryModel

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


@router.get("/attributes/{data_element_URI}")
async def get_terms(data_element_URI: constr(regex=CONTROLLED_TERM_REGEX)):
    """When a GET request is sent, return a dict with the only key corresponding to controlled term of a neurobagel class and value corresponding to all the available terms."""
    response = await crud.get_terms(data_element_URI)

    return response
