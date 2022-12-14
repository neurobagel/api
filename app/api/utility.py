"""Constants for Stardog graph connection and utility functions for writing the SPARQL query."""

from collections import namedtuple

# For the request
DOG_ROOT = "http://206.12.99.17"
DOG_DB = "test_data"
DOG_PORT = 5820
QUERY_URL = f"{DOG_ROOT}:{DOG_PORT}/{DOG_DB}/query"
QUERY_HEADER = {
    "Content-Type": "application/sparql-query",
    "Accept": "application/sparql-results+json",
}

# For the SPARQL query
DEFAULT_CONTEXT = """
PREFIX bg: <http://neurobagel.org/vocab/>
PREFIX snomed: <http://neurobagel.org/snomed/>
PREFIX nidm: <http://purl.org/nidash/nidm#>
"""

# Store domains in named tuples
Domain = namedtuple("Domain", ["var", "pred"])
# Core domains
AGE = Domain("age", "bg:hasAge")
SEX = Domain("sex", "bg:sex")
DIAGNOSIS = Domain("diagnosis", "bg:diagnosis")
IMAGE_MODAL = Domain("image_modal", "bg:hasContrastType")
TOOL = Domain("tool", "")
PROJECT = Domain("project", "bg:hasSamples")
CONTROL = Domain("nidm:Control", "nidm:isSubjectGroup")

CATEGORICAL_DOMAINS = [SEX, DIAGNOSIS, IMAGE_MODAL]


def create_query(age: tuple = (None, None), sex: str = None) -> str:
    """
    Creates a SPARQL query using a query template and adds filters to the query using the input parameters.

    Parameters
    ----------
    age : tuple, optional
        Minimum and maximum age of subject, by default (None, None).
    sex : str, optional
        Subject sex, by default None.

    Returns
    -------
    str
        The SPARQL query.
    """
    subject_level_filters = ""

    if isinstance(age, tuple):
        if age[0] is not None:
            subject_level_filters += "\n" + f"FILTER (?{AGE.var} >= {age[0]})."
        if age[1] is not None:
            subject_level_filters += "\n" + f"FILTER (?{AGE.var} <= {age[1]})."

    if sex is not None and not sex == "":
        # select_str += f' ?{GENDER_VAR}'
        subject_level_filters += "\n" + f"FILTER (?{SEX.var} = '{sex}')."

    session_level_filters = ""

    query_template = f"""
    {DEFAULT_CONTEXT}

    SELECT DISTINCT ?dataset ?dataset_name ?subject ?sub_id ?age ?sex
    ?diagnosis ?modality ?number_session
    WHERE {{
    ?dataset a bg:Dataset;
             bg:label ?dataset_name;
             bg:hasSamples ?subject.

    ?subject a bg:Subject;
            bg:label ?sub_id;
            bg:age ?age;
            bg:sex ?sex;
            bg:diagnosis ?diagnosis;
            bg:hasSession/bg:hasAcquisition/bg:hasContrastType ?modality.

    {{
    SELECT ?subject (count(distinct ?session) as ?number_session)
    WHERE {{
        ?subject a bg:Subject;
                 bg:hasSession ?session.
        ?session bg:hasAcquisition/bg:hasContrastType ?modality.
        {session_level_filters}

    }} GROUP BY ?subject
    }}

    {subject_level_filters}
}}"""

    return query_template
