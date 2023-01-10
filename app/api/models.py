"""Data models."""

from typing import Literal

from fastapi import Query
from fastapi.exceptions import HTTPException
from pydantic import BaseModel, constr, root_validator


class QueryModel(BaseModel):
    """Data model and dependency for API that stores the query parameters to be accepted and validated."""

    age_min: float = Query(default=None, ge=0)
    age_max: float = Query(default=None, ge=0)
    sex: Literal["male", "female", "other"] = None
    diagnosis: constr(regex=r"^[a-zA-Z]+[:]\S+$") = None
    is_control: bool = None
    min_num_sessions: int = Query(default=None, ge=1)
    image_modal: constr(regex=r"^[a-zA-Z]+[:]\S+$") = None

    @root_validator()
    def check_agemax_ge_agemin(cls, values):
        """
        If both age bounds have been set to values other than their defaults (None), ensure that age_max is >= age_min.
        NOTE: HTTPException (and not ValueError) raised here to get around "Internal Server Error" raised by
        FastAPI when a validation error comes from a Pydantic validator inside a class dependency.
        See:
        https://github.com/tiangolo/fastapi/issues/1474
        https://github.com/tiangolo/fastapi/discussions/3426
        https://fastapi.tiangolo.com/tutorial/handling-errors/?h=validation#requestvalidationerror-vs-validationerror
        """
        amin, amax = values["age_min"], values["age_max"]
        if amin is not None and amax is not None and (amax < amin):
            raise HTTPException(
                status_code=422,
                detail="'age_max' must be greater than or equal to 'age_min'",
            )
        return values

    @root_validator
    def check_exclusive_diagnosis_or_ctrl(cls, values):
        if values["diagnosis"] is not None and values["is_control"]:
            raise HTTPException(
                status_code=422,
                detail="Subjects cannot both be healthy controls and have a diagnosis.",
            )
        return values


class AggDatasetResponse(BaseModel):
    """Data model for query results aggregated at the dataset-level."""

    dataset: str = None
    dataset_name: str = None
    num_matching_subjects: int
