"""Data models."""

from typing import Literal

from pydantic import BaseModel


class QueryModel(BaseModel):
    """Data model and dependency for API that stores the query parameters to be accepted and validated."""

    sex: Literal["male", "female", "other"] = None
    age_min: float = None
    age_max: float = None
