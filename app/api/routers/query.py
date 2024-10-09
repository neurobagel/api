"""Router for query path operations."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2

from .. import crud, security
from ..models import CohortQueryResponse, QueryModel
from ..security import verify_token

router = APIRouter(prefix="/query", tags=["query"])

# Adapted from info in https://github.com/tiangolo/fastapi/discussions/9137#discussioncomment-5157382
oauth2_scheme = OAuth2(
    flows={
        "implicit": {
            "authorizationUrl": "https://accounts.google.com/o/oauth2/auth",
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
@router.get("", response_model=List[CohortQueryResponse])
async def get_query(
    query: QueryModel = Depends(QueryModel),
    token: str | None = Depends(oauth2_scheme),
):
    """When a GET request is sent, return list of dicts corresponding to subject-level metadata aggregated by dataset."""
    if security.AUTH_ENABLED:
        if token is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authenticated",
            )
        verify_token(token)

    response = await crud.get(
        query.min_age,
        query.max_age,
        query.sex,
        query.diagnosis,
        query.is_control,
        query.min_num_imaging_sessions,
        query.min_num_phenotypic_sessions,
        query.assessment,
        query.image_modal,
        query.pipeline_name,
        query.pipeline_version,
    )

    return response
