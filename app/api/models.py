"""Data models."""

from enum import Enum
from typing import Optional, Union

from fastapi import Query
from fastapi.exceptions import HTTPException
from pydantic import BaseModel, constr, root_validator

CONTROLLED_TERM_REGEX = r"^[a-zA-Z]+[:]\S+$"
VERSION_REGEX = r"^([A-Za-z0-9-]+)\.(\d+)\.([A-Za-z0-9-]+)$"


class QueryModel(BaseModel):
    """Data model and dependency for API that stores the query parameters to be accepted and validated."""

    min_age: float = Query(default=None, ge=0)
    max_age: float = Query(default=None, ge=0)
    sex: constr(regex=CONTROLLED_TERM_REGEX) = None
    diagnosis: constr(regex=CONTROLLED_TERM_REGEX) = None
    is_control: bool = None
    min_num_imaging_sessions: int = Query(default=None, ge=0)
    min_num_phenotypic_sessions: int = Query(default=None, ge=0)
    assessment: constr(regex=CONTROLLED_TERM_REGEX) = None
    image_modal: constr(regex=CONTROLLED_TERM_REGEX) = None
    pipeline_name: constr(regex=CONTROLLED_TERM_REGEX) = None
    # TODO: Check back if validating using a regex is too restrictive
    pipeline_version: constr(regex=VERSION_REGEX) = None

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


class SessionResponse(BaseModel):
    """Data model for a single session available for a matching subject."""

    sub_id: str
    session_id: str
    num_matching_phenotypic_sessions: int
    num_matching_imaging_sessions: int
    session_type: str
    age: Optional[float]
    sex: Optional[str]
    diagnosis: list
    subject_group: Optional[str]
    assessment: list
    image_modal: list
    session_file_path: Optional[str]
    completed_pipelines: dict


class CohortQueryResponse(BaseModel):
    """Data model for query results for one matching dataset (i.e., a cohort)."""

    dataset_uuid: str
    # dataset_file_path: str  # TODO: Revisit this field once we have datasets without imaging info/sessions.
    dataset_name: str
    dataset_portal_uri: Optional[str]
    dataset_total_subjects: int
    records_protected: bool
    num_matching_subjects: int
    subject_data: Union[list[SessionResponse], str]
    image_modals: list
    available_pipelines: dict


class DataElementURI(str, Enum):
    """Data model for data element URIs that have available vocabulary lookups."""

    assessment = "nb:Assessment"
    diagnosis = "nb:Diagnosis"


class VocabLabelsResponse(BaseModel):
    """Data model for response to a request for all term labels for a vocabulary."""

    vocabulary_name: str
    namespace_url: str
    namespace_prefix: str
    term_labels: dict
