"""Constants for graph server connection and utility functions for writing the SPARQL query."""

import textwrap
from collections import namedtuple
from typing import Any, Literal, Optional

import httpx
import numpy as np
import pandas as pd

from . import config

QUERY_HEADER = {
    "Content-Type": "application/sparql-query",
    "Accept": "application/sparql-results+json",
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


def parse_origins_as_list(allowed_origins: str | None) -> list:
    """Returns user-defined allowed origins as a list."""
    return list(allowed_origins.split(" ")) if allowed_origins else []


# TODO: Consider switching to PyGitHub if we need more complex operations
def request_data(url: str, err_message: str) -> Any:
    try:
        with httpx.Client() as client:
            response = client.get(url)
            response.raise_for_status()
            data = response.json()

        return data
    except httpx.HTTPError as e:
        raise RuntimeError(
            f"{err_message}. Error: {e}\n"
            "Please check that you have an internet connection. "
            "If the problem persists, please open an issue in https://github.com/neurobagel/api/issues."
        ) from e


def create_query_context(context: dict) -> str:
    """Creates a SPARQL query context string from the context dictionary."""
    return "\n".join(
        [f"PREFIX {prefix}: <{uri}>" for prefix, uri in context.items()]
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
    is_control: Literal[True, None] = None,
    min_num_imaging_sessions: Optional[int] = None,
    min_num_phenotypic_sessions: Optional[int] = None,
    assessment: Optional[str] = None,
    image_modal: Optional[str] = None,
    pipeline_name: Optional[str] = None,
    pipeline_version: Optional[str] = None,
    dataset_uuids: Optional[list] = None,
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
    is_control : {True, None}, optional
        If True, return only healthy control subjects.
        If None (default), return all matching subjects.
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
    dataset_uuids : list[str], optional
        List of datasets to restrict the query to, by default None (all datasets).

    Returns
    -------
    str
        The SPARQL query.
    """
    subject_level_filters = ""
    datasets_filter = ""

    # Include all datasets when the user does not provide the dataset_uuids parameter/field,
    # or if they explicitly provide an empty list
    if dataset_uuids:
        datasets_filter = (
            "\n"
            + f"VALUES ?dataset_uuid {{ {' '.join([f'<{uuid}>' for uuid in dataset_uuids])} }}"
        )

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
            {datasets_filter}
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

    # The query defined above will return all subject-level attributes from the graph. If aggregate results have been enabled,
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

    return "\n".join([create_query_context(config.CONTEXT), query_string])


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

    return "\n".join([create_query_context(config.CONTEXT), query_string])


def construct_matching_sub_results_for_dataset(
    matching_records: pd.DataFrame,
) -> list:
    subject_data = matching_records.groupby(
        by=["sub_id", "session_id", "session_type"],
        dropna=True,
    ).agg(
        {
            "sub_id": "first",
            "session_id": "first",
            "num_matching_phenotypic_sessions": "first",
            "num_matching_imaging_sessions": "first",
            "session_type": "first",
            "age": "first",
            "sex": "first",
            "diagnosis": lambda record_group: list(record_group.unique()),
            "subject_group": "first",
            "assessment": lambda record_group: list(record_group.unique()),
            "image_modal": lambda record_group: list(record_group.unique()),
            "session_file_path": "first",
        }
    )

    # Get the unique versions of each pipeline that was run on each session
    pipeline_grouped_data = (
        matching_records.groupby(
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
                "pipeline_version": lambda record_group: list(
                    record_group.dropna().unique()
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
    all_nan_columns = subject_data.columns[subject_data.isna().all()]
    subject_data[all_nan_columns] = subject_data[all_nan_columns].replace(
        {np.nan: None}
    )

    subject_data = list(subject_data.to_dict("records"))

    return subject_data


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
    """

    query_string = f"""
    SELECT DISTINCT ?termURL
    WHERE {{
        ?termURL a {data_element_URI} .
        {data_element_URI} rdfs:subClassOf nb:ControlledTerm .
    }}
    """

    return "\n".join([create_query_context(config.CONTEXT), query_string])


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
    for uri in config.CONTEXT.values():
        if uri in term_url:
            return True
    return False


def strip_namespace_from_term_uri(
    term: str, has_prefix: bool = False
) -> tuple[str | None, str]:
    """
    Removes namespace URL or prefix from a term URI if the namespace is recognized.

    Parameters
    ----------
    term : str
        A controlled term URI.
    has_prefix : bool, optional
        Whether the term URI includes a namespace prefix (as opposed to the full namespace URL), by default False.

    Returns
    -------
    tuple[str, str]
        The stripped namespace URL/prefix and the term ID.
    """
    if has_prefix:
        term_prefix, term_id = term.rsplit(":", 1)
        return term_prefix, term_id

    for term_url in config.CONTEXT.values():
        if term_url in term:
            return term_url, term[len(term_url) :]

    # If no match found within the context, return original term
    return None, term


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
    for prefix, uri in config.CONTEXT.items():
        if uri in url:
            return url.replace(uri, f"{prefix}:")

    # If no match found within the context, return original URL
    return url


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
    return "\n".join([create_query_context(config.CONTEXT), query_string])
