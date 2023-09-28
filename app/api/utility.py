"""Constants for Stardog graph connection and utility functions for writing the SPARQL query."""

import os
from collections import namedtuple
from typing import Optional

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

# SPARQL query context
DEFAULT_CONTEXT = """
PREFIX cogatlas: <https://www.cognitiveatlas.org/task/id/>
PREFIX nb: <http://neurobagel.org/vocab/>
PREFIX nbg: <http://neurobagel.org/graph/>
PREFIX ncit: <http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#>
PREFIX nidm: <http://purl.org/nidash/nidm#>
PREFIX snomed: <http://purl.bioontology.org/ontology/SNOMEDCT/>
"""

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


def parse_origins_as_list(allowed_origins: str) -> list:
    """Returns user-defined allowed origins as a list."""
    return list(allowed_origins.split(" "))


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
            SELECT ?dataset_uuid ?dataset_name ?dataset_portal_uri ?sub_id ?session_file_path ?image_modal WHERE {{\n
            {query_string}
            \n}} GROUP BY ?dataset_uuid ?dataset_name ?dataset_portal_uri ?sub_id ?session_file_path ?image_modal
        """

    return "\n".join([DEFAULT_CONTEXT, query_string])


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
        ?termURL a {data_element_URI}.
    }}
    """

    return "\n".join([DEFAULT_CONTEXT, query_string])
