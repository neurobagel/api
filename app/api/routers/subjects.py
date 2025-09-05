from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2

from .. import config, crud
from ..models import SubjectsQueryModel, SubjectsQueryResponse
from ..security import verify_token

router = APIRouter(prefix="/subjects", tags=["subjects"])

oauth2_scheme = OAuth2(
    flows={
        "implicit": {
            "authorizationUrl": "https://neurobagel.ca.auth0.com/authorize",
        }
    },
    # Don't automatically error out when request is not authenticated, to support optional authentication
    auto_error=False,
)


@router.post("", response_model=List[SubjectsQueryResponse])
async def post_subjects_query(
    request: Request,
    query: SubjectsQueryModel,
    token: str | None = Depends(oauth2_scheme),
):
    """When a POST request is sent, return list of dicts corresponding to (meta)data of subject-sessions matching the query, grouped by dataset."""
    if config.settings.auth_enabled:
        if token is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authenticated",
            )
        verify_token(token)

    response = await crud.query_records(
        **query.model_dump(),
        is_datasets_query=False,
        context=config.CONTEXT,
    )

    return response
