"""Contains constants for Stardog graph connection and a utility function for writing the SPARQL query."""

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


def create_query(
    age: tuple = (None, None),
    sex: str = None,
    image_modal: str = None,
    diagnosis: str = None,
    tool: str = None,
    control: bool = None,
    num_sessions: int = None,
) -> str:
    """Creates a SPARQL query using a query template and adds filters to the query using the input parameters.

    Parameters
    ----------
    age : tuple, optional
        Subjects' age (upper bound, lower bound), by default (None, None).
    sex : str, optional
        Subjects' sex, by default None.
    image_modal : str, optional
        Subjects' imaging modality, by default None.
    diagnosis : str, optional
        Subjects' diagnosis, by default None.
    tool : str, optional
        Tool, by default None.
    control : bool, optional
        Whether the subject was part of the control group, by default None.
    num_sessions : int, optional
        Subjects' number of scanning sessions, by default None.

    Returns
    -------
    str
        The SPARQL query.
    """
    subject_level_filters = ""
    if (
        isinstance(age, tuple)
        and not age == (None, None)
        and not age == ("", "")
    ):
        # TODO: revisit this and replace this solution with one that just
        # doesn't add the filter condition.
        age = tuple(
            (
                default_val if age_val is None else age_val
                for age_val, default_val in zip(age, [0, 100])
            )
        )
        subject_level_filters += (
            "\n" + f"FILTER (?{AGE.var} > {age[0]} && ?{AGE.var} < {age[1]})."
        )
    if sex is not None and not sex == "":
        # select_str += f' ?{GENDER_VAR}'
        subject_level_filters += "\n" + f"FILTER (?{SEX.var} = '{sex}')."

    if diagnosis is not None and not diagnosis == "" and not control:
        # select_str += ' ?diagnosis'
        subject_level_filters += (
            "\n" + f"FILTER (?{DIAGNOSIS.var} = <{diagnosis}>)."
        )

    # TODO: implement the check for control subjects (once we have control
    # subjects in the meta data)
    if control is not None and not control == "" and not diagnosis:
        subject_level_filters += (
            "\n" + f"FILTER (?{DIAGNOSIS.var} = <{control}>)."
        )

    if num_sessions is not None:
        subject_level_filters += (
            "\n" + f"FILTER (?number_session > {num_sessions})"
        )

    session_level_filters = ""
    if image_modal is not None and not image_modal == "":
        session_level_filters += (
            "\n" + f"FILTER (?{IMAGE_MODAL.var} = <{image_modal}>)."
        )

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
