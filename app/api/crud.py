"""CRUD functions called by path operations using SQLModel ORM."""

import asyncio
from collections import defaultdict
from typing import Optional

import pandas as pd
from fastapi import HTTPException, status
from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from . import env_settings, utility as util
from .db_models import (
    Acquisition,
    CompletedPipeline,
    ControlledTerm,
    ControlledTermAttribute,
    Dataset,
    Session,
    Subject,
)
from .env_settings import settings
from .logger import get_logger
from .models import (
    DataElementURI,
    DatasetQueryResponse,
    QueryModel,
    SessionResponse,
    SubjectsQueryModel,
    SubjectsQueryResponse,
)

logger = get_logger(__name__)


ALL_SUBJECT_ATTRIBUTES = list(SessionResponse.model_fields.keys()) + [
    "dataset_uuid",
    "dataset_name",
    "dataset_portal_uri",
    "pipeline_version",
    "pipeline_name",
]


async def query_matching_dataset_sizes(
    session: AsyncSession, dataset_uuids: list[str]
) -> dict:
    """
    Queries the database for the number of subjects in each dataset in a list of dataset UUIDs.

    Parameters
    ----------
    session : AsyncSession
        Database session.
    dataset_uuids : list[str]
        A list of unique dataset UUIDs.

    Returns
    -------
    dict
        A dictionary with keys corresponding to the dataset UUIDs and values corresponding to the number of subjects in the dataset.
    """
    stmt = (
        select(Dataset.dataset_uuid, func.count(distinct(Subject.id)))
        .join(Subject, Subject.dataset_id == Dataset.id)
        .where(Dataset.dataset_uuid.in_(dataset_uuids))
        .group_by(Dataset.dataset_uuid)
    )
    result = await session.execute(stmt)
    return {row[0]: row[1] for row in result.all()}


async def query_available_modalities_and_pipelines(
    session: AsyncSession,
    dataset_uuids: list[str],
) -> dict:
    """
    Queries the database for all imaging modalities and available pipelines for each dataset in a list of dataset UUIDs.
    
    Parameters
    ----------
    session : AsyncSession
        Database session.
    dataset_uuids : list[str]
        A list of unique dataset UUIDs.

    Returns
    -------
    dict
        A dictionary mapping each dataset UUID to a nested dictionaries with the following keys:
        - "image_modals": list of available imaging modalities for the dataset
        - "available_pipelines": dict of available pipelines and their versions for the dataset
    """
    # Query for imaging modalities
    modalities_stmt = (
        select(Dataset.dataset_uuid, Acquisition.image_modal)
        .join(Subject, Subject.dataset_id == Dataset.id)
        .join(Session, Session.subject_id == Subject.id)
        .join(Acquisition, Acquisition.session_id == Session.id)
        .where(Dataset.dataset_uuid.in_(dataset_uuids))
        .where(Acquisition.image_modal.isnot(None))
        .distinct()
    )
    modalities_result = await session.execute(modalities_stmt)
    
    # Group by dataset
    dataset_imaging_modals = defaultdict(list)
    for dataset_uuid, image_modal in modalities_result.all():
        dataset_imaging_modals[dataset_uuid].append(image_modal)

    # Query for pipelines
    pipelines_stmt = (
        select(
            Dataset.dataset_uuid,
            CompletedPipeline.pipeline_name,
            CompletedPipeline.pipeline_version,
        )
        .join(Subject, Subject.dataset_id == Dataset.id)
        .join(Session, Session.subject_id == Subject.id)
        .join(CompletedPipeline, CompletedPipeline.session_id == Session.id)
        .where(Dataset.dataset_uuid.in_(dataset_uuids))
        .where(CompletedPipeline.pipeline_name.isnot(None))
        .distinct()
    )
    pipelines_result = await session.execute(pipelines_stmt)
    
    # Group by dataset and pipeline
    dataset_pipelines: dict[str, dict] = defaultdict(lambda: defaultdict(list))
    for dataset_uuid, pipeline_name, pipeline_version in pipelines_result.all():
        if pipeline_version:
            dataset_pipelines[dataset_uuid][pipeline_name].append(pipeline_version)
    
    # Convert defaultdicts to regular dicts
    dataset_pipelines = {
        k: dict(v) for k, v in dataset_pipelines.items()
    }

    dataset_imaging_modals_and_pipelines = {
        dataset_uuid: {
            "image_modals": dataset_imaging_modals.get(dataset_uuid, []),
            "available_pipelines": dataset_pipelines.get(dataset_uuid, {}),
        }
        for dataset_uuid in dataset_uuids
    }

    return dataset_imaging_modals_and_pipelines


async def build_query_filters(
    query: QueryModel, base_stmt, subject_alias=None
):
    """
    Build SQLAlchemy filters based on query parameters.
    
    Parameters
    ----------
    query : QueryModel
        Query model with filter parameters.
    base_stmt : Select
        Base SQLAlchemy select statement.
    subject_alias : Table, optional
        Subject table alias if needed.
        
    Returns
    -------
    Select
        SQLAlchemy select statement with filters applied.
    """
    stmt = base_stmt
    
    # Age filters
    if query.min_age is not None:
        stmt = stmt.where(Session.age >= query.min_age)
    if query.max_age is not None:
        stmt = stmt.where(Session.age <= query.max_age)
    
    # Sex filter
    if query.sex is not None:
        stmt = stmt.where(Session.sex == query.sex)
    
    # Diagnosis filter
    if query.diagnosis is not None:
        stmt = stmt.where(Session.diagnosis == query.diagnosis)
    
    # Assessment filter
    if query.assessment is not None:
        stmt = stmt.where(Session.assessment == query.assessment)
    
    # Imaging filters
    if query.image_modal is not None:
        stmt = stmt.join(Acquisition, Acquisition.session_id == Session.id)
        stmt = stmt.where(Acquisition.image_modal == query.image_modal)
    
    # Pipeline filters
    if query.pipeline_name is not None or query.pipeline_version is not None:
        if "Acquisition" not in str(stmt):
            # Only join if not already joined
            stmt = stmt.outerjoin(
                CompletedPipeline, CompletedPipeline.session_id == Session.id
            )
        if query.pipeline_name is not None:
            stmt = stmt.where(CompletedPipeline.pipeline_name == query.pipeline_name)
        if query.pipeline_version is not None:
            stmt = stmt.where(
                CompletedPipeline.pipeline_version == query.pipeline_version
            )
    
    return stmt


async def query_records(
    session: AsyncSession,
    min_age: float,
    max_age: float,
    sex: str,
    diagnosis: str,
    min_num_imaging_sessions: int,
    min_num_phenotypic_sessions: int,
    assessment: str,
    image_modal: str,
    pipeline_name: str,
    pipeline_version: str,
) -> list[dict]:
    """
    Queries the database for subject-session metadata matching the given query parameters.

    Parameters
    ----------
    session : AsyncSession
        Database session.
    min_age : float
        Minimum age of subject.
    max_age : float
        Maximum age of subject.
    sex : str
        Sex of subject.
    diagnosis : str
        Subject diagnosis.
    min_num_imaging_sessions : int
        Subject minimum number of imaging sessions.
    min_num_phenotypic_sessions : int
        Subject minimum number of phenotypic sessions.
    assessment : str
        Non-imaging assessment completed by subjects.
    image_modal : str
        Imaging modality of subject scans.
    pipeline_name : str
        Name of pipeline run on subject scans.
    pipeline_version : str
        Version of pipeline run on subject scans.

    Returns
    -------
    list
        List of CohortQueryResponse objects, where each object corresponds to a dataset matching the query.
    """
    # Build base query
    stmt = (
        select(
            Dataset.dataset_uuid,
            Dataset.dataset_name,
            Dataset.dataset_portal_uri,
            Subject.sub_id,
            Session.age,
            Session.sex,
            Session.diagnosis,
            Session.subject_group,
            Session.session_id,
            Session.session_type,
            Session.assessment,
            Session.session_file_path,
        )
        .join(Subject, Subject.dataset_id == Dataset.id)
        .join(Session, Session.subject_id == Subject.id)
    )
    
    # Create query model for filters
    query_model = QueryModel(
        min_age=min_age,
        max_age=max_age,
        sex=sex,
        diagnosis=diagnosis,
        min_num_imaging_sessions=min_num_imaging_sessions,
        min_num_phenotypic_sessions=min_num_phenotypic_sessions,
        assessment=assessment,
        image_modal=image_modal,
        pipeline_name=pipeline_name,
        pipeline_version=pipeline_version,
    )
    
    # Apply filters
    stmt = await build_query_filters(query_model, stmt)
    
    # Execute query
    result = await session.execute(stmt)
    rows = result.all()
    
    # Convert to list of dicts
    db_results = []
    for row in rows:
        db_results.append({
            "dataset_uuid": row[0],
            "dataset_name": row[1],
            "dataset_portal_uri": row[2],
            "sub_id": row[3],
            "age": row[4],
            "sex": row[5],
            "diagnosis": row[6],
            "subject_group": row[7],
            "session_id": row[8],
            "session_type": row[9],
            "assessment": row[10],
            "session_file_path": row[11],
        })
    
    # Get imaging modalities and pipelines for each session
    if db_results:
        session_ids = list(set(row["session_id"] for row in db_results))
        
        # Query acquisitions
        acq_stmt = (
            select(Session.session_id, Acquisition.image_modal)
            .join(Acquisition, Acquisition.session_id == Session.id)
            .where(Session.session_id.in_(session_ids))
        )
        acq_result = await session.execute(acq_stmt)
        acquisitions_map = defaultdict(list)
        for sess_id, img_modal in acq_result.all():
            acquisitions_map[sess_id].append(img_modal)
        
        # Query pipelines
        pipe_stmt = (
            select(
                Session.session_id,
                CompletedPipeline.pipeline_name,
                CompletedPipeline.pipeline_version,
            )
            .join(CompletedPipeline, CompletedPipeline.session_id == Session.id)
            .where(Session.session_id.in_(session_ids))
        )
        pipe_result = await session.execute(pipe_stmt)
        pipelines_map = defaultdict(list)
        for sess_id, p_name, p_version in pipe_result.all():
            pipelines_map[sess_id].append({
                "pipeline_name": p_name,
                "pipeline_version": p_version,
            })
        
        # Add to results
        for row in db_results:
            sess_id = row["session_id"]
            row["image_modal"] = acquisitions_map.get(sess_id, [None])[0]
            pipelines = pipelines_map.get(sess_id, [])
            row["pipeline_name"] = pipelines[0]["pipeline_name"] if pipelines else None
            row["pipeline_version"] = pipelines[0]["pipeline_version"] if pipelines else None
    
    # Count sessions per subject
    # TODO: Implement min_num_imaging_sessions and min_num_phenotypic_sessions filters
    for row in db_results:
        row["num_matching_phenotypic_sessions"] = 0
        row["num_matching_imaging_sessions"] = 0
    
    # Reindex to match expected format
    formatted_results = pd.DataFrame(db_results).reindex(
        columns=ALL_SUBJECT_ATTRIBUTES
    )

    matching_dataset_sizes = await query_matching_dataset_sizes(
        session, dataset_uuids=formatted_results["dataset_uuid"].unique()
    )

    response = []
    dataset_cols = ["dataset_uuid", "dataset_name"]
    if not formatted_results.empty:
        for (
            dataset_uuid,
            dataset_name,
        ), dataset_matching_records in formatted_results.groupby(
            by=dataset_cols
        ):
            num_matching_subjects = dataset_matching_records[
                "sub_id"
            ].nunique()
            if num_matching_subjects <= settings.min_cell_size:
                continue

            dataset_available_pipelines = (
                dataset_matching_records.groupby("pipeline_name", dropna=True)[
                    "pipeline_version"
                ]
                .agg(lambda x: list(x.dropna().unique()))
                .to_dict()
            )

            matching_dataset_info = {
                "dataset_uuid": dataset_uuid,
                "dataset_name": dataset_name,
                "dataset_total_subjects": matching_dataset_sizes[dataset_uuid],
                "dataset_portal_uri": (
                    dataset_matching_records["dataset_portal_uri"].iloc[0]
                    if not dataset_matching_records["dataset_portal_uri"]
                    .isna()
                    .any()
                    else None
                ),
                "num_matching_subjects": num_matching_subjects,
                "records_protected": settings.return_agg,
                "image_modals": list(
                    dataset_matching_records["image_modal"][
                        dataset_matching_records["image_modal"].notna()
                    ].unique()
                ),
                "available_pipelines": dataset_available_pipelines,
            }

            if settings.return_agg:
                subject_data: str | list = "protected"
            else:
                dataset_matching_records = dataset_matching_records.drop(
                    dataset_cols, axis=1
                )
                subject_data = util.construct_matching_sub_results_for_dataset(
                    dataset_matching_records
                )

            dataset_result = {
                **matching_dataset_info,
                "subject_data": subject_data,
            }
            response.append(dataset_result)

    return response


async def post_subjects(
    db_session: AsyncSession, query: SubjectsQueryModel
):
    """
    When a POST request is sent to the /subjects path, return a list of dicts where each dict corresponds to
    data for subjects matching the query from a specific dataset.

    Parameters
    ----------
    db_session : AsyncSession
        Database session.
    query : SubjectsQueryModel
        Data model representing the query parameters sent in the POST request.

    Returns
    -------
    list[SubjectsQueryResponse]
        List of responses corresponding to data for subjects matching the query, grouped by dataset.
    """
    # Build base query
    stmt = (
        select(
            Dataset.dataset_uuid,
            Subject.sub_id,
            Session.session_id,
            Session.session_type,
        )
        .join(Subject, Subject.dataset_id == Dataset.id)
        .join(Session, Session.subject_id == Subject.id)
    )
    
    # Apply dataset filter if provided
    if query.dataset_uuids:
        stmt = stmt.where(Dataset.dataset_uuid.in_(query.dataset_uuids))
    
    # Apply other filters
    stmt = await build_query_filters(query, stmt)
    
    # Execute query
    result = await db_session.execute(stmt)
    rows = result.all()
    
    # Convert to DataFrame
    db_results = [
        {
            "dataset_uuid": row[0],
            "sub_id": row[1],
            "session_id": row[2],
            "session_type": row[3],
        }
        for row in rows
    ]
    
    formatted_results = pd.DataFrame(db_results).reindex(
        columns=ALL_SUBJECT_ATTRIBUTES
    )

    response = []
    if not formatted_results.empty:
        for (
            dataset_uuid,
            dataset_matching_records,
        ) in formatted_results.groupby(by="dataset_uuid"):
            num_matching_subjects = dataset_matching_records[
                "sub_id"
            ].nunique()
            if num_matching_subjects <= settings.min_cell_size:
                continue

            if settings.return_agg:
                subject_data: str | list = "protected"
            else:
                subject_data = util.construct_matching_sub_results_for_dataset(
                    dataset_matching_records
                )

            dataset_result = SubjectsQueryResponse(
                dataset_uuid=dataset_uuid,
                subject_data=subject_data,
            )
            response.append(dataset_result)

    return response


async def post_datasets(
    db_session: AsyncSession, query: QueryModel
) -> list[DatasetQueryResponse]:
    """
    When a POST request is sent to the /datasets path, return list of dicts corresponding to metadata for datasets matching the query.

    Parameters
    ----------
    db_session : AsyncSession
        Database session.
    query : QueryModel
        Data model representing the query parameters sent in the POST request.

    Returns
    -------
    list[DatasetQueryResponse]
        List of responses corresponding to metadata for datasets matching the query.
    """
    # Build base query to find matching datasets
    stmt = (
        select(Dataset.dataset_uuid, Subject.sub_id)
        .join(Subject, Subject.dataset_id == Dataset.id)
        .join(Session, Session.subject_id == Subject.id)
        .distinct()
    )
    
    # Apply filters
    stmt = await build_query_filters(query, stmt)
    
    # Execute query
    result = await db_session.execute(stmt)
    rows = result.all()
    
    # Convert to DataFrame
    db_results = [{"dataset": row[0], "subject": row[1]} for row in rows]
    combined_query_results = pd.DataFrame(db_results)

    if combined_query_results.empty:
        return []

    matching_datasets = combined_query_results["dataset"].unique().tolist()
    
    # Get dataset sizes and imaging modalities/pipelines
    matching_dataset_sizes, matching_dataset_imaging_modals_and_pipelines = (
        await asyncio.gather(
            query_matching_dataset_sizes(
                db_session, dataset_uuids=matching_datasets
            ),
            query_available_modalities_and_pipelines(
                db_session, dataset_uuids=matching_datasets
            ),
        )
    )

    response = []
    for (
        dataset_uuid,
        dataset_matching_records,
    ) in combined_query_results.groupby(by="dataset"):
        num_matching_subjects = dataset_matching_records["subject"].nunique()
        
        if num_matching_subjects <= settings.min_cell_size:
            continue

        # Get static metadata from loaded JSON
        dataset_static_metadata = env_settings.DATASETS_METADATA.get(
            util.replace_namespace_uri_with_prefix(dataset_uuid), {}
        )
        dataset_dynamic_metadata = {
            "dataset_uuid": dataset_uuid,
            "dataset_total_subjects": matching_dataset_sizes[dataset_uuid],
            "num_matching_subjects": num_matching_subjects,
            "records_protected": settings.return_agg,
            "image_modals": matching_dataset_imaging_modals_and_pipelines[
                dataset_uuid
            ]["image_modals"],
            "available_pipelines": matching_dataset_imaging_modals_and_pipelines[
                dataset_uuid
            ]["available_pipelines"],
        }
        dataset_result = DatasetQueryResponse(
            **dataset_static_metadata,
            **dataset_dynamic_metadata,
        )

        response.append(dataset_result)

    return response


async def get_terms(
    db_session: AsyncSession,
    data_element_URI: str,
    std_trm_vocab: list[dict] | None,
) -> dict:
    """
    Queries the database for all used standardized terms that represent instances of the given data element URI.

    Parameters
    ----------
    db_session : AsyncSession
        Database session.
    data_element_URI : str
        Controlled term of neurobagel class for which all the available terms should be retrieved.
    std_trm_vocab : list[dict] | None
        List of dictionaries representing the vocabulary for the data element URI.

    Returns
    -------
    dict
        Dictionary where the key is the Neurobagel class and the value is a list of dictionaries
        corresponding to the available (i.e. used) instances of that class in the graph.
    """
    stmt = select(ControlledTerm.term_url).where(
        ControlledTerm.data_element_uri == data_element_URI
    )
    result = await db_session.execute(stmt)
    db_results = [{"termURL": row[0]} for row in result.all()]

    if std_trm_vocab is None:
        std_trm_vocab = []

    term_metadata = []
    for result in db_results:
        term_url = result["termURL"]
        if util.is_term_namespace_in_context(term_url):
            term_namespace_url, term_id = util.split_namespace_from_term_uri(
                term_url
            )
            namespace_terms: list = next(
                (
                    namespace["terms"]
                    for namespace in std_trm_vocab
                    if namespace["namespace_url"] == term_namespace_url
                ),
                [],
            )
            matched_term = next(
                (term for term in namespace_terms if term["id"] == term_id),
                None,
            )
            term_entry = {
                "TermURL": util.replace_namespace_uri_with_prefix(term_url),
                "Label": matched_term.get("name") if matched_term else None,
            }
            if data_element_URI == DataElementURI.image.value:
                term_entry["Abbreviation"] = (
                    matched_term.get("abbreviation", None)
                    if matched_term
                    else None
                )
                term_entry["DataType"] = (
                    matched_term.get("data_type") if matched_term else None
                )
            term_metadata.append(term_entry)
        else:
            logger.warning(
                f"The controlled term {term_url} was found in the graph but does not come from a vocabulary recognized by Neurobagel. "
                "This term will be ignored."
            )

    term_instances = {data_element_URI: term_metadata}

    return term_instances


async def get_controlled_term_attributes(
    db_session: AsyncSession,
) -> list:
    """
    Queries database for all Neurobagel classes representing controlled term attributes.

    Parameters
    ----------
    db_session : AsyncSession
        Database session.

    Returns
    -------
    list
        List of TermURLs of all available controlled term attributes, with abbreviated namespace prefixes.
    """
    stmt = select(ControlledTermAttribute.attribute)
    result = await db_session.execute(stmt)
    all_attributes = [
        util.replace_namespace_uri_with_prefix(row[0])
        for row in result.all()
    ]
    return all_attributes
