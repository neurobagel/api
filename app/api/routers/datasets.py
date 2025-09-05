from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2

from .. import config, crud
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
    request: Request,
    query: QueryModel,
    token: str | None = Depends(oauth2_scheme),
):
    """When a POST request is sent, return list of dicts corresponding to metadata for datasets matching the query."""
    if config.settings.auth_enabled:
        if token is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authenticated",
            )
        verify_token(token)

    response = await crud.query_records(
        **query.model_dump(),
        is_datasets_query=True,
        dataset_uuids=None,
        context=config.CONTEXT,
    )

    return response
