from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2

from .. import crud
from ..env_settings import settings
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
    """When a POST request is sent, return list of dicts corresponding to metadata for datasets matching the query."""
    if settings.auth_enabled:
        if token is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authenticated",
            )
        verify_token(token)

    response = await crud.post_datasets(query)

    return response
