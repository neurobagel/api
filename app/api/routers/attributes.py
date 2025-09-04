from fastapi import APIRouter, Request

from .. import crud

router = APIRouter(prefix="/attributes", tags=["attributes"])


@router.get("", response_model=list)
async def get_attributes(request: Request):
    """When a GET request is sent, return a list of the harmonized controlled term attributes."""
    response = await crud.get_controlled_term_attributes(
        context=request.app.state.context
    )

    return response
