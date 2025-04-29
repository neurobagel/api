from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2

from .. import crud
from ..config import settings
from ..models import DatasetQueryResponse, QueryModel
from ..security import verify_token

router = APIRouter(prefix="/datasets", tags=["datasets"])

oauth2_scheme = OAuth2(
    flows={
        "implicit": {
            "authorizationUrl": "https://neurobagel.ca.auth0.com/authorize",
        }
    },
    # Don't automatically error out when request is not authenticated, to support optional authentication
    auto_error=False,
)


@router.post("", response_model=List[DatasetQueryResponse])
async def post_datasets_query(
    query: QueryModel,
    token: str | None = Depends(oauth2_scheme),
):
    """When a GET request is sent, return list of dicts corresponding to subject-level metadata aggregated by dataset."""
    if settings.auth_enabled:
        if token is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authenticated",
            )
        verify_token(token)

    # TODO: See if we can pass the query object directly to crud.get() instead of unpacking it
    response = await crud.get(
        min_age=query.min_age,
        max_age=query.max_age,
        sex=query.sex,
        diagnosis=query.diagnosis,
        is_control=query.is_control,
        min_num_imaging_sessions=query.min_num_imaging_sessions,
        min_num_phenotypic_sessions=query.min_num_phenotypic_sessions,
        assessment=query.assessment,
        image_modal=query.image_modal,
        pipeline_name=query.pipeline_name,
        pipeline_version=query.pipeline_version,
        is_datasets_query=True,
    )

    return response
