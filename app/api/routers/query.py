"""Router for query path operations."""

from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2

from .. import crud
from ..config import settings
from ..models import QueryModel, SubjectsQueryResponse
from ..security import verify_token

router = APIRouter(prefix="/query", tags=["query"])

# Adapted from info in https://github.com/tiangolo/fastapi/discussions/9137#discussioncomment-5157382
# I believe for us this is purely for documentatation/a nice looking interactive API docs page,
# and doesn't actually have any bearing on the ID token validation process.
oauth2_scheme = OAuth2(
    flows={
        "implicit": {
            "authorizationUrl": "https://neurobagel.ca.auth0.com/authorize",
        }
    },
    # Don't automatically error out when request is not authenticated, to support optional authentication
    auto_error=False,
)


# We (unconventionally) use an "" path prefix here because we have globally disabled
# redirection of trailing slashes in the main app file. We use an empty string here
# to ensure that a request without a trailing slash (e.g., to /query instead of /query/)
# is correctly routed to this endpoint.
# For more context, see https://github.com/neurobagel/api/issues/327.
@router.get("", response_model=List[SubjectsQueryResponse])
async def get_query(
    query: Annotated[QueryModel, Query()],
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

    # TODO: See if we can pass the query object directly to crud.query_records() instead of unpacking it
    response = await crud.query_records(
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
        is_datasets_query=False,
    )

    return response
