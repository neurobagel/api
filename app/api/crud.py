"""CRUD functions called by path operations."""

import os
import warnings
from pathlib import Path

import httpx
import numpy as np
import pandas as pd
from fastapi import HTTPException, status

from . import utility as util
from .models import CohortQueryResponse, SessionResponse, VocabLabelsResponse

ALL_SUBJECT_ATTRIBUTES = list(SessionResponse.__fields__.keys()) + [
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
            url=util.QUERY_URL,
            content=query,
            headers=util.QUERY_HEADER,
            auth=httpx.BasicAuth(
                os.environ.get(util.GRAPH_USERNAME.name),
                os.environ.get(util.GRAPH_PASSWORD.name),
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


async def get(
    min_age: float,
    max_age: float,
    sex: str,
    diagnosis: str,
    is_control: bool,
    min_num_imaging_sessions: int,
    min_num_phenotypic_sessions: int,
    assessment: str,
    image_modal: str,
    pipeline_name: str,
    pipeline_version: str,
) -> list[CohortQueryResponse]:
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
    is_control : bool
        Whether or not subject is a control.
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
    results = post_query_to_graph(
        util.create_query(
            return_agg=util.RETURN_AGG.val,
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
        for (dataset_uuid, dataset_name), group in results_df.groupby(
            by=dataset_cols
        ):
            if util.RETURN_AGG.val:
                subject_data = "protected"
            else:
                subject_data = (
                    group.drop(dataset_cols, axis=1)
                    .groupby(
                        by=["sub_id", "session_id", "session_type"],
                        dropna=True,
                    )
                    .agg(
                        {
                            "sub_id": "first",
                            "session_id": "first",
                            "num_matching_phenotypic_sessions": "first",
                            "num_matching_imaging_sessions": "first",
                            "session_type": "first",
                            "age": "first",
                            "sex": "first",
                            "diagnosis": lambda x: list(x.unique()),
                            "subject_group": "first",
                            "assessment": lambda x: list(x.unique()),
                            "image_modal": lambda x: list(x.unique()),
                            "session_file_path": "first",
                        }
                    )
                )

                # Get the unique versions of each pipeline that was run on each session
                pipeline_grouped_data = (
                    group.groupby(
                        [
                            "sub_id",
                            "session_id",
                            "session_type",
                            "pipeline_name",
                        ],
                        # We cannot drop NaNs here because sessions without pipelines (i.e., with empty values for pipeline_name)
                        # would otherwise be completely removed and in an extreme case where no matching sessions have pipeline info,
                        # we'd end up with an empty dataframe.
                        dropna=False,
                    ).agg(
                        {
                            "pipeline_version": lambda x: list(
                                x.dropna().unique()
                            )
                        }
                    )
                    # Turn indices from the groupby back into dataframe columns
                    .reset_index()
                )

                # Aggregate all completed pipelines for each session
                session_grouped_data = pipeline_grouped_data.groupby(
                    ["sub_id", "session_id", "session_type"],
                )
                session_completed_pipeline_data = (
                    session_grouped_data.apply(
                        lambda x: {
                            pname: pvers
                            for pname, pvers in zip(
                                x["pipeline_name"], x["pipeline_version"]
                            )
                            if not pd.isnull(pname)
                        }
                    )
                    # NOTE: The below function expects a pd.Series only.
                    # This can break if the result of the apply function is a pd.DataFrame
                    # (pd.DataFrame.reset_index() doesn't have a "name" arg),
                    # which can happen if the original dataframe being operated on is empty.
                    # For example, see https://github.com/neurobagel/api/issues/367.
                    # (Related: https://github.com/pandas-dev/pandas/issues/55225)
                    .reset_index(name="completed_pipelines")
                )

                subject_data = pd.merge(
                    subject_data.reset_index(drop=True),
                    session_completed_pipeline_data,
                    on=["sub_id", "session_id", "session_type"],
                    how="left",
                )

                # TODO: Revisit this as there may be a more elegant solution.
                # The following code replaces columns with all NaN values with values of None, to ensure they show up in the final JSON as `null`.
                # This is needed as the above .agg() seems to turn NaN into None for object-type columns (which have some non-missing values)
                # but not for columns with all NaN, which end up with a column type of float64. This is a problem because
                # if the column corresponds to a SessionResponse attribute with an expected str type, then the column values will be converted
                # to the string "nan" in the response JSON, which we don't want.
                all_nan_columns = subject_data.columns[
                    subject_data.isna().all()
                ]
                subject_data[all_nan_columns] = subject_data[
                    all_nan_columns
                ].replace({np.nan: None})

                subject_data = list(subject_data.to_dict("records"))

            dataset_available_pipelines = (
                group.groupby("pipeline_name", dropna=True)["pipeline_version"]
                .apply(lambda x: list(x.dropna().unique()))
                .to_dict()
            )

            response_obj.append(
                CohortQueryResponse(
                    dataset_uuid=dataset_uuid,
                    dataset_name=dataset_name,
                    dataset_total_subjects=matching_dataset_sizes[
                        dataset_uuid
                    ],
                    dataset_portal_uri=(
                        group["dataset_portal_uri"].iloc[0]
                        if not group["dataset_portal_uri"].isna().any()
                        else None
                    ),
                    num_matching_subjects=group["sub_id"].nunique(),
                    records_protected=util.RETURN_AGG.val,
                    subject_data=subject_data,
                    image_modals=list(
                        group["image_modal"][
                            group["image_modal"].notna()
                        ].unique()
                    ),
                    available_pipelines=dataset_available_pipelines,
                )
            )

    return response_obj


async def get_terms(
    data_element_URI: str, term_labels_path: Path | None
) -> dict:
    """
    Makes a POST request to graph API using httpx where the payload is a SPARQL query generated by the create_terms_query function.

    Parameters
    ----------
    data_element_URI : str
        Controlled term of neurobagel class for which all the available terms should be retrieved.
    term_labels_path : Path
        Path to JSON file containing term-label mappings for the vocabulary of the data element URI.

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

    if term_labels_path is not None:
        vocab_term_lookup = util.load_json(term_labels_path)
    else:
        vocab_term_lookup = {}

    term_label_dicts = []
    for result in term_url_results["results"]["bindings"]:
        term_url = result["termURL"]["value"]
        # First, check whether the found instance of the data element contains a recognized namespace
        if util.is_term_namespace_in_context(term_url):
            # Then, attempt to get the label for the term
            term_label = vocab_term_lookup.get(
                util.strip_namespace_from_term_uri(term_url), None
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


async def get_term_labels_for_vocab(
    term_labels_path: Path, vocabulary_name: str, namespace_prefix: str
) -> VocabLabelsResponse:
    """
    Returns the term-label mappings along with the vocabulary namespace details for the specified vocabulary.

    Returns
    -------
    VocabLabelsResponse
    """
    term_labels = util.load_json(term_labels_path)

    return VocabLabelsResponse(
        vocabulary_name=vocabulary_name,
        namespace_url=util.CONTEXT[namespace_prefix],
        namespace_prefix=namespace_prefix,
        term_labels=term_labels,
    )
