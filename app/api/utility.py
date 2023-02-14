"""Constants for Stardog graph connection and utility functions for writing the SPARQL query."""

import os
from collections import namedtuple
from typing import Optional

# Request constants
DOG_ROOT = os.environ.get("DOG_ROOT", "206.12.99.17")
DOG_DB = "test_data"
DOG_PORT = 5820
QUERY_URL = f"http://{DOG_ROOT}:{DOG_PORT}/{DOG_DB}/query"
QUERY_HEADER = {
    "Content-Type": "application/sparql-query",
    "Accept": "application/sparql-results+json",
}

# SPARQL query context
DEFAULT_CONTEXT = """
PREFIX bg: <http://neurobagel.org/vocab/>
PREFIX snomed: <https://identifiers.org/snomedct:>
PREFIX nidm: <http://purl.org/nidash/nidm#>
"""

# Store domains in named tuples
Domain = namedtuple("Domain", ["var", "pred"])
# Core domains
AGE = Domain("age", "bg:age")
SEX = Domain("sex", "bg:sex")
DIAGNOSIS = Domain("diagnosis", "bg:diagnosis")
IS_CONTROL = Domain("subject_group", "bg:isSubjectGroup")
ASSESSMENT = Domain("assessment", "bg:assessment")
IMAGE_MODAL = Domain("image_modal", "bg:hasContrastType")
PROJECT = Domain("project", "bg:hasSamples")


CATEGORICAL_DOMAINS = [SEX, DIAGNOSIS, IMAGE_MODAL, ASSESSMENT]

IS_CONTROL_TERM = "http://purl.obolibrary.org/obo/NCIT_C94342"


def create_query(
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
        subject_level_filters += "\n" + f"FILTER (?{SEX.var} = '{sex}')."

    if diagnosis is not None:
        subject_level_filters += (
            "\n" + f"FILTER (?{DIAGNOSIS.var} = {diagnosis})."
        )

    if is_control is not None:
        if is_control:
            subject_level_filters += (
                "\n" + f"FILTER (?{IS_CONTROL.var} = <{IS_CONTROL_TERM}>)."
            )
        else:
            subject_level_filters += (
                "\n" + f"FILTER (?{IS_CONTROL.var} != <{IS_CONTROL_TERM}>)."
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

    query_template = f"""
    {DEFAULT_CONTEXT}

    SELECT ?dataset ?dataset_name ?sub_id ?file_path ?image_modal
    WHERE {{
    SELECT DISTINCT ?dataset ?dataset_name ?subject ?sub_id ?age ?sex
    ?diagnosis ?subject_group ?num_sessions ?assessment ?image_modal ?file_path
    WHERE {{
    ?dataset a bg:Dataset;
             bg:label ?dataset_name;
             bg:hasSamples ?subject.

    ?subject a bg:Subject;
            bg:label ?sub_id;
            bg:hasSession ?session;
            bg:hasSession/bg:hasAcquisition/bg:hasContrastType ?image_modal.

    OPTIONAL {{
        ?session bg:filePath ?file_path.
    }}
    OPTIONAL {{
        ?subject bg:age ?age.
    }}
    OPTIONAL {{
        ?subject bg:sex ?sex.
    }}
    OPTIONAL {{
        ?subject bg:diagnosis ?diagnosis.
    }}
    OPTIONAL {{
        ?subject bg:isSubjectGroup ?subject_group.
    }}
    OPTIONAL {{
        ?subject bg:assessment ?assessment.
    }}

    {{
    SELECT ?subject (count(distinct ?session) as ?num_sessions)
    WHERE {{
        ?subject a bg:Subject;
                 bg:hasSession ?session.
        ?session bg:hasAcquisition/bg:hasContrastType ?image_modal.
        {session_level_filters}

    }} GROUP BY ?subject
    }}

    {subject_level_filters}
}}
}} GROUP BY ?dataset ?dataset_name ?sub_id ?file_path ?image_modal
"""

    return query_template
