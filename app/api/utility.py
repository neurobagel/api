"""Constants for graph server connection and utility functions for writing the SPARQL query."""

import json
import os
import warnings
from collections import namedtuple
from pathlib import Path
from typing import Optional

import httpx

# Request constants
EnvVar = namedtuple("EnvVar", ["name", "val"])

ALLOWED_ORIGINS = EnvVar(
    "NB_API_ALLOWED_ORIGINS", os.environ.get("NB_API_ALLOWED_ORIGINS", "")
)

GRAPH_USERNAME = EnvVar(
    "NB_GRAPH_USERNAME", os.environ.get("NB_GRAPH_USERNAME")
)
GRAPH_PASSWORD = EnvVar(
    "NB_GRAPH_PASSWORD", os.environ.get("NB_GRAPH_PASSWORD")
)
GRAPH_ADDRESS = EnvVar(
    "NB_GRAPH_ADDRESS", os.environ.get("NB_GRAPH_ADDRESS", "206.12.99.17")
)
GRAPH_DB = EnvVar(
    "NB_GRAPH_DB", os.environ.get("NB_GRAPH_DB", "test_data/query")
)
GRAPH_PORT = EnvVar("NB_GRAPH_PORT", os.environ.get("NB_GRAPH_PORT", 5820))
# TODO: Environment variables can't be parsed as bool so this is a workaround but isn't ideal.
# Another option is to switch this to a command-line argument, but that would require changing the
# Dockerfile also since Uvicorn can't accept custom command-line args.
RETURN_AGG = EnvVar(
    "NB_RETURN_AGG", os.environ.get("NB_RETURN_AGG", "True").lower() == "true"
)

QUERY_URL = f"http://{GRAPH_ADDRESS.val}:{GRAPH_PORT.val}/{GRAPH_DB.val}"
QUERY_HEADER = {
    "Content-Type": "application/sparql-query",
    "Accept": "application/sparql-results+json",
}

CONTEXT = {
    "cogatlas": "https://www.cognitiveatlas.org/task/id/",
    "nb": "http://neurobagel.org/vocab/",
    "nbg": "http://neurobagel.org/graph/",  # TODO: Check if we still need this namespace.
    "ncit": "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#",
    "nidm": "http://purl.org/nidash/nidm#",
    "snomed": "http://purl.bioontology.org/ontology/SNOMEDCT/",
}

# Store domains in named tuples
Domain = namedtuple("Domain", ["var", "pred"])
# Core domains
AGE = Domain("age", "nb:hasAge")
SEX = Domain("sex", "nb:hasSex")
DIAGNOSIS = Domain("diagnosis", "nb:hasDiagnosis")
IS_CONTROL = Domain("subject_group", "nb:isSubjectGroup")
ASSESSMENT = Domain("assessment", "nb:hasAssessment")
IMAGE_MODAL = Domain("image_modal", "nb:hasContrastType")
PROJECT = Domain("project", "nb:hasSamples")


CATEGORICAL_DOMAINS = [SEX, DIAGNOSIS, IMAGE_MODAL, ASSESSMENT]

IS_CONTROL_TERM = "ncit:C94342"

BACKUP_VOCAB_DIR = (
    Path(__file__).absolute().parents[2] / "vocab/backup_external"
)


def parse_origins_as_list(allowed_origins: str) -> list:
    """Returns user-defined allowed origins as a list."""
    return list(allowed_origins.split(" "))


def create_context() -> str:
    """Creates a SPARQL query context string from the CONTEXT dictionary."""
    return "\n".join(
        [f"PREFIX {prefix}: <{uri}>" for prefix, uri in CONTEXT.items()]
    )


def create_query(
    return_agg: bool,
    age: Optional[tuple] = (None, None),
    sex: Optional[str] = None,
    diagnosis: Optional[str] = None,
    is_control: Optional[bool] = None,
    min_num_sessions: Optional[int] = None,
    assessment: Optional[str] = None,
    image_modal: Optional[str] = None,
) -> str:
    """
    Creates a SPARQL query using a query template and filters it using the input parameters.

    Parameters
    ----------
    return_agg : bool
        Whether to return only aggregate query results (and not subject-level attributes besides file paths).
    age : tuple, optional
        Minimum and maximum age of subject, by default (None, None).
    sex : str, optional
        Subject sex, by default None.
    diagnosis : str, optional
        Subject diagnosis, by default None.
    is_control : bool, optional
        Whether or not subject is a control, by default None.
    min_num_sessions : int, optional
        Subject minimum number of imaging sessions, by default None.
    assessment : str, optional
        Non-imaging assessment completed by subjects, by default None.
    image_modal : str, optional
        Imaging modality of subject scans, by default None.

    Returns
    -------
    str
        The SPARQL query.
    """
    subject_level_filters = ""

    if age[0] is not None:
        subject_level_filters += "\n" + f"FILTER (?{AGE.var} >= {age[0]})."
    if age[1] is not None:
        subject_level_filters += "\n" + f"FILTER (?{AGE.var} <= {age[1]})."

    if sex is not None:
        subject_level_filters += "\n" + f"FILTER (?{SEX.var} = {sex})."

    if diagnosis is not None:
        subject_level_filters += (
            "\n" + f"FILTER (?{DIAGNOSIS.var} = {diagnosis})."
        )

    if is_control is not None:
        if is_control:
            subject_level_filters += (
                "\n" + f"FILTER (?{IS_CONTROL.var} = {IS_CONTROL_TERM})."
            )
        else:
            subject_level_filters += (
                "\n" + f"FILTER (?{IS_CONTROL.var} != {IS_CONTROL_TERM})."
            )

    if min_num_sessions is not None:
        subject_level_filters += (
            "\n" + f"FILTER (?num_sessions >= {min_num_sessions})."
        )

    if assessment is not None:
        subject_level_filters += (
            "\n" + f"FILTER (?{ASSESSMENT.var} = {assessment})."
        )

    session_level_filters = ""

    if image_modal is not None:
        session_level_filters += (
            "\n" + f"FILTER (?{IMAGE_MODAL.var} = {image_modal})."
        )

    query_string = f"""
        SELECT DISTINCT ?dataset_uuid ?dataset_name ?dataset_portal_uri ?sub_id ?age ?sex
        ?diagnosis ?subject_group ?num_sessions ?session_id ?assessment ?image_modal ?session_file_path
        WHERE {{
            ?dataset_uuid a nb:Dataset;
                    nb:hasLabel ?dataset_name;
                    nb:hasSamples ?subject.
            ?subject a nb:Subject;
                    nb:hasLabel ?sub_id;
                    nb:hasSession ?session;
                    nb:hasSession/nb:hasAcquisition/nb:hasContrastType ?image_modal.
            ?session nb:hasLabel ?session_id.
            OPTIONAL {{
                ?dataset_uuid nb:hasPortalURI ?dataset_portal_uri.
            }}
            OPTIONAL {{
                ?session nb:hasFilePath ?session_file_path.
            }}
            OPTIONAL {{
                ?subject nb:hasAge ?age.
            }}
            OPTIONAL {{
                ?subject nb:hasSex ?sex.
            }}
            OPTIONAL {{
                ?subject nb:hasDiagnosis ?diagnosis.
            }}
            OPTIONAL {{
                ?subject nb:isSubjectGroup ?subject_group.
            }}
            OPTIONAL {{
                ?subject nb:hasAssessment ?assessment.
            }}
            {{
                SELECT ?subject (count(distinct ?session) as ?num_sessions)
                WHERE {{
                    ?subject a nb:Subject;
                            nb:hasSession ?session.
                    ?session nb:hasAcquisition/nb:hasContrastType ?image_modal.
                    {session_level_filters}
                }} GROUP BY ?subject
            }}
            {subject_level_filters}
        }}
    """

    # The query defined above will return all subject-level attributes from the graph. If RETURN_AGG variable has been set to true,
    # wrap query in an aggregating statement so data returned from graph include only attributes needed for dataset-level aggregate metadata.
    if return_agg:
        query_string = f"""
            SELECT ?dataset_uuid ?dataset_name ?dataset_portal_uri ?sub_id ?image_modal WHERE {{\n
            {query_string}
            \n}} GROUP BY ?dataset_uuid ?dataset_name ?dataset_portal_uri ?sub_id ?image_modal
        """

    return "\n".join([create_context(), query_string])


def create_terms_query(data_element_URI: str) -> str:
    """
    Creates a SPARQL query using a simple query template to retrieve term URLS for a given data element.

    Parameters
    ----------
    data_element_URI : str
        The URI of the data element for which to retrieve the URIs of all connected term.

    Returns
    -------
    str
        The SPARQL query.

    Examples
    --------
    get_terms_query("nb:Assessment")
    """

    query_string = f"""
    SELECT DISTINCT ?termURL
    WHERE {{
        ?termURL a {data_element_URI} .
        {data_element_URI} rdfs:subClassOf nb:ControlledTerm .
    }}
    """

    return "\n".join([create_context(), query_string])


def is_term_namespace_in_context(term_url: str) -> bool:
    """
    Performs basic check for if a term URL contains a namespace URI from the context.

    Parameters
    ----------
    url : str
        A controlled term URI.

    Returns
    -------
    bool
        True if the term URL contains a namespace URI from the context, False otherwise.
    """
    for uri in CONTEXT.values():
        if uri in term_url:
            return True
    return False


def strip_namespace_from_term_uri(term: str, has_prefix: bool = False) -> str:
    """
    Removes namespace URI or prefix from a term URI if the namespace is recognized.

    Parameters
    ----------
    uri : str
        A controlled term URI.

    Returns
    -------
    str
        The unique term ID.
    """
    if has_prefix:
        for prefix in CONTEXT:
            if prefix in term:
                return term.replace(prefix, "")
    elif not has_prefix:
        for uri in CONTEXT.values():
            if uri in term:
                return term.replace(uri, "")

    # If no match found within the context, return original term
    return term


def replace_namespace_uri(url: str) -> str:
    """
    Replaces namespace URIs in term URLs with corresponding prefixes from the context.

    Parameters
    ----------
    url : str
        A controlled term URL.

    Returns
    -------
    str
        The term with namespace URIs replaced with prefixes if found in the context, or the original URL.
    """
    for prefix, uri in CONTEXT.items():
        if uri in url:
            return url.replace(uri, f"{prefix}:")

    # If no match found within the context, return original URL
    return url


def load_json(path: Path) -> dict:
    """
    Loads a user-specified JSON file.

    Parameters
    ----------
    path : Path
        Path to JSON file.
    """
    with open(path, "r") as f:
        return json.load(f)


def fetch_and_save_cogatlas(output_path: Path):
    """
    Fetches the Cognitive Atlas vocabulary using its native Task API and writes term ID-label mappings to a temporary lookup file.
    If the API request fails, a backup copy of the vocabulary is used instead.

    Saves a JSON with keys corresponding to Cognitive Atlas task IDs and values corresponding to human-readable task names).

    Parameters
    ----------
    output_path : Path
        File path to store output vocabulary lookup file.
    """
    api_url = "https://www.cognitiveatlas.org/api/v-alpha/task?format=json"
    response = httpx.get(url=api_url)

    if response.is_success:
        vocab = response.json()
    else:
        warnings.warn(
            f"""
            The API was unable to fetch the Cognitive Atlas task vocabulary (https://www.cognitiveatlas.org/tasks/a/) from the source and will default to using a local backup copy of the vocabulary instead.

            Details of the response from the source:
            Status code {response.status_code}
            {response.reason_phrase}: {response.text}
            """
        )
        # Use backup copy of the raw vocabulary JSON
        vocab = load_json(BACKUP_VOCAB_DIR / "cogatlas_task.json")

    term_labels = {term["id"]: term["name"] for term in vocab}
    with open(output_path, "w") as f:
        f.write(json.dumps(term_labels, indent=2))
