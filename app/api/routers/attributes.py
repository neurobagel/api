from fastapi import APIRouter

from .. import crud

router = APIRouter(prefix="/attributes", tags=["attributes"])


@router.get("", response_model=list)
async def get_attributes():
    """When a GET request is sent, return a list of the harmonized standardized variable attributes."""
    response = await crud.get_standardized_variables()

    return response
