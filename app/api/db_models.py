"""SQLModel database models for Postgres backend."""

from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


class Dataset(SQLModel, table=True):
    """Dataset model representing a neuroscience dataset."""

    __tablename__ = "datasets"

    id: Optional[int] = Field(default=None, primary_key=True)
    dataset_uuid: str = Field(unique=True, index=True)
    dataset_name: str
    dataset_portal_uri: Optional[str] = None

    # Additional metadata fields
    authors: Optional[str] = None  # JSON array stored as string
    homepage: Optional[str] = None
    references_and_links: Optional[str] = None  # JSON array stored as string
    keywords: Optional[str] = None  # JSON array stored as string
    repository_url: Optional[str] = None
    access_instructions: Optional[str] = None
    access_type: Optional[str] = None
    access_email: Optional[str] = None
    access_link: Optional[str] = None

    # Relationships
    subjects: list["Subject"] = Relationship(back_populates="dataset")


class Subject(SQLModel, table=True):
    """Subject model representing a participant in a dataset."""

    __tablename__ = "subjects"

    id: Optional[int] = Field(default=None, primary_key=True)
    sub_id: str = Field(index=True)
    dataset_id: int = Field(foreign_key="datasets.id", index=True)

    # Relationships
    dataset: Dataset = Relationship(back_populates="subjects")
    sessions: list["Session"] = Relationship(back_populates="subject")


class Session(SQLModel, table=True):
    """Session model representing either an imaging or phenotypic session."""

    __tablename__ = "sessions"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(index=True)
    session_type: str = Field(
        index=True
    )  # "ImagingSession" or "PhenotypicSession"
    subject_id: int = Field(foreign_key="subjects.id", index=True)

    # Phenotypic attributes
    age: Optional[float] = None
    sex: Optional[str] = Field(default=None, index=True)
    diagnosis: Optional[str] = Field(default=None, index=True)
    subject_group: Optional[str] = None
    assessment: Optional[str] = Field(default=None, index=True)

    # Imaging attributes
    session_file_path: Optional[str] = None

    # Relationships
    subject: Subject = Relationship(back_populates="sessions")
    acquisitions: list["Acquisition"] = Relationship(back_populates="session")
    pipelines: list["CompletedPipeline"] = Relationship(
        back_populates="session"
    )


class Acquisition(SQLModel, table=True):
    """Acquisition model representing an imaging acquisition."""

    __tablename__ = "acquisitions"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="sessions.id", index=True)
    image_modal: str = Field(index=True)  # hasContrastType

    # Relationships
    session: Session = Relationship(back_populates="acquisitions")


class CompletedPipeline(SQLModel, table=True):
    """CompletedPipeline model representing a pipeline run on a session."""

    __tablename__ = "completed_pipelines"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="sessions.id", index=True)
    pipeline_name: str = Field(index=True)
    pipeline_version: str = Field(index=True)

    # Relationships
    session: Session = Relationship(back_populates="pipelines")


class ControlledTermAttribute(SQLModel, table=True):
    """ControlledTermAttribute model for storing available controlled term attributes."""

    __tablename__ = "controlled_term_attributes"

    id: Optional[int] = Field(default=None, primary_key=True)
    attribute: str = Field(unique=True, index=True)


class ControlledTerm(SQLModel, table=True):
    """ControlledTerm model for storing standardized terms."""

    __tablename__ = "controlled_terms"

    id: Optional[int] = Field(default=None, primary_key=True)
    term_url: str = Field(unique=True, index=True)
    data_element_uri: str = Field(index=True)
