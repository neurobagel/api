"""Data models."""

from enum import Enum
from typing import Annotated, Any, Literal, Optional, Union

from fastapi.exceptions import HTTPException
from pydantic import (
    BaseModel,
    BeforeValidator,
    Field,
    RootModel,
    model_validator,
)
from typing_extensions import Self

CONTROLLED_TERM_REGEX = r"^[a-zA-Z]+[:]\S+$"

# TODO: Check if version regex is too restrictive
# Constrain version numbers to be in the following format:
# Exactly three dot-separated segments, where the first and third segments can be letters, numbers, or hyphens (at least one character each),
# and the middle segment must be purely digits (one or more).
VERSION_REGEX = r"^([A-Za-z0-9-]+)\.(\d+)\.([A-Za-z0-9-]+)$"


def convert_valid_is_control_values_to_bool(
    value: Any,
) -> Optional[bool]:
    """
    Ensure that allowed values for the 'is_control' query parameter are converted to boolean True.

    Accept:
      - None → returns None
      - any-case "true" (string) → returns True
      - boolean True → returns True

    Otherwise raise a validation error.
    """
    if value is None:
        return None
    if (isinstance(value, str) and value.lower() == "true") or value is True:
        return True
    raise HTTPException(
        status_code=422,
        detail="'is_control' must be either set to 'true' or omitted from the query",
    )


# TODO: Consider renaming to DatasetsQueryModel once we deprecate the /query endpoint
class QueryModel(BaseModel):
    """Data model and dependency for API that stores the query parameters to be accepted and validated."""

    # NOTE: extra query parameters are just ignored/have no effect
    # NOTE: Explicit examples are needed for fields requiring a URI to avoid random-string examples being generated
    # for the example request body in the interactive docs

    min_age: float = Field(default=None, ge=0)
    max_age: float = Field(default=None, ge=0)
    sex: str = Field(
        default=None, pattern=CONTROLLED_TERM_REGEX, examples=["vocab:12345"]
    )
    diagnosis: str = Field(
        default=None, pattern=CONTROLLED_TERM_REGEX, examples=["vocab:12345"]
    )
    # We explicitly use None instead of True as the example value for is_control to ensure that
    # if a user tries the example query provided in the interactive docs, they do not
    # get an error about both diagnosis and is_control being set
    is_control: Annotated[
        Literal[True, None],
        BeforeValidator(convert_valid_is_control_values_to_bool),
        Field(default=None, examples=[None]),
    ]
    min_num_imaging_sessions: int = Field(default=None, ge=0)
    min_num_phenotypic_sessions: int = Field(default=None, ge=0)
    assessment: str = Field(
        default=None, pattern=CONTROLLED_TERM_REGEX, examples=["vocab:12345"]
    )
    image_modal: str = Field(
        default=None, pattern=CONTROLLED_TERM_REGEX, examples=["vocab:12345"]
    )
    pipeline_name: str = Field(
        default=None, pattern=CONTROLLED_TERM_REGEX, examples=["vocab:12345"]
    )
    pipeline_version: str = Field(
        default=None, pattern=VERSION_REGEX, examples=["1.0.0"]
    )

    @model_validator(mode="after")
    def check_maxage_ge_minage(self) -> Self:
        """
        If both age bounds have been set to values other than their defaults (None), ensure that max_age is >= min_age.
        NOTE: HTTPException (and not ValueError) raised here to get around "Internal Server Error" raised by
        FastAPI when a validation error comes from a Pydantic validator inside a class dependency.
        See:
        https://github.com/tiangolo/fastapi/issues/1474
        https://github.com/tiangolo/fastapi/discussions/3426
        https://fastapi.tiangolo.com/tutorial/handling-errors/?h=validation#requestvalidationerror-vs-validationerror
        """
        if (
            self.min_age is not None
            and self.max_age is not None
            and (self.max_age < self.min_age)
        ):
            raise HTTPException(
                status_code=422,
                detail="'max_age' must be greater than or equal to 'min_age'",
            )
        return self

    @model_validator(mode="after")
    def check_exclusive_diagnosis_or_ctrl(self) -> Self:
        """Raise an error when a subject has both a diagnosis and is a control."""
        if self.diagnosis is not None and self.is_control:
            raise HTTPException(
                status_code=422,
                detail="Subjects cannot both be healthy controls and have a diagnosis.",
            )
        return self


class SubjectsQueryModel(QueryModel):
    # TODO: At the moment datasets always appears as the last field, after all other query parameters.
    # Revisit if we want to modify the order.
    # TODO: If we want to restrict the format of UUIDs further, we could use AnyURL or AnyHttpUrl
    dataset_uuids: list[str] | None = None


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


class DatasetQueryResponse(BaseModel):
    """Data model for metadata of datasets matching a query."""

    dataset_uuid: str
    # dataset_file_path: str  # TODO: Revisit this field once we have datasets without imaging info/sessions.
    dataset_name: str
    dataset_portal_uri: Optional[str]
    dataset_total_subjects: int
    records_protected: bool
    num_matching_subjects: int
    image_modals: list
    available_pipelines: dict


class SubjectsQueryResponse(DatasetQueryResponse):
    """Data model for subject data matching a query."""

    subject_data: Union[list[SessionResponse], str]


class DataElementURI(str, Enum):
    """Data model for data element URIs that have available vocabularies."""

    assessment = "nb:Assessment"
    diagnosis = "nb:Diagnosis"


class StandardizedTermVocabularyNamespace(BaseModel):
    """
    Data model for the terms and metadata for a single namespace used in a standardized term vocabulary.
    This includes a list of standardized terms belonging to a standardized variable that all share the same namespace.
    """

    vocabulary_name: str
    namespace_url: str
    namespace_prefix: str
    version: Optional[str]  # TODO: Make version mandatory?
    terms: list[dict]


class StandardizedTermVocabularyResponse(
    RootModel[list[StandardizedTermVocabularyNamespace]]
):
    """Data model for response to a request for all terms in a vocabulary."""

    pass
