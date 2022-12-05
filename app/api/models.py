from pydantic import BaseModel
from typing import Literal


class QueryModel(BaseModel):
    sex: Literal[
        "male", "female", "other"
    ] = None  # Field(["male", "female", "others"])
