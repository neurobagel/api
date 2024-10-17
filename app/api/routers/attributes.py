from fastapi import APIRouter

from .. import crud

router = APIRouter(prefix="/attributes", tags=["attributes"])


@router.get("/", response_model=list)
async def get_attributes():
    """When a GET request is sent, return a list of the harmonized controlled term attributes."""
    response = await crud.get_controlled_term_attributes()

    return response
