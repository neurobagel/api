"""CRUD functions called by path operations."""

import warnings
from typing import Literal

import httpx
import pandas as pd
from fastapi import HTTPException, status

from . import utility as util
from .config import settings
from .models import SessionResponse

ALL_SUBJECT_ATTRIBUTES = list(SessionResponse.model_fields.keys()) + [
    "dataset_uuid",
    "dataset_name",
    "dataset_portal_uri",
    "pipeline_version",
    "pipeline_name",
]


def post_query_to_graph(query: str, timeout: float = None) -> dict:
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
    dict
        The response from the graph API, encoded as json.
    """
    try:
        response = httpx.post(
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

    return response.json()


def query_matching_dataset_sizes(dataset_uuids: list) -> dict:
    """
    Queries the graph for the number of subjects in each dataset in a list of dataset UUIDs.

    Parameters
    ----------
    dataset_uuids : pd.Series
        A list of unique dataset UUIDs.

    Returns
    -------
    dict
        A dictionary with keys corresponding to the dataset UUIDs and values corresponding to the number of subjects in the dataset.
    """
    # Get the total number of subjects in each dataset that matched the query
    matching_dataset_size_results = post_query_to_graph(
        util.create_multidataset_size_query(dataset_uuids)
    )
    return {
        ds["dataset_uuid"]: int(ds["total_subjects"])
        for ds in util.unpack_graph_response_json_to_dicts(
            matching_dataset_size_results
        )
    }


async def query_records(
    min_age: float,
    max_age: float,
    sex: str,
    diagnosis: str,
    is_control: Literal[True, None],
    min_num_imaging_sessions: int,
    min_num_phenotypic_sessions: int,
    assessment: str,
    image_modal: str,
    pipeline_name: str,
    pipeline_version: str,
    is_datasets_query: bool,
    dataset_uuids: list[str],
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
    is_control : {True, None}
        If True, return only healthy control subjects.
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
    is_datasets_query : bool
        Whether the query is for matching dataset metadata only (used by the /datasets path).
    dataset_uuids : list[str]
        List of datasets to restrict the query to.

    Returns
    -------
    list
        List of CohortQueryResponse objects, where each object corresponds to a dataset matching the query.
    """
    results = post_query_to_graph(
        util.create_query(
            return_agg=is_datasets_query or settings.return_agg,
            age=(min_age, max_age),
            sex=sex,
            diagnosis=diagnosis,
            is_control=is_control,
            min_num_phenotypic_sessions=min_num_phenotypic_sessions,
            min_num_imaging_sessions=min_num_imaging_sessions,
            assessment=assessment,
            image_modal=image_modal,
            pipeline_version=pipeline_version,
            pipeline_name=pipeline_name,
            dataset_uuids=dataset_uuids,
        )
    )

    # Reindexing is needed here because when a certain attribute is missing from all matching sessions,
    # the attribute does not end up in the graph API response or the below resulting processed dataframe.
    # Conforming the columns to a list of expected attributes ensures every subject-session has the same response shape from the node API.
    results_df = pd.DataFrame(
        util.unpack_graph_response_json_to_dicts(results)
    ).reindex(columns=ALL_SUBJECT_ATTRIBUTES)

    matching_dataset_sizes = query_matching_dataset_sizes(
        results_df["dataset_uuid"].unique()
    )

    response_obj = []
    dataset_cols = ["dataset_uuid", "dataset_name"]
    if not results_df.empty:
        for (
            dataset_uuid,
            dataset_name,
        ), dataset_matching_records in results_df.groupby(by=dataset_cols):
            num_matching_subjects = dataset_matching_records[
                "sub_id"
            ].nunique()
            # TODO: The current implementation is valid in that we do not return
            # results for datasets with fewer than min_cell_count subjects. But
            # ideally we would handle this directly inside SPARQL so we don't even
            # get the results in the first place. See #267 for a solution.
            if num_matching_subjects <= settings.min_cell_size:
                continue

            dataset_available_pipelines = (
                dataset_matching_records.groupby("pipeline_name", dropna=True)[
                    "pipeline_version"
                ]
                .apply(lambda x: list(x.dropna().unique()))
                .to_dict()
            )

            dataset_response = {
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

            if is_datasets_query:
                # TODO: need to append as response model instance?
                response_obj.append(dataset_response)
            else:
                if settings.return_agg:
                    subject_data = "protected"
                else:
                    dataset_matching_records = dataset_matching_records.drop(
                        dataset_cols, axis=1
                    )
                    subject_data = (
                        util.construct_matching_sub_results_for_dataset(
                            dataset_matching_records
                        )
                    )

                subject_response = {
                    **dataset_response,
                    "subject_data": subject_data,
                }
                # TODO: need to append as response model instance?
                response_obj.append(subject_response)

    return response_obj


async def get_terms(data_element_URI: str, terms_vocab: list | None) -> dict:
    """
    Makes a POST request to graph API using httpx where the payload is a SPARQL query generated by the create_terms_query function.

    Parameters
    ----------
    data_element_URI : str
        Controlled term of neurobagel class for which all the available terms should be retrieved.
    terms_vocab : list | None
        List of vocabulary namespaces and their corresponding standardized terms for the data element URI.
        Corresponds to the contents of the terms file for a specific standardized variable.

    Returns
    -------
    dict
        Dictionary where the key is the Neurobagel class and the value is a list of dictionaries
        corresponding to the available (i.e. used) instances of that class in the graph. Each instance dictionary
        has two items: the 'TermURL' and the human-readable 'Label' for the term.
    """
    term_url_results = post_query_to_graph(
        util.create_terms_query(data_element_URI)
    )

    if terms_vocab is None:
        terms_vocab = []

    term_label_dicts = []
    for result in term_url_results["results"]["bindings"]:
        term_url = result["termURL"]["value"]
        # First, check whether the found instance of the data element contains a recognized namespace
        if util.is_term_namespace_in_context(term_url):
            # Then, attempt to get the label for the term
            namespace_url, term_id = util.strip_namespace_from_term_uri(
                term_url
            )
            namespace_terms = next(
                (
                    namespace["terms"]
                    for namespace in terms_vocab
                    if namespace["namespace_url"] == namespace_url
                ),
                [],
            )
            term_label = next(
                (
                    term["label"]
                    for term in namespace_terms
                    if term["id"] == term_id
                ),
                None,
            )
            term_label_dicts.append(
                {
                    "TermURL": util.replace_namespace_uri_with_prefix(
                        term_url
                    ),
                    "Label": term_label,
                }
            )
        else:
            warnings.warn(
                f"The controlled term {term_url} was found in the graph but does not come from a vocabulary recognized by Neurobagel."
                "This term will be ignored."
            )

    results_dict = {data_element_URI: term_label_dicts}

    return results_dict


async def get_controlled_term_attributes() -> list:
    """
    Makes a POST query to graph API for all Neurobagel classes representing controlled term attributes.

    Returns
    -------
    list
        List of TermURLs of all available controlled term attributes, with abbrieviated namespace prefixes.
    """
    attributes_query = f"""
    {util.create_context()}

    SELECT DISTINCT ?attribute
    WHERE {{
        ?attribute rdfs:subClassOf nb:ControlledTerm .
    }}
    """
    results = post_query_to_graph(attributes_query)

    results_list = [
        util.replace_namespace_uri_with_prefix(result["attribute"]["value"])
        for result in results["results"]["bindings"]
    ]

    return results_list
