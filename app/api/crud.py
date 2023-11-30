"""CRUD functions called by path operations."""

import os
import warnings
from pathlib import Path

import httpx
import pandas as pd
from fastapi import HTTPException, status

from . import utility as util
from .models import CohortQueryResponse, VocabLabelsResponse

# Order that dataset and subject-level attributes should appear in the API JSON response.
# This order is defined explicitly because when graph-returned results are transformed to a dataframe,
# the default order of columns may be different than the order that variables are given in the SPARQL SELECT state
ATTRIBUTES_ORDER = [
    "sub_id",
    "num_sessions",
    "session_id",
    "session_file_path",
    "age",
    "sex",
    "diagnosis",
    "subject_group",
    "assessment",
    "image_modal",
    "dataset_name",
    "dataset_uuid",
    "dataset_portal_uri",
]


def post_query_to_graph(query: str, timeout: float = 5.0) -> dict:
    """
    Makes a post request to the graph API to perform a query, using parameters from the environment.
    Parameters
    ----------
    query : str
        The full SPARQL query string.
    timeout : float, optional
        The maximum duration for the request, by default 5.0 seconds.

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


async def get(
    min_age: float,
    max_age: float,
    sex: str,
    diagnosis: str,
    is_control: bool,
    min_num_sessions: int,
    assessment: str,
    image_modal: str,
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
    min_num_sessions : int
        Subject minimum number of imaging sessions.
    assessment : str
        Non-imaging assessment completed by subjects.
    image_modal : str
        Imaging modality of subject scans.

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
            min_num_sessions=min_num_sessions,
            assessment=assessment,
            image_modal=image_modal,
        ),
        # TODO: Revisit timeout value when query performance is improved
        timeout=30.0,
    )
    results_df = pd.DataFrame(
        util.unpack_http_response_json_to_dicts(results)
    ).reindex(columns=ATTRIBUTES_ORDER)

    # Get the total number of subjects in each dataset that matched the query
    matching_dataset_size_results = post_query_to_graph(
        util.create_multidataset_size_query(
            results_df["dataset_uuid"].unique()
        )
    )
    matching_dataset_sizes = {
        ds["dataset_uuid"]: int(ds["total_subjects"])
        for ds in util.unpack_http_response_json_to_dicts(
            matching_dataset_size_results
        )
    }

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
                    # TODO: Switch back to dropna=True once phenotypic sessions are implemented, as all subjects will have at least one non-null session ID
                    .groupby(by=["sub_id", "session_id"], dropna=False).agg(
                        {
                            "sub_id": "first",
                            "session_id": "first",
                            "num_sessions": "first",
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
                subject_data = list(subject_data.to_dict("records"))

            response_obj.append(
                CohortQueryResponse(
                    dataset_uuid=dataset_uuid,
                    dataset_name=dataset_name,
                    dataset_total_subjects=matching_dataset_sizes[
                        dataset_uuid
                    ],
                    dataset_portal_uri=group["dataset_portal_uri"].iloc[0]
                    if group["dataset_portal_uri"].notna().all()
                    else None,
                    num_matching_subjects=group["sub_id"].nunique(),
                    records_protected=util.RETURN_AGG.val,
                    subject_data=subject_data,
                    image_modals=list(
                        group["image_modal"][
                            group["image_modal"].notna()
                        ].unique()
                    ),
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
