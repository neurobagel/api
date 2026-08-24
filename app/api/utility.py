"""Constants for graph server connection and utility functions for writing the SPARQL query."""

import json
import textwrap
from collections import namedtuple
from pathlib import Path
from typing import Any

import httpx
import numpy as np
import pandas as pd
from pydantic import BaseModel

from . import env_settings, sparql_models
from .logger import get_logger, log_and_raise_error
from .models import (
    IMAGING_FILTERS,
    PHENOTYPIC_FILTERS,
    PipelineQuery,
    QueryModel,
)

logger = get_logger(__name__)

QUERY_HEADER = {
    "Content-Type": "application/sparql-query",
    "Accept": "application/sparql-results+json",
}

# Mapping of categorical standardized variables to catalog dataset metadata fields and
# corresponding query fields
CATALOG_DATASET_TERM_FILTER_FIELDS = {
    "nb:Assessment": {
        "query_field": "assessment",
        "catalog_field": "available_assessments",
    },
    "nb:Diagnosis": {
        "query_field": "diagnosis",
        "catalog_field": "available_diagnoses",
    },
    "nb:Sex": {
        "query_field": "sex",
        "catalog_field": "available_sex",
    },
}

# TODO: Consider removing these namedtuples - they don't necessarily increase readability of query templates
# Store domains in named tuples
Domain = namedtuple("Domain", ["var", "pred"])
# Core domains
AGE = Domain("age", "nb:hasAge")
SEX = Domain("sex", "nb:hasSex")
DIAGNOSIS = Domain("diagnosis", "nb:hasDiagnosis")
ASSESSMENT = Domain("assessment", "nb:hasAssessment")
IMAGE_MODAL = Domain("image_modal", "nb:hasContrastType")
PIPELINE_NAME = Domain("pipeline_name", "nb:hasPipelineName")
PIPELINE_VERSION = Domain("pipeline_version", "nb:hasPipelineVersion")
PROJECT = Domain("project", "nb:hasSamples")


CATEGORICAL_DOMAINS = [SEX, DIAGNOSIS, IMAGE_MODAL, ASSESSMENT]


def load_json(path: Path) -> dict:
    """Load a JSON file as a dictionary."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_origins_as_list(allowed_origins: str | None) -> list:
    """Returns user-defined allowed origins as a list."""
    return list(allowed_origins.split(" ")) if allowed_origins else []


def create_gh_raw_content_url(repo: str, content_path: str) -> str:
    """
    Create a raw content URL for a given path in a specific GitHub repository.

    NOTE: We use raw URLs instead of the GitHub API to avoid rate limits when working without a token.
    """
    return f"https://raw.githubusercontent.com/{repo}/refs/heads/main/{content_path}"


def request_data(url: str, err_message: str) -> Any:
    """Request JSON data from a given URL. Log an error and exit if the request fails."""
    try:
        with httpx.Client() as client:
            response = client.get(url)
            response.raise_for_status()
            data = response.json()

        return data
    except httpx.HTTPError as e:
        log_and_raise_error(
            logger,
            RuntimeError,
            f"{err_message}. Error: {e}\n"
            "Please check that you have an internet connection. "
            "If the problem persists, please open an issue in https://github.com/neurobagel/api/issues.",
        )


def create_query_context(context: dict) -> str:
    """Creates a SPARQL query context string from the context dictionary."""
    return "\n".join(
        [f"PREFIX {prefix}: <{uri}>" for prefix, uri in context.items()]
    )


def add_sparql_context_to_query(query_body: str) -> str:
    """Adds the SPARQL query context to a given query body."""
    return "\n".join([create_query_context(env_settings.CONTEXT), query_body])


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
    age: tuple[float | None, float | None],
    sex: str | None,
    diagnosis: list[str] | None,
    min_num_imaging_sessions: int | None,
    min_num_phenotypic_sessions: int | None,
    assessment: list[str],
    image_modal: list[str],
    pipeline: list[PipelineQuery],
    dataset_uuids: list[str] | None,
) -> str:
    """
    Creates a SPARQL query using a query template and filters it using the input parameters.

    Parameters
    ----------
    return_agg : bool
        Whether to return only aggregate query results (and not subject-level attributes besides file paths).
    age : tuple[float | None, float | None
        Minimum and maximum age of subject, by default (None, None).
    sex : str
        Subject sex, by default None.
    diagnosis : list[str]
        Subject diagnosis, by default None.
    min_num_imaging_sessions : int
        Subject minimum number of imaging sessions, by default None.
    min_num_phenotypic_sessions : int
        Subject minimum number of phenotypic sessions, by default None.
    assessment : list[str]
        Non-imaging assessment completed by subjects, by default None.
    image_modal : list[str]
        Imaging modality of subject scans, by default None.
    pipeline : list[dict[str, str]]
        Pipeline run on subject scans, by default None.
    dataset_uuids : list[str]
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

    if diagnosis:
        phenotypic_session_level_filters += "".join(
            f"\n?phenotypic_session nb:hasDiagnosis {diagnosis_value}."
            for diagnosis_value in diagnosis
        )

    if assessment:
        phenotypic_session_level_filters += "".join(
            f"\n?phenotypic_session nb:hasAssessment {assessment_value}."
            for assessment_value in assessment
        )

    imaging_session_level_filters = ""
    if image_modal:
        imaging_session_level_filters += "".join(
            f"\n?imaging_session nb:hasAcquisition/nb:hasContrastType {image_modal_value}."
            for image_modal_value in image_modal
        )

    if pipeline:
        for pipeline_count, pipeline_info in enumerate(pipeline, start=1):
            pipeline_name = pipeline_info.name
            pipeline_version = pipeline_info.version

            if pipeline_name is not None:
                imaging_session_level_filters += (
                    f"\n?imaging_session nb:hasCompletedPipeline ?pipeline{pipeline_count}."
                    f"\n?pipeline{pipeline_count} nb:hasPipelineName {pipeline_name}."
                )
                if pipeline_version is not None:
                    imaging_session_level_filters += f'\n?pipeline{pipeline_count} nb:hasPipelineVersion "{pipeline_version}".'

    query_string = textwrap.dedent(f"""
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
            OPTIONAL {{?dataset_uuid nb:hasAccessLink ?dataset_portal_uri.}}
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
    """)

    # The query defined above will return all subject-level attributes from the graph. If aggregate results have been enabled,
    # wrap query in an aggregating statement so data returned from graph include only attributes needed for dataset-level aggregate metadata.
    if return_agg:
        query_string = (
            textwrap.dedent("""
            SELECT ?dataset_uuid ?dataset_name ?dataset_portal_uri ?sub_id ?image_modal ?pipeline_version ?pipeline_name
            WHERE {""")
            + textwrap.indent(query_string, "    ")
            + "} GROUP BY ?dataset_uuid ?dataset_name ?dataset_portal_uri ?sub_id ?image_modal ?pipeline_version ?pipeline_name"
        )

    return query_string


def create_multidataset_size_query(dataset_uuids: list[str]) -> str:
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

    return query_string


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

    return query_string


def is_term_namespace_in_context(
    term_url: str, has_prefix: bool = False
) -> bool:
    """
    Performs basic check for if a term URL contains a namespace URI from the context.

    Parameters
    ----------
    term_url : str
        A controlled term URI.

    has_prefix : bool, optional
        Whether the term URI includes a namespace prefix (as opposed to the full namespace URL).

    Returns
    -------
    bool
        True if the term URL contains a namespace URI from the context, False otherwise.
    """
    namespaces = (
        [f"{prefix}:" for prefix in env_settings.CONTEXT]
        if has_prefix
        else list(env_settings.CONTEXT.values())
    )
    return any(term_url.startswith(namespace) for namespace in namespaces)


def split_namespace_from_term_uri(
    term: str, has_prefix: bool = False
) -> tuple[str | None, str]:
    """
    Splits namespace URI or prefix from a term URI if the namespace is recognized.

    Parameters
    ----------
    term : str
        A controlled term URI.
    has_prefix : bool, optional
        Whether the term URI includes a namespace prefix (as opposed to the full namespace URL), by default False.

    Returns
    -------
    tuple[str | None, str]
        The stripped namespace URL/prefix and the term ID.
    """
    if has_prefix:
        term_prefix, term_id = term.rsplit(":", 1)
        return term_prefix, term_id

    for term_url in env_settings.CONTEXT.values():
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
    for prefix, uri in env_settings.CONTEXT.items():
        if uri in url:
            return url.replace(uri, f"{prefix}:")

    # If no match found within the context, return original URL
    return url


def replace_namespace_prefix_with_uri(term: str) -> str:
    """
    Replace the namespace prefix in a prefixed term URIs with corresponding full namespace URI from the context.

    Parameters
    ----------
    term : str
        A controlled term URI with a namespace prefix.

    Returns
    -------
    str
        The term with namespace prefix replaced with full URI if found in the context, or the original term.
    """
    for prefix, uri in env_settings.CONTEXT.items():
        if term.startswith(f"{prefix}:"):
            return term.replace(f"{prefix}:", uri)

    return term


def create_pipeline_versions_query(pipeline: str) -> str:
    """Create a SPARQL query for all versions of a pipeline available in a graph."""
    query_string = textwrap.dedent(f"""\
    SELECT DISTINCT ?pipeline_version
    WHERE {{
        ?completed_pipeline a nb:CompletedPipeline;
            nb:hasPipelineName {pipeline};
            nb:hasPipelineVersion ?pipeline_version.
    }}""")
    return query_string


def create_phenotypic_sparql_query_for_datasets(query: QueryModel):
    """Create a SPARQL query string for phenotypic parameters from a query to the POST /datasets endpoint."""
    age_bounds = sparql_models.Age(
        min_age=query.min_age, max_age=query.max_age
    )
    phenotypic_session = sparql_models.PhenotypicSession(
        hasAge=age_bounds,
        hasSex=query.sex,
        hasDiagnosis=query.diagnosis,
        hasAssessment=query.assessment,
        min_num_phenotypic_sessions=query.min_num_phenotypic_sessions,
    )
    subject = sparql_models.Subject(hasSession=phenotypic_session)
    dataset = sparql_models.Dataset(hasSamples=subject)

    query_string = dataset.to_sparql()
    return query_string


def create_imaging_sparql_query_for_datasets(query: QueryModel):
    """Create a SPARQL query string for imaging parameters from a query to the POST /datasets endpoint."""
    acquisitions = [
        sparql_models.Acquisition(hasContrastType=image_modal)
        for image_modal in query.image_modal
    ]
    pipelines = [
        sparql_models.Pipeline(
            hasPipelineVersion=pipeline.version,
            hasPipelineName=pipeline.name,
        )
        for pipeline in query.pipeline
    ]
    imaging_session = sparql_models.ImagingSession(
        hasAcquisition=acquisitions,
        hasCompletedPipeline=pipelines,
        min_num_imaging_sessions=query.min_num_imaging_sessions,
    )
    subject = sparql_models.Subject(hasSession=imaging_session)
    dataset = sparql_models.Dataset(hasSamples=subject)

    query_string = dataset.to_sparql()
    return query_string


def is_field_set(value: Any) -> bool:
    """Check if a field has been set (i.e., not an empty list, model instance, or None)."""
    if isinstance(value, list):
        return any(is_field_set(item) for item in value)
    if isinstance(value, BaseModel):
        nested_values = value.model_dump().values()
        return any(
            is_field_set(nested_value) for nested_value in nested_values
        )
    return value is not None


def contains_filters(query: QueryModel, filters: list[str]) -> bool:
    """Check if certain filter fields have been set in a given query."""
    return any(
        is_field_set(getattr(query, filter_name)) for filter_name in filters
    )


def create_sparql_queries_for_datasets(query: QueryModel) -> tuple[str, str]:
    """
    Create SPARQL queries based on the phenotypic and/or imaging filters specified in the request payload.
    """
    phenotypic_query = ""
    imaging_query = ""

    if contains_filters(query, PHENOTYPIC_FILTERS) or not contains_filters(
        query, IMAGING_FILTERS
    ):
        phenotypic_query = create_phenotypic_sparql_query_for_datasets(query)
    if contains_filters(query, IMAGING_FILTERS):
        imaging_query = create_imaging_sparql_query_for_datasets(query)

    return phenotypic_query, imaging_query


def combine_sparql_query_results(
    results_from_queries: list[pd.DataFrame],
) -> pd.DataFrame:
    """
    Combine results from multiple SPARQL queries, returning only the records (rows)
    that appear in all query result tables.
    """
    if len(results_from_queries) == 1:
        combined_query_results = results_from_queries[0]
    else:
        combined_query_results = pd.merge(
            results_from_queries[0],
            results_from_queries[1],
            how="inner",
            on=sparql_models.SPARQL_SELECTED_VARS,
        )

    return combined_query_results


def create_imaging_modalities_and_pipelines_query(
    dataset_uuids: list[str],
) -> str:
    """Create a SPARQL query to retrieve all imaging modalities and pipelines available in specified datasets."""
    dataset_uuids_string = "\n".join([f"<{uuid}>" for uuid in dataset_uuids])
    query_string = f"""
SELECT DISTINCT ?dataset_uuid ?image_modal ?pipeline_name ?pipeline_version
WHERE {{
    VALUES ?dataset_uuid {{
        {dataset_uuids_string}
    }}
    ?dataset_uuid nb:hasSamples ?subject.
    ?subject a nb:Subject;
        nb:hasSession ?imaging_session.
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
"""

    return query_string


def catalog_dataset_matches_categorical_filter(
    dataset: dict, terms_field: str, field_filter: str | list | None
) -> bool:
    """
    Return True if a given filter term or list of terms exists in the specified
    categorical dataset metadata field, or if a filter has not been specified.
    """
    if not field_filter:
        return True

    dataset_terms = dataset.get(terms_field, [])

    field_filter = (
        [field_filter] if isinstance(field_filter, str) else field_filter
    )
    return all(value in dataset_terms for value in field_filter)


def age_filters_include_catalog_dataset_age_range(
    dataset: dict,
    query_min_age: float | None,
    query_max_age: float | None,
) -> bool:
    """
    Return True if a dataset's age range overlaps with the age range specified in the query,
    or if no age filters have been specified in the query.
    """
    if query_min_age is None and query_max_age is None:
        return True

    dataset_age_range = dataset.get("age_range")
    if not isinstance(dataset_age_range, dict):
        return False

    dataset_min_age = dataset_age_range.get("minimum")
    dataset_max_age = dataset_age_range.get("maximum")

    # This should theoretically never happen because of the schema validation for catalog dataset files,
    # but we include this check as a safeguard to avoid errors.
    if dataset_min_age is None or dataset_max_age is None:
        return False

    if query_min_age is not None and dataset_max_age < query_min_age:
        return False
    if query_max_age is not None and dataset_min_age > query_max_age:
        return False

    return True


def catalog_dataset_metadata_matches_query(
    dataset: dict,
    query: QueryModel,
) -> bool:
    """
    Return True if a dataset's catalog metadata matches the filters specified in the query, and False otherwise.
    """
    term_filters_match = all(
        catalog_dataset_matches_categorical_filter(
            dataset,
            fields["catalog_field"],
            getattr(query, fields["query_field"]),
        )
        for fields in CATALOG_DATASET_TERM_FILTER_FIELDS.values()
    )
    age_filters_match = age_filters_include_catalog_dataset_age_range(
        dataset, query.min_age, query.max_age
    )

    return term_filters_match and age_filters_match


def find_matching_term_in_vocab(
    term_url: str, std_trm_vocab: list[dict], has_prefix: bool = False
) -> dict | None:
    """
    Finds the matching term from the standardized vocabulary based on the provided term URL.

    Parameters
    ----------
    term_url : str
        The URL of the controlled term to find.
    std_trm_vocab : list[dict]
        The standardized term vocabulary containing metadata for controlled terms.

    Returns
    -------
    dict | None
        The dictionary representing the matching term from the vocabulary, or None if no match is found.
    """
    # First, check whether the instance of the standardized variable contains a recognized namespace
    if not is_term_namespace_in_context(term_url, has_prefix):
        logger.warning(
            f"The controlled term {term_url} was found in a dataset but "
            "does not come from a vocabulary recognized by Neurobagel. "
            "This term will be ignored."
        )
        return None

    # Then, get the namespace and ID for the term
    term_namespace, term_id = split_namespace_from_term_uri(
        term_url, has_prefix=has_prefix
    )

    if has_prefix:
        namespace_key = "namespace_prefix"
    else:
        namespace_key = "namespace_url"

    # Since the term vocabulary for a standardized variable can contain terms from several namespaces,
    # we first have to locate the namespace used in the term we are looking up
    namespace_terms: list = next(
        (
            namespace["terms"]
            for namespace in std_trm_vocab
            if namespace[namespace_key] == term_namespace
        ),
        [],
    )
    # If the term has a recognized namespace but is not found in the vocabulary,
    # we return an empty dictionary to indicate that no term metadata is available.
    matched_term: dict = next(
        (term for term in namespace_terms if term["id"] == term_id),
        {},
    )
    return matched_term
