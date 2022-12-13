"""Data models."""

from typing import Literal

from fastapi import Query
from fastapi.exceptions import HTTPException
from pydantic import BaseModel, root_validator


class QueryModel(BaseModel):
    """Data model and dependency for API that stores the query parameters to be accepted and validated."""

    sex: Literal["male", "female", "other"] = None
    age_min: float = Query(default=None, gt=0)
    age_max: float = Query(default=None, gt=0)

    @root_validator()
    def check_age_range(cls, v):
        if (None not in [v.get("age_min"), v.get("age_max")]) and (
            v.get("age_min") > v.get("age_max")
        ):
            raise HTTPException(
                status_code=422,
                detail="'age_max' must be greater than or equal to 'age_min'",
            )
        return v
