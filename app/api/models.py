"""Data models."""

from typing import Optional

from fastapi import Query
from fastapi.exceptions import HTTPException
from pydantic import BaseModel, constr, root_validator

CONTROLLED_TERM_REGEX = r"^[a-zA-Z]+[:]\S+$"


class QueryModel(BaseModel):
    """Data model and dependency for API that stores the query parameters to be accepted and validated."""

    min_age: float = Query(default=None, ge=0)
    max_age: float = Query(default=None, ge=0)
    sex: constr(regex=CONTROLLED_TERM_REGEX) = None
    diagnosis: constr(regex=CONTROLLED_TERM_REGEX) = None
    is_control: bool = None
    min_num_sessions: int = Query(default=None, ge=1)
    assessment: constr(regex=CONTROLLED_TERM_REGEX) = None
    image_modal: constr(regex=CONTROLLED_TERM_REGEX) = None

    @root_validator()
    def check_maxage_ge_minage(cls, values):
        """
        If both age bounds have been set to values other than their defaults (None), ensure that max_age is >= min_age.
        NOTE: HTTPException (and not ValueError) raised here to get around "Internal Server Error" raised by
        FastAPI when a validation error comes from a Pydantic validator inside a class dependency.
        See:
        https://github.com/tiangolo/fastapi/issues/1474
        https://github.com/tiangolo/fastapi/discussions/3426
        https://fastapi.tiangolo.com/tutorial/handling-errors/?h=validation#requestvalidationerror-vs-validationerror
        """
        mina, maxa = values["min_age"], values["max_age"]
        if mina is not None and maxa is not None and (maxa < mina):
            raise HTTPException(
                status_code=422,
                detail="'max_age' must be greater than or equal to 'min_age'",
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


class CohortQueryResponse(BaseModel):
    """Data model for query results for one matching dataset (i.e., a cohort)."""

    dataset_uuid: str
    # dataset_file_path: str  # TODO: Revisit this field once we have datasets without imaging info/sessions.
    dataset_name: str
    dataset_portal_uri: Optional[str]
    num_matching_subjects: int
    subject_data: list
    image_modals: list
