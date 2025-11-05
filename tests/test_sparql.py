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
    variables = ["dataset_uuid", "dataset_name", "dataset_portal_uri"]
    expected_select_string = "?dataset_uuid ?dataset_name ?dataset_portal_uri"
    assert (
        sparql_models.get_select_variables(variables) == expected_select_string
    )


@pytest.mark.parametrize(
    "datasets_request_body, expected_where_triples",
    [
        (
            {},
            [
                "WHERE {",
                "    ?dataset_uuid a nb:Dataset.",
                "    ?dataset_uuid nb:hasLabel ?dataset_name.",
                "    ?dataset_uuid nb:hasSamples ?subject_uuid.",
                "    OPTIONAL {?dataset_uuid nb:hasPortalURI ?dataset_portal_uri.}",
                "    ?subject_uuid a nb:Subject.",
                "}",
            ],
        ),
        (
            {"min_num_imaging_sessions": 2},
            [
                "WHERE {",
                "    ?dataset_uuid a nb:Dataset.",
                "    ?dataset_uuid nb:hasLabel ?dataset_name.",
                "    ?dataset_uuid nb:hasSamples ?subject_uuid.",
                "    OPTIONAL {?dataset_uuid nb:hasPortalURI ?dataset_portal_uri.}",
                "    ?subject_uuid a nb:Subject.",
                "    ?subject_uuid nb:hasSession ?imaging_session.",
                "    ?imaging_session a nb:ImagingSession.",
                "}",
                "GROUP BY ?dataset_uuid ?dataset_name ?dataset_portal_uri ?subject_uuid",
                "HAVING (COUNT(DISTINCT ?imaging_session) >= 2)",
            ],
        ),
        (
            {"image_modal": "nidm:T1Weighted"},
            [
                "WHERE {",
                "    ?dataset_uuid a nb:Dataset.",
                "    ?dataset_uuid nb:hasLabel ?dataset_name.",
                "    ?dataset_uuid nb:hasSamples ?subject_uuid.",
                "    OPTIONAL {?dataset_uuid nb:hasPortalURI ?dataset_portal_uri.}",
                "    ?subject_uuid a nb:Subject.",
                "    ?subject_uuid nb:hasSession ?imaging_session.",
                "    ?imaging_session a nb:ImagingSession.",
                "    ?imaging_session nb:hasAcquisition ?acquisition.",
                "    ?acquisition nb:hasContrastType nidm:T1Weighted.",
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
                "WHERE {",
                "    ?dataset_uuid a nb:Dataset.",
                "    ?dataset_uuid nb:hasLabel ?dataset_name.",
                "    ?dataset_uuid nb:hasSamples ?subject_uuid.",
                "    OPTIONAL {?dataset_uuid nb:hasPortalURI ?dataset_portal_uri.}",
                "    ?subject_uuid a nb:Subject.",
                "    ?subject_uuid nb:hasSession ?imaging_session.",
                "    ?imaging_session a nb:ImagingSession.",
                "    ?imaging_session nb:hasAcquisition ?acquisition.",
                "    ?acquisition nb:hasContrastType nidm:T1Weighted.",
                "    ?imaging_session nb:hasCompletedPipeline ?pipeline.",
                "    ?pipeline nb:hasPipelineName np:fmriprep.",
                '    ?pipeline nb:hasPipelineVersion "23.2.0".',
                "}",
                "GROUP BY ?dataset_uuid ?dataset_name ?dataset_portal_uri ?subject_uuid",
                "HAVING (COUNT(DISTINCT ?imaging_session) >= 2)",
            ],
        ),
    ],
)
def test_create_imaging_sparql_query_for_datasets(
    datasets_request_body, expected_where_triples
):
    """Test that a SPARQL query string is correctly created from a POST /datasets request body."""
    query = QueryModel(**datasets_request_body)
    expected_sparql_query = "\n".join(
        [
            "\nSELECT ?dataset_uuid ?dataset_name ?dataset_portal_uri ?subject_uuid"
        ]
        + expected_where_triples
    )
    assert (
        util.create_imaging_sparql_query_for_datasets(query)
        == expected_sparql_query
    )


def test_context_in_sparql_query(mock_context):
    """Test that the SPARQL query string includes a context."""
    query = QueryModel()
    sparql_query = util.create_imaging_sparql_query_for_datasets(query)
    assert sparql_query.startswith("PREFIX")
