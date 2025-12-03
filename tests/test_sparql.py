import pytest

from app.api import sparql_models
from app.api import utility as util
from app.api.models import QueryModel


@pytest.mark.parametrize(
    "raw_value, expected_value",
    [
        ("np:fmriprep", "np:fmriprep"),
        ("23.0.2", '"23.0.2"'),
    ],
)
def test_format_value(raw_value, expected_value):
    """Test that query field values are correctly formatted for SPARQL query triples."""
    assert sparql_models.format_value(raw_value) == expected_value


def test_get_select_variables():
    """Test that a list of variable names is correctly converted to a SPARQL SELECT variable string."""
    variables = ["dataset", "dataset_name", "dataset_portal_uri"]
    expected_select_string = "?dataset ?dataset_name ?dataset_portal_uri"
    assert (
        sparql_models.get_select_variables(variables) == expected_select_string
    )


@pytest.mark.parametrize(
    "datasets_request_body, sparql_query_statements",
    [
        (
            {},
            [
                "SELECT ?dataset ?dataset_name ?dataset_portal_uri ?subject",
                "WHERE {",
                "    ?dataset a nb:Dataset.",
                "    ?dataset nb:hasLabel ?dataset_name.",
                "    ?dataset nb:hasSamples ?subject.",
                "    ?subject a nb:Subject.",
                "    OPTIONAL {?dataset nb:hasPortalURI ?dataset_portal_uri.}",
                "}",
            ],
        ),
        (
            {"min_num_imaging_sessions": 2},
            [
                "SELECT ?dataset ?dataset_name ?dataset_portal_uri ?subject",
                "WHERE {",
                "    ?dataset a nb:Dataset.",
                "    ?dataset nb:hasLabel ?dataset_name.",
                "    ?dataset nb:hasSamples ?subject.",
                "    ?subject a nb:Subject.",
                "    ?subject nb:hasSession ?imaging_session.",
                "    ?imaging_session a nb:ImagingSession.",
                "    OPTIONAL {?dataset nb:hasPortalURI ?dataset_portal_uri.}",
                "}",
                "GROUP BY ?dataset ?dataset_name ?dataset_portal_uri ?subject",
                "HAVING (COUNT(DISTINCT ?imaging_session) >= 2)",
            ],
        ),
        (
            {"image_modal": "nidm:T1Weighted"},
            [
                "SELECT ?dataset ?dataset_name ?dataset_portal_uri ?subject",
                "WHERE {",
                "    ?dataset a nb:Dataset.",
                "    ?dataset nb:hasLabel ?dataset_name.",
                "    ?dataset nb:hasSamples ?subject.",
                "    ?subject a nb:Subject.",
                "    ?subject nb:hasSession ?imaging_session.",
                "    ?imaging_session a nb:ImagingSession.",
                "    ?imaging_session nb:hasAcquisition ?acquisition.",
                "    ?acquisition nb:hasContrastType nidm:T1Weighted.",
                "    OPTIONAL {?dataset nb:hasPortalURI ?dataset_portal_uri.}",
                "}",
            ],
        ),
        (
            {
                "image_modal": "nidm:T1Weighted",
                "pipeline_name": "np:fmriprep",
                "pipeline_version": "23.2.0",
                "min_num_imaging_sessions": 2,
            },
            [
                "SELECT ?dataset ?dataset_name ?dataset_portal_uri ?subject",
                "WHERE {",
                "    ?dataset a nb:Dataset.",
                "    ?dataset nb:hasLabel ?dataset_name.",
                "    ?dataset nb:hasSamples ?subject.",
                "    ?subject a nb:Subject.",
                "    ?subject nb:hasSession ?imaging_session.",
                "    ?imaging_session a nb:ImagingSession.",
                "    ?imaging_session nb:hasAcquisition ?acquisition.",
                "    ?acquisition nb:hasContrastType nidm:T1Weighted.",
                "    ?imaging_session nb:hasCompletedPipeline ?pipeline.",
                "    ?pipeline nb:hasPipelineName np:fmriprep.",
                '    ?pipeline nb:hasPipelineVersion "23.2.0".',
                "    OPTIONAL {?dataset nb:hasPortalURI ?dataset_portal_uri.}",
                "}",
                "GROUP BY ?dataset ?dataset_name ?dataset_portal_uri ?subject",
                "HAVING (COUNT(DISTINCT ?imaging_session) >= 2)",
            ],
        ),
    ],
)
def test_create_imaging_sparql_query_for_datasets(
    datasets_request_body, sparql_query_statements
):
    """
    Test that a SPARQL query string is correctly created from a POST /datasets request body
    with imaging filters.
    """
    query = QueryModel(**datasets_request_body)
    expected_sparql_query = "\n".join(sparql_query_statements)
    assert (
        util.create_imaging_sparql_query_for_datasets(query)
        == expected_sparql_query
    )


@pytest.mark.parametrize(
    "datasets_request_body, sparql_query_statements",
    [
        (
            {"min_age": 60},
            [
                "SELECT ?dataset ?dataset_name ?dataset_portal_uri ?subject",
                "WHERE {",
                "    ?dataset a nb:Dataset.",
                "    ?dataset nb:hasLabel ?dataset_name.",
                "    ?dataset nb:hasSamples ?subject.",
                "    ?subject a nb:Subject.",
                "    ?subject nb:hasSession ?phenotypic_session.",
                "    ?phenotypic_session a nb:PhenotypicSession.",
                "    ?phenotypic_session nb:hasAge ?age.",
                "    FILTER (?age >= 60.0).",
                "    OPTIONAL {?dataset nb:hasPortalURI ?dataset_portal_uri.}",
                "}",
            ],
        ),
        (
            {"min_age": 60, "max_age": 80},
            [
                "SELECT ?dataset ?dataset_name ?dataset_portal_uri ?subject",
                "WHERE {",
                "    ?dataset a nb:Dataset.",
                "    ?dataset nb:hasLabel ?dataset_name.",
                "    ?dataset nb:hasSamples ?subject.",
                "    ?subject a nb:Subject.",
                "    ?subject nb:hasSession ?phenotypic_session.",
                "    ?phenotypic_session a nb:PhenotypicSession.",
                "    ?phenotypic_session nb:hasAge ?age.",
                "    FILTER (?age >= 60.0 && ?age <= 80.0).",
                "    OPTIONAL {?dataset nb:hasPortalURI ?dataset_portal_uri.}",
                "}",
            ],
        ),
        (
            {"min_num_phenotypic_sessions": 2},
            [
                "SELECT ?dataset ?dataset_name ?dataset_portal_uri ?subject",
                "WHERE {",
                "    ?dataset a nb:Dataset.",
                "    ?dataset nb:hasLabel ?dataset_name.",
                "    ?dataset nb:hasSamples ?subject.",
                "    ?subject a nb:Subject.",
                "    ?subject nb:hasSession ?phenotypic_session.",
                "    ?phenotypic_session a nb:PhenotypicSession.",
                "    OPTIONAL {?dataset nb:hasPortalURI ?dataset_portal_uri.}",
                "}",
                "GROUP BY ?dataset ?dataset_name ?dataset_portal_uri ?subject",
                "HAVING (COUNT(DISTINCT ?phenotypic_session) >= 2)",
            ],
        ),
        (
            {
                "min_age": 60,
                "sex": "snomed:12345",
                "diagnosis": "snomed:23456",
                "assessment": "snomed:34567",
                "min_num_phenotypic_sessions": 2,
            },
            [
                "SELECT ?dataset ?dataset_name ?dataset_portal_uri ?subject",
                "WHERE {",
                "    ?dataset a nb:Dataset.",
                "    ?dataset nb:hasLabel ?dataset_name.",
                "    ?dataset nb:hasSamples ?subject.",
                "    ?subject a nb:Subject.",
                "    ?subject nb:hasSession ?phenotypic_session.",
                "    ?phenotypic_session a nb:PhenotypicSession.",
                "    ?phenotypic_session nb:hasSex snomed:12345.",
                "    ?phenotypic_session nb:hasDiagnosis snomed:23456.",
                "    ?phenotypic_session nb:hasAssessment snomed:34567.",
                "    ?phenotypic_session nb:hasAge ?age.",
                "    FILTER (?age >= 60.0).",
                "    OPTIONAL {?dataset nb:hasPortalURI ?dataset_portal_uri.}",
                "}",
                "GROUP BY ?dataset ?dataset_name ?dataset_portal_uri ?subject",
                "HAVING (COUNT(DISTINCT ?phenotypic_session) >= 2)",
            ],
        ),
    ],
)
def test_create_phenotypic_sparql_query_for_datasets(
    datasets_request_body, sparql_query_statements
):
    """
    Test that a SPARQL query string is correctly created from a POST /datasets request body
    with phenotypic filters.
    """
    query = QueryModel(**datasets_request_body)
    expected_sparql_query = "\n".join(sparql_query_statements)
    assert (
        util.create_phenotypic_sparql_query_for_datasets(query)
        == expected_sparql_query
    )


@pytest.mark.parametrize(
    "datasets_request_body, expected_phenotypic_query_statements, expected_imaging_query_statements",
    [
        (
            {
                "diagnosis": "snomed:12345",
                "image_modal": "nidm:T1Weighted",
                "min_num_phenotypic_sessions": 2,
                "min_num_imaging_sessions": 2,
            },
            [
                "SELECT ?dataset ?dataset_name ?dataset_portal_uri ?subject",
                "WHERE {",
                "    ?dataset a nb:Dataset.",
                "    ?dataset nb:hasLabel ?dataset_name.",
                "    ?dataset nb:hasSamples ?subject.",
                "    ?subject a nb:Subject.",
                "    ?subject nb:hasSession ?phenotypic_session.",
                "    ?phenotypic_session a nb:PhenotypicSession.",
                "    ?phenotypic_session nb:hasDiagnosis snomed:12345.",
                "    OPTIONAL {?dataset nb:hasPortalURI ?dataset_portal_uri.}",
                "}",
                "GROUP BY ?dataset ?dataset_name ?dataset_portal_uri ?subject",
                "HAVING (COUNT(DISTINCT ?phenotypic_session) >= 2)",
            ],
            [
                "SELECT ?dataset ?dataset_name ?dataset_portal_uri ?subject",
                "WHERE {",
                "    ?dataset a nb:Dataset.",
                "    ?dataset nb:hasLabel ?dataset_name.",
                "    ?dataset nb:hasSamples ?subject.",
                "    ?subject a nb:Subject.",
                "    ?subject nb:hasSession ?imaging_session.",
                "    ?imaging_session a nb:ImagingSession.",
                "    ?imaging_session nb:hasAcquisition ?acquisition.",
                "    ?acquisition nb:hasContrastType nidm:T1Weighted.",
                "    OPTIONAL {?dataset nb:hasPortalURI ?dataset_portal_uri.}",
                "}",
                "GROUP BY ?dataset ?dataset_name ?dataset_portal_uri ?subject",
                "HAVING (COUNT(DISTINCT ?imaging_session) >= 2)",
            ],
        ),
        (
            {"diagnosis": "snomed:12345"},
            [
                "SELECT ?dataset ?dataset_name ?dataset_portal_uri ?subject",
                "WHERE {",
                "    ?dataset a nb:Dataset.",
                "    ?dataset nb:hasLabel ?dataset_name.",
                "    ?dataset nb:hasSamples ?subject.",
                "    ?subject a nb:Subject.",
                "    ?subject nb:hasSession ?phenotypic_session.",
                "    ?phenotypic_session a nb:PhenotypicSession.",
                "    ?phenotypic_session nb:hasDiagnosis snomed:12345.",
                "    OPTIONAL {?dataset nb:hasPortalURI ?dataset_portal_uri.}",
                "}",
            ],
            [""],
        ),
        (
            {"image_modal": "nidm:T1Weighted"},
            [""],
            [
                "SELECT ?dataset ?dataset_name ?dataset_portal_uri ?subject",
                "WHERE {",
                "    ?dataset a nb:Dataset.",
                "    ?dataset nb:hasLabel ?dataset_name.",
                "    ?dataset nb:hasSamples ?subject.",
                "    ?subject a nb:Subject.",
                "    ?subject nb:hasSession ?imaging_session.",
                "    ?imaging_session a nb:ImagingSession.",
                "    ?imaging_session nb:hasAcquisition ?acquisition.",
                "    ?acquisition nb:hasContrastType nidm:T1Weighted.",
                "    OPTIONAL {?dataset nb:hasPortalURI ?dataset_portal_uri.}",
                "}",
            ],
        ),
        (
            {},
            [
                "SELECT ?dataset ?dataset_name ?dataset_portal_uri ?subject",
                "WHERE {",
                "    ?dataset a nb:Dataset.",
                "    ?dataset nb:hasLabel ?dataset_name.",
                "    ?dataset nb:hasSamples ?subject.",
                "    ?subject a nb:Subject.",
                "    OPTIONAL {?dataset nb:hasPortalURI ?dataset_portal_uri.}",
                "}",
            ],
            [""],
        ),
    ],
)
def test_create_sparql_queries_for_datasets(
    datasets_request_body,
    expected_phenotypic_query_statements,
    expected_imaging_query_statements,
):
    """
    Test that phenotypic and imaging query filters from a request are correctly extracted into
    separate SPARQL queries and that for an unfiltered query, only one SPARQL query is created.
    """
    query = QueryModel(**datasets_request_body)
    expected_phenotypic_query = "\n".join(expected_phenotypic_query_statements)
    expected_imaging_query = "\n".join(expected_imaging_query_statements)
    phenotypic_query, imaging_query = util.create_sparql_queries_for_datasets(
        query
    )
    assert phenotypic_query == expected_phenotypic_query
    assert imaging_query == expected_imaging_query
