from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .. import crud
from ..database import get_session

router = APIRouter(prefix="/attributes", tags=["attributes"])


@router.get("", response_model=list)
async def get_attributes(db_session: AsyncSession = Depends(get_session)):
    """When a GET request is sent, return a list of the harmonized controlled term attributes."""
    response = await crud.get_controlled_term_attributes(db_session)

    return response
