"""Constants for graph server connection and utility functions for writing the SPARQL query."""

import json
import os
import textwrap
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
    "np": "https://github.com/nipoppy/pipeline-catalog/tree/main/processing/",
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
PIPELINE_NAME = Domain("pipeline_name", "nb:hasPipelineName")
PIPELINE_VERSION = Domain("pipeline_version", "nb:hasPipelineVersion")
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


def unpack_graph_response_json_to_dicts(response: dict) -> list[dict]:
    """
    Reformats a nested dictionary object from a SPARQL query response JSON into a list of dictionaries,
    where the keys are the variables selected in the SPARQL query and the values correspond to the variable values.
    The number of dictionaries should correspond to the number of query matches.
    """
    return [
        {k: v["value"] for k, v in res.items()}
        for res in response["results"]["bindings"]
    ]


def create_bound_filter(var: str) -> str:
    """
    Create a SPARQL filter substring for checking if a variable is bound
    (meaning the variable actually has a corresponding value, e.g., the property exists).
    """
    return f"FILTER (BOUND(?{var})"


def create_query(
    return_agg: bool,
    age: Optional[tuple] = (None, None),
    sex: Optional[str] = None,
    diagnosis: Optional[str] = None,
    is_control: Optional[bool] = None,
    min_num_imaging_sessions: Optional[int] = None,
    min_num_phenotypic_sessions: Optional[int] = None,
    assessment: Optional[str] = None,
    image_modal: Optional[str] = None,
    pipeline_name: Optional[str] = None,
    pipeline_version: Optional[str] = None,
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
    min_num_imaging_sessions : int, optional
        Subject minimum number of imaging sessions, by default None.
    min_num_phenotypic_sessions : int, optional
        Subject minimum number of phenotypic sessions, by default None.
    assessment : str, optional
        Non-imaging assessment completed by subjects, by default None.
    image_modal : str, optional
        Imaging modality of subject scans, by default None.
    pipeline_name : str, optional
        Name of pipeline run on subject scans, by default None.
    pipeline_version : str, optional
        Version of pipeline run on subject scans, by default None.

    Returns
    -------
    str
        The SPARQL query.
    """
    subject_level_filters = ""
    if min_num_phenotypic_sessions is not None:
        subject_level_filters += (
            "\n"
            + f"FILTER (?num_matching_phenotypic_sessions >= {min_num_phenotypic_sessions})."
        )
    if min_num_imaging_sessions is not None:
        subject_level_filters += (
            "\n"
            + f"FILTER (?num_matching_imaging_sessions >= {min_num_imaging_sessions})."
        )

    phenotypic_session_level_filters = ""

    if age[0] is not None:
        phenotypic_session_level_filters += (
            "\n"
            + f"{create_bound_filter(AGE.var)} && ?{AGE.var} >= {age[0]})."
        )
    if age[1] is not None:
        phenotypic_session_level_filters += (
            "\n"
            + f"{create_bound_filter(AGE.var)} && ?{AGE.var} <= {age[1]})."
        )

    if sex is not None:
        phenotypic_session_level_filters += (
            "\n" + f"{create_bound_filter(SEX.var)} && ?{SEX.var} = {sex})."
        )

    if diagnosis is not None:
        phenotypic_session_level_filters += (
            "\n"
            + f"{create_bound_filter(DIAGNOSIS.var)} && ?{DIAGNOSIS.var} = {diagnosis})."
        )

    # TODO: Simple equivalence to the URI for Healthy Control only works for the condition is_control=True,
    # since otherwise the subject node wouldn't be expected to have the property nb:hasSubjectGroup at all.
    # If we decide to support queries of is_control = False (i.e., give me all subjects that are *not* controls / have
    # at least one diagnosis), we can use something like `FILTER (!BOUND(?{IS_CONTROL.var}))` to
    # return only subjects missing the property nb:hasSubjectGroup.
    # Related: https://github.com/neurobagel/api/issues/247
    if is_control is True:
        phenotypic_session_level_filters += (
            "\n"
            + f"{create_bound_filter(IS_CONTROL.var)} && ?{IS_CONTROL.var} = {IS_CONTROL_TERM})."
        )

    if assessment is not None:
        phenotypic_session_level_filters += (
            "\n"
            + f"{create_bound_filter(ASSESSMENT.var)} && ?{ASSESSMENT.var} = {assessment})."
        )

    imaging_session_level_filters = ""
    if image_modal is not None:
        imaging_session_level_filters += (
            "\n"
            + f"{create_bound_filter(IMAGE_MODAL.var)} && ?{IMAGE_MODAL.var} = {image_modal})."
        )

    if pipeline_name is not None:
        imaging_session_level_filters += (
            "\n"
            + f"{create_bound_filter(PIPELINE_NAME.var)} && ?{PIPELINE_NAME.var} = {pipeline_name})."
        )

    # In case a user specified the pipeline version but not the name
    if pipeline_version is not None:
        imaging_session_level_filters += (
            "\n"
            + f'{create_bound_filter(PIPELINE_VERSION.var)} && ?{PIPELINE_VERSION.var} = "{pipeline_version}").'  # Wrap with quotes to avoid workaround implicit conversion
        )

    query_string = textwrap.dedent(
        f"""
        SELECT DISTINCT ?dataset_uuid ?dataset_name ?dataset_portal_uri ?sub_id ?age ?sex
        ?diagnosis ?subject_group ?num_matching_phenotypic_sessions ?num_matching_imaging_sessions
        ?session_id ?session_type ?assessment ?image_modal ?session_file_path ?pipeline_name ?pipeline_version
        WHERE {{
            ?dataset_uuid a nb:Dataset;
                nb:hasLabel ?dataset_name;
                nb:hasSamples ?subject.
            ?subject a nb:Subject;
                nb:hasLabel ?sub_id;
                nb:hasSession ?session.
            VALUES ?session_type {{nb:ImagingSession nb:PhenotypicSession}}
            ?session a ?session_type;
                nb:hasLabel ?session_id.
            OPTIONAL {{
                ?session nb:hasAcquisition/nb:hasContrastType ?image_modal.
                OPTIONAL {{?session nb:hasFilePath ?session_file_path.}}
            }}
            OPTIONAL {{?dataset_uuid nb:hasPortalURI ?dataset_portal_uri.}}
            OPTIONAL {{?session nb:hasAge ?age.}}
            OPTIONAL {{?session nb:hasSex ?sex.}}
            OPTIONAL {{?session nb:hasDiagnosis ?diagnosis.}}
            OPTIONAL {{?session nb:isSubjectGroup ?subject_group.}}
            OPTIONAL {{?session nb:hasAssessment ?assessment.}}
            {{
                SELECT ?subject (count(distinct ?phenotypic_session) as ?num_matching_phenotypic_sessions)
                WHERE {{
                    ?subject nb:hasSession ?phenotypic_session.
                    ?phenotypic_session a nb:PhenotypicSession.

                    OPTIONAL {{?phenotypic_session nb:hasAge ?age.}}
                    OPTIONAL {{?phenotypic_session nb:hasSex ?sex.}}
                    OPTIONAL {{?phenotypic_session nb:hasDiagnosis ?diagnosis.}}
                    OPTIONAL {{?phenotypic_session nb:isSubjectGroup ?subject_group.}}
                    OPTIONAL {{?phenotypic_session nb:hasAssessment ?assessment.}}

                    {phenotypic_session_level_filters}
                }} GROUP BY ?subject
            }}

            OPTIONAL {{
                ?session nb:hasCompletedPipeline ?pipeline.
                ?pipeline nb:hasPipelineVersion ?pipeline_version.
                ?pipeline nb:hasPipelineName ?pipeline_name.
            }}
            {{
                SELECT ?subject (count(distinct ?imaging_session) as ?num_matching_imaging_sessions)
                WHERE {{
                    ?subject a nb:Subject.
                    OPTIONAL {{
                        ?subject nb:hasSession ?imaging_session.
                        ?imaging_session a nb:ImagingSession.

                        OPTIONAL {{
                            ?imaging_session nb:hasAcquisition ?acquisition.
                            ?acquisition nb:hasContrastType ?image_modal.
                        }}

                        OPTIONAL {{
                            ?imaging_session nb:hasCompletedPipeline ?pipeline.
                            ?pipeline nb:hasPipelineName ?pipeline_name;
                            nb:hasPipelineVersion ?pipeline_version.
                        }}
                    }}
                    {imaging_session_level_filters}
                }} GROUP BY ?subject
            }}
            {subject_level_filters}
        }}
    """
    )

    # The query defined above will return all subject-level attributes from the graph. If RETURN_AGG variable has been set to true,
    # wrap query in an aggregating statement so data returned from graph include only attributes needed for dataset-level aggregate metadata.
    if return_agg:
        query_string = (
            textwrap.dedent(
                """
            SELECT ?dataset_uuid ?dataset_name ?dataset_portal_uri ?sub_id ?image_modal ?pipeline_version ?pipeline_name
            WHERE {"""
            )
            + textwrap.indent(query_string, "    ")
            + "} GROUP BY ?dataset_uuid ?dataset_name ?dataset_portal_uri ?sub_id ?image_modal ?pipeline_version ?pipeline_name"
        )

    return "\n".join([create_context(), query_string])


def create_multidataset_size_query(dataset_uuids: list) -> str:
    """Construct a SPARQL query to retrieve the number of subjects in each dataset in a list of dataset UUIDs."""
    dataset_uuids_string = "\n".join([f"<{uuid}>" for uuid in dataset_uuids])
    query_string = f"""
        SELECT ?dataset_uuid (COUNT(DISTINCT ?subject) as ?total_subjects)
        WHERE {{
            VALUES ?dataset_uuid {{
                {dataset_uuids_string}
            }}
            ?dataset_uuid nb:hasSamples ?subject.
            ?subject a nb:Subject.
        }} GROUP BY ?dataset_uuid
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
    term_url : str
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
    term : str
        A controlled term URI.
    has_prefix : bool, optional
        Whether the term URI includes a namespace prefix (as opposed to the full namespace URI), by default False.

    Returns
    -------
    str
        The unique term ID.
    """
    if has_prefix:
        term_split = term.rsplit(":", 1)
        if term_split[0] in CONTEXT:
            return term_split[1]
    else:
        for uri in CONTEXT.values():
            if uri in term:
                return term.replace(uri, "")

    # If no match found within the context, return original term
    return term


def replace_namespace_uri_with_prefix(url: str) -> str:
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

    Saves a JSON with keys corresponding to Cognitive Atlas task IDs and values corresponding to human-readable task names.

    Parameters
    ----------
    output_path : Path
        File path to store output vocabulary lookup file.
    """
    api_url = "https://www.cognitiveatlas.org/api/v-alpha/task?format=json"

    try:
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
    except httpx.NetworkError as exc:
        warnings.warn(
            f""""
            Fetching of the Cognitive Atlas task vocabulary (https://www.cognitiveatlas.org/tasks/a/) from the source failed due to a network error.
            The API will default to using a local backup copy of the vocabulary instead.

            Error: {exc}
            """
        )
        # Use backup copy of the raw vocabulary JSON
        vocab = load_json(BACKUP_VOCAB_DIR / "cogatlas_task.json")

    term_labels = {term["id"]: term["name"] for term in vocab}
    with open(output_path, "w") as f:
        f.write(json.dumps(term_labels, indent=2))


def create_snomed_term_lookup(output_path: Path):
    """
    Reads in a file of disorder terms from the SNOMED CT vocabulary and writes term ID-label mappings to a temporary lookup file.

    Saves a JSON with keys corresponding to SNOMED CT IDs and values corresponding to human-readable term names.

    Parameters
    ----------
    output_path : Path
        File path to store output vocabulary lookup file.
    """
    vocab = load_json(BACKUP_VOCAB_DIR / "snomedct_disorder.json")

    term_labels = {term["sctid"]: term["preferred_name"] for term in vocab}
    with open(output_path, "w") as f:
        f.write(json.dumps(term_labels, indent=2))


def create_pipeline_versions_query(pipeline: str) -> str:
    """Create a SPARQL query for all versions of a pipeline available in a graph."""
    query_string = textwrap.dedent(
        f"""\
    SELECT DISTINCT ?pipeline_version
    WHERE {{
        ?completed_pipeline a nb:CompletedPipeline;
            nb:hasPipelineName {pipeline};
            nb:hasPipelineVersion ?pipeline_version.
    }}"""
    )
    return "\n".join([create_context(), query_string])
