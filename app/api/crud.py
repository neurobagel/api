"""CRUD functions called by path operations."""

import asyncio
from collections import defaultdict

import httpx
import pandas as pd
from fastapi import HTTPException, status

from . import env_settings, sparql_models
from . import utility as util
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


async def post_query_to_graph(query: str, timeout: float = None) -> dict:
    """
    Makes a post request to the graph API to perform a query, using parameters from the environment.

    # TODO: Revisit default timeout value when query performance is improved

    Parameters
    ----------
    query : str
        The full SPARQL query string.
    timeout : float, optional
        The maximum duration for the request in seconds, by default None.

    Returns
    -------
    list[dict]
        The response from the graph API, unpacked into a list of dictionaries where
        - each dictionary corresponds to a unique query result
        - dictionary keys are the variables selected in the SPARQL query
        - dictionary values correspond to the variable values
    """
    query = util.add_sparql_context_to_query(query)
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url=settings.query_url,
                content=query,
                headers=util.QUERY_HEADER,
                auth=httpx.BasicAuth(
                    settings.graph_username,
                    settings.graph_password,
                ),
                timeout=timeout,
            )
    # Provide more informative error message for a timeout in the connection to the host.
    except httpx.ConnectTimeout as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Timed out while connecting to the server. You may not be on an authorized network to perform this request.",
        ) from exc

    if not response.is_success:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"{response.reason_phrase}: {response.text}",
        )

    return util.unpack_graph_response_json_to_dicts(response.json())


async def query_matching_dataset_sizes(dataset_uuids: list[str]) -> dict:
    """
    Queries the graph for the number of subjects in each dataset in a list of dataset UUIDs.

    Parameters
    ----------
    dataset_uuids : list[str]
        A list of unique dataset UUIDs.

    Returns
    -------
    dict
        A dictionary with keys corresponding to the dataset UUIDs and values corresponding to the number of subjects in the dataset.
    """
    # Get the total number of subjects in each dataset that matched the query
    matching_dataset_size_results = await post_query_to_graph(
        util.create_multidataset_size_query(dataset_uuids)
    )
    return {
        ds["dataset_uuid"]: int(ds["total_subjects"])
        for ds in matching_dataset_size_results
    }


async def query_available_modalities_and_pipelines(
    dataset_uuids: list[str],
) -> dict:
    """
    Queries the graph for all imaging modalities and available pipelines for each dataset in a list of dataset UUIDs.
    Parameters
    ----------
    dataset_uuids : list[str]
        A list of unique dataset UUIDs.

    Returns
    -------
    dict
        A dictionary mapping each dataset UUID to a nested dictionaries with the following keys:
        - "image_modals": list of available imaging modalities for the dataset
        - "available_pipelines": dict of available pipelines and their versions for the dataset
    """

    db_results = await post_query_to_graph(
        util.create_imaging_modalities_and_pipelines_query(dataset_uuids)
    )
    formatted_results = pd.DataFrame(db_results).reindex(
        columns=[
            "dataset_uuid",
            "image_modal",
            "pipeline_name",
            "pipeline_version",
        ]
    )

    dataset_imaging_modals = (
        formatted_results.groupby("dataset_uuid")["image_modal"]
        .agg(lambda image_modals: list(image_modals.dropna().unique()))
        .to_dict()
    )

    # Per dataset-pipeline pair, collect list of unique pipeline versions
    pipeline_versions = (
        formatted_results.dropna(subset=["pipeline_name"])
        .groupby(["dataset_uuid", "pipeline_name"])["pipeline_version"]
        .agg(
            lambda pipeline_versions: list(pipeline_versions.dropna().unique())
        )
    )
    dataset_pipelines = defaultdict(dict)
    for (dataset_uuid, pipeline_name), versions in pipeline_versions.items():
        dataset_pipelines[dataset_uuid][pipeline_name] = versions
    # Cast back to regular dict to avoid unpredictable defaultdict behavior downstream
    # (e.g., unwanted dict mutation, key creation)
    dataset_pipelines = dict(dataset_pipelines)

    dataset_imaging_modals_and_pipelines = {
        dataset_uuid: {
            "image_modals": dataset_imaging_modals.get(dataset_uuid, []),
            "available_pipelines": dataset_pipelines.get(dataset_uuid, {}),
        }
        for dataset_uuid in dataset_uuids
    }

    return dataset_imaging_modals_and_pipelines


async def query_records(
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
    Sends SPARQL queries to the graph API via httpx POST requests for subject-session or dataset metadata
    matching the given query parameters, as well as the total number of subjects in each matching dataset.

    Parameters
    ----------
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
    db_results = await post_query_to_graph(
        util.create_query(
            return_agg=settings.return_agg,
            age=(min_age, max_age),
            sex=sex,
            diagnosis=diagnosis,
            min_num_phenotypic_sessions=min_num_phenotypic_sessions,
            min_num_imaging_sessions=min_num_imaging_sessions,
            assessment=assessment,
            image_modal=image_modal,
            pipeline_version=pipeline_version,
            pipeline_name=pipeline_name,
        )
    )

    # Reindexing is needed here because when a certain attribute is missing from all matching sessions,
    # the attribute does not end up in the graph API response or the below resulting processed dataframe.
    # Conforming the columns to a list of expected attributes ensures every subject-session has the same response shape from the node API.
    formatted_results = pd.DataFrame(db_results).reindex(
        columns=ALL_SUBJECT_ATTRIBUTES
    )

    matching_dataset_sizes = await query_matching_dataset_sizes(
        dataset_uuids=formatted_results["dataset_uuid"].unique()
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
            # TODO: The current implementation is valid in that we do not return
            # results for datasets with fewer than min_cell_size subjects. But
            # ideally we would handle this directly inside SPARQL so we don't even
            # get the results in the first place. See #267 for a solution.
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
                subject_data = "protected"
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
            # TODO: need to append as response model instance?
            response.append(dataset_result)

    return response


async def post_subjects(query: SubjectsQueryModel):
    """
    When a POST request is sent to the /subjects path, return a list of dicts where each dict corresponds to
    data for subjects matching the query from a specific dataset.

    Parameters
    ----------
    query : SubjectsQueryModel
        Data model representing the query parameters sent in the POST request.

    Returns
    -------
    list[SubjectsQueryResponse]
        List of responses corresponding to data for subjects matching the query, grouped by dataset.
    """
    db_results = await post_query_to_graph(
        util.create_query(
            return_agg=settings.return_agg,
            age=(query.min_age, query.max_age),
            sex=query.sex,
            diagnosis=query.diagnosis,
            min_num_phenotypic_sessions=query.min_num_phenotypic_sessions,
            min_num_imaging_sessions=query.min_num_imaging_sessions,
            assessment=query.assessment,
            image_modal=query.image_modal,
            pipeline_version=query.pipeline_version,
            pipeline_name=query.pipeline_name,
            dataset_uuids=query.dataset_uuids,
        )
    )

    # Reindexing is needed here because when a certain attribute is missing from all matching sessions,
    # the attribute does not end up in the graph API response or the below resulting processed dataframe.
    # Conforming the columns to a list of expected attributes ensures every subject-session has the same response shape from the node API.
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
            # TODO: The current implementation is valid in that we do not return
            # results for datasets with fewer than min_cell_size subjects. But
            # ideally we would handle this directly inside SPARQL so we don't even
            # get the results in the first place. See #267 for a solution.
            if num_matching_subjects <= settings.min_cell_size:
                continue

            if settings.return_agg:
                subject_data = "protected"
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


async def post_datasets(query: QueryModel) -> list[DatasetQueryResponse]:
    """
    When a POST request is sent to the /datasets path, return list of dicts corresponding to metadata for datasets matching the query.

    Parameters
    ----------
    query : QueryModel
        Data model representing the query parameters sent in the POST request.

    Returns
    -------
    list[DatasetQueryResponse]
        List of responses corresponding to metadata for datasets matching the query.
    """

    phenotypic_query, imaging_query = util.create_sparql_queries_for_datasets(
        query
    )
    tasks = [
        post_query_to_graph(sparql_query)
        for sparql_query in (phenotypic_query, imaging_query)
        if sparql_query
    ]
    db_results_all_queries = await asyncio.gather(*tasks)

    all_formatted_results = []
    for db_results in db_results_all_queries:
        all_formatted_results.append(
            pd.DataFrame(db_results).reindex(
                columns=sparql_models.SPARQL_SELECTED_VARS
            )
        )
    combined_query_results = util.combine_sparql_query_results(
        all_formatted_results
    )

    matching_datasets = combined_query_results["dataset"].unique().tolist()
    # This only needs to be run once, on the intersection of datasets matching
    # both phenotypic and imaging queries.
    matching_dataset_sizes, matching_dataset_imaging_modals_and_pipelines = (
        await asyncio.gather(
            query_matching_dataset_sizes(dataset_uuids=matching_datasets),
            query_available_modalities_and_pipelines(
                dataset_uuids=matching_datasets
            ),
        )
    )

    response = []
    if not combined_query_results.empty:
        for (
            dataset_uuid,
            dataset_matching_records,
        ) in combined_query_results.groupby(by="dataset"):
            num_matching_subjects = dataset_matching_records[
                "subject"
            ].nunique()
            # TODO: The current implementation is valid in that we do not return
            # results for datasets with fewer than min_cell_count subjects. But
            # ideally we would handle this directly inside SPARQL so we don't even
            # get the results in the first place. See #267 for a solution.
            if num_matching_subjects <= settings.min_cell_size:
                continue

            # TODO: Do we need to explicitly account/error out for a scenario where there's somehow a dataset in the graph
            # that doesn't have a corresponding entry in the datasets metadata JSON?
            # NOTE: Dataset UUIDs in the graph have full namespace URIs, whereas the datasets metadata JSON uses
            # prefixed versions (e.g., nb:123456 instead of http://neurobagel.ca/vocab/123456).
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
                ][
                    "available_pipelines"
                ],
            }
            dataset_result = DatasetQueryResponse(
                **dataset_static_metadata,
                **dataset_dynamic_metadata,
            )

            response.append(dataset_result)

    return response


async def get_terms(
    data_element_URI: str, std_trm_vocab: list[dict] | None
) -> dict:
    """
    Makes a POST request to the graph API for all used standardized terms that represent instances of the given data element URI.
    The payload is a SPARQL query generated by the create_terms_query function.

    Parameters
    ----------
    data_element_URI : str
        Controlled term of neurobagel class for which all the available terms should be retrieved.
    std_trm_vocab : list[dict] | None
        List of dictionaries representing the vocabulary for the data element URI, where each dictionary corresponds to a vocabulary namespace and
        contains the namespace metadata and a list of standardized terms. Corresponds to the contents of the terms file for a specific standardized variable.

    Returns
    -------
    dict
        Dictionary where the key is the Neurobagel class and the value is a list of dictionaries
        corresponding to the available (i.e. used) instances of that class in the graph. Each instance dictionary
        contains the 'TermURL' and the human-readable 'Label' for the term, and may include additional
        metadata fields (e.g., 'abbreviation', 'data_type' for imaging modalities) when available.
    """
    db_results = await post_query_to_graph(
        util.create_terms_query(data_element_URI)
    )

    if std_trm_vocab is None:
        std_trm_vocab = []

    term_metadata = []
    for result in db_results:
        term_url = result["termURL"]
        # First, check whether the found instance of the standardized variable contains a recognized namespace
        if util.is_term_namespace_in_context(term_url):
            # Then, get the namespace and ID for the term
            term_namespace_url, term_id = util.split_namespace_from_term_uri(
                term_url
            )
            # Since the term vocabulary for a standardized variable can contain terms from several namespaces,
            # we first have to locate the namespace used in the term we are looking up
            namespace_terms = next(
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
                f"The controlled term {term_url} was found in the graph but does not come from a vocabulary recognized by Neurobagel."
                "This term will be ignored."
            )

    term_instances = {data_element_URI: term_metadata}

    return term_instances


async def get_controlled_term_attributes() -> list:
    """
    Makes a POST query to graph API for all Neurobagel classes representing controlled term attributes.

    Parameters
    ----------

    Returns
    -------
    list
        List of TermURLs of all available controlled term attributes, with abbrieviated namespace prefixes.
    """
    attributes_query = """
    SELECT DISTINCT ?attribute
    WHERE {
        ?attribute rdfs:subClassOf nb:ControlledTerm .
    }
    """
    db_results = await post_query_to_graph(attributes_query)
    all_attributes = [
        util.replace_namespace_uri_with_prefix(result["attribute"])
        for result in db_results
    ]
    return all_attributes
