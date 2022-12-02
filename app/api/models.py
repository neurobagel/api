from enum import Enum
from fastapi import Query


class sexEnum(Enum):
    """Sex query parameter as an Enum to be accepted and validated as an Enum."""

    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    NONE = ""


class NBQuery:
    """Dependency for API that stores the query parameters to be accepted and validated."""

    def __init__(self, sex: sexEnum = Query(sexEnum.NONE)):
        self.sex = sex
