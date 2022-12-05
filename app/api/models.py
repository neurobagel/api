from pydantic import BaseModel
from typing import Literal


class QueryModel(BaseModel):
    """Data model and dependency for API that stores the query parameters to be accepted and validated."""

    sex: Literal["male", "female", "other"] = None
