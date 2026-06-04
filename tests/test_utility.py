"""Test utility functions."""

import pandas as pd
import pandas.testing as pdt
import pytest

from app.api import utility as util
from app.api.models import QueryModel


def test_unpack_graph_response_json_to_dicts():
    """Test that given a valid httpx JSON response, the function returns a simplified list of dicts with the correct keys and values."""
    mock_response_json = {
        "head": {"vars": ["dataset_uuid", "total_subjects"]},
        "results": {
            "bindings": [
                {
                    "dataset_uuid": {
                        "type": "uri",
                        "value": "http://neurobagel.org/vocab/ds1234",
                    },
                    "total_subjects": {
                        "datatype": "http://www.w3.org/2001/XMLSchema#integer",
                        "type": "literal",
                        "value": "70",
                    },
                },
                {
                    "dataset_uuid": {
                        "type": "uri",
                        "value": "http://neurobagel.org/vocab/ds2345",
                    },
                    "total_subjects": {
                        "datatype": "http://www.w3.org/2001/XMLSchema#integer",
                        "type": "literal",
                        "value": "40",
                    },
                },
                {
                    "dataset_uuid": {
                        "type": "uri",
                        "value": "http://neurobagel.org/vocab/ds3456",
                    },
                    "total_subjects": {
                        "datatype": "http://www.w3.org/2001/XMLSchema#integer",
                        "type": "literal",
                        "value": "84",
                    },
                },
            ]
        },
    }

    assert util.unpack_graph_response_json_to_dicts(mock_response_json) == [
        {
            "dataset_uuid": "http://neurobagel.org/vocab/ds1234",
            "total_subjects": "70",
        },
        {
            "dataset_uuid": "http://neurobagel.org/vocab/ds2345",
            "total_subjects": "40",
        },
        {
            "dataset_uuid": "http://neurobagel.org/vocab/ds3456",
            "total_subjects": "84",
        },
    ]


def test_bound_filter_created_correctly():
    """Test that the function creates a valid SPARQL filter substring given a variable name."""
    var = "subject_group"
    assert util.create_bound_filter(var) == "FILTER (BOUND(?subject_group)"


def test_combine_sparql_query_results():
    """
    Test that combine_sparql_query_results correctly returns rows common to multiple query result tables
    returned from phenotypic and imaging POST /datasets queries.
    """
    mock_phenotypic_query_results = pd.DataFrame(
        {
            "dataset": [
                "http://neurobagel.org/vocab/ds01",
                "http://neurobagel.org/vocab/ds01",
                "http://neurobagel.org/vocab/ds02",
                "http://neurobagel.org/vocab/ds02",
            ],
            "subject": [
                "http://neurobagel.org/vocab/ds01-sub01",
                "http://neurobagel.org/vocab/ds01-sub02",
                "http://neurobagel.org/vocab/ds02-sub01",
                "http://neurobagel.org/vocab/ds02-sub02",
            ],
        }
    )
    mock_imaging_query_results = pd.DataFrame(
        {
            "dataset": [
                "http://neurobagel.org/vocab/ds01",
                "http://neurobagel.org/vocab/ds01",
                "http://neurobagel.org/vocab/ds02",
                "http://neurobagel.org/vocab/ds02",
            ],
            "subject": [
                "http://neurobagel.org/vocab/ds01-sub01",
                "http://neurobagel.org/vocab/ds01-sub03",
                "http://neurobagel.org/vocab/ds02-sub01",
                "http://neurobagel.org/vocab/ds02-sub03",
            ],
        }
    )
    expected_combined_query_results = pd.DataFrame(
        {
            "dataset": [
                "http://neurobagel.org/vocab/ds01",
                "http://neurobagel.org/vocab/ds02",
            ],
            "subject": [
                "http://neurobagel.org/vocab/ds01-sub01",
                "http://neurobagel.org/vocab/ds02-sub01",
            ],
        }
    )

    results_from_queries = [
        mock_phenotypic_query_results,
        mock_imaging_query_results,
    ]
    combined_query_results = util.combine_sparql_query_results(
        results_from_queries
    )

    pdt.assert_frame_equal(
        combined_query_results, expected_combined_query_results
    )


def test_sparql_context_correctly_added_to_query_body(mock_context):
    """Test that the expected prefix declarations are correctly added to a query body."""
    query_body = "\n".join(
        [
            "SELECT DISTINCT ?pipeline_version",
            "WHERE {",
            "?completed_pipeline a nb:CompletedPipeline;",
            "nb:hasPipelineName np:fmriprep;",
            "nb:hasPipelineVersion ?pipeline_version.",
            "}",
        ]
    )

    expected_query_with_context = "\n".join(
        [
            "PREFIX nb: <http://neurobagel.org/vocab/>",
            "PREFIX ncit: <http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#>",
            "PREFIX nidm: <http://purl.org/nidash/nidm#>",
            "PREFIX snomed: <http://purl.bioontology.org/ontology/SNOMEDCT/>",
            "PREFIX np: <https://github.com/nipoppy/pipeline-catalog/tree/main/processing/>",
            "SELECT DISTINCT ?pipeline_version",
            "WHERE {",
            "?completed_pipeline a nb:CompletedPipeline;",
            "nb:hasPipelineName np:fmriprep;",
            "nb:hasPipelineVersion ?pipeline_version.",
            "}",
        ]
    )

    query_with_context = util.add_sparql_context_to_query(query_body)

    assert query_with_context == expected_query_with_context


@pytest.mark.parametrize(
    "assessment_filter, expected_match_result",
    [
        ("snomed:11111", True),
        ("snomed:NOTFOUND", False),
        (
            None,
            True,
        ),  # if no filter is provided, dataset should match by default
    ],
)
def test_term_in_catalog_dataset_attributes(
    assessment_filter, expected_match_result
):
    """
    Test that the function correctly identifies whether a query term is present in the relevant field
    of the catalog dataset info.
    """
    mock_catalog_dataset_info = {
        "dataset_name": "BIDS synthetic",
        "participant_count": 5,
        "available_sex": ["snomed:12345", "snomed:45678"],
        "available_diagnoses": ["snomed:67890", "ncit:C94342"],
        "available_assessments": ["snomed:11111", "snomed:22222"],
        "age_range": {"minimum": 21.0, "maximum": 42.0},
    }
    assert (
        util.catalog_dataset_has_term(
            dataset=mock_catalog_dataset_info,
            terms_field="available_assessments",
            query_term=assessment_filter,
        )
        == expected_match_result
    )


@pytest.mark.parametrize(
    "min_age_filter, max_age_filter, expected_match_result",
    [
        (25, 35, True),
        (None, 30, True),
        (30, None, True),
        (10, 20, False),
        (43, 50, False),
        (10, 30, True),
        (30, 50, True),
        (None, None, True),
    ],
)
def test_age_filters_include_catalog_dataset_age_range(
    min_age_filter, max_age_filter, expected_match_result
):
    """
    Test that the function correctly identifies whether a catalog dataset's age range overlaps
    with the age range specified by query filters.
    """
    mock_catalog_dataset_info = {
        "dataset_name": "BIDS synthetic",
        "participant_count": 5,
        "available_sex": ["snomed:12345", "snomed:45678"],
        "available_diagnoses": ["snomed:67890", "ncit:C94342"],
        "available_assessments": ["snomed:11111", "snomed:22222"],
        "age_range": {"minimum": 21.0, "maximum": 42.0},
    }

    assert (
        util.age_filters_include_catalog_dataset_age_range(
            dataset=mock_catalog_dataset_info,
            query_min_age=min_age_filter,
            query_max_age=max_age_filter,
        )
        == expected_match_result
    )


def test_dataset_with_no_age_range_matches_query_without_age_filters():
    """
    Test that a dataset with no age range information is not excluded when age filters are not provided in the query.
    """
    mock_catalog_dataset_info = {
        "dataset_name": "BIDS synthetic",
        "participant_count": 5,
        "available_sex": ["snomed:12345", "snomed:45678"],
        "available_diagnoses": ["snomed:67890", "ncit:C94342"],
        "available_assessments": ["snomed:11111", "snomed:22222"],
        "age_range": None,
    }

    assert (
        util.age_filters_include_catalog_dataset_age_range(
            dataset=mock_catalog_dataset_info,
            query_min_age=None,
            query_max_age=None,
        )
        is True
    )


@pytest.mark.parametrize(
    "query_fields,expected_match_result",
    [
        ({"assessment": "snomed:11111", "min_age": 20}, True),
        (
            {
                "assessment": "snomed:11111",
                "diagnosis": "snomed:otherdiagnosis",
            },
            False,
        ),
        ({"sex": "snomed:12345", "min_age": 60}, False),
    ],
)
def test_query_filters_correctly_match_catalog_datasets(
    query_fields, expected_match_result
):
    """
    Test that the function correctly identifies whether a catalog dataset matches all provided query filters.
    """
    query = QueryModel(**query_fields)

    mock_catalog_dataset_info = {
        "dataset_name": "BIDS synthetic",
        "participant_count": 5,
        "available_sex": ["snomed:12345", "snomed:45678"],
        "available_diagnoses": ["snomed:67890", "ncit:C94342"],
        "available_assessments": ["snomed:11111", "snomed:22222"],
        "age_range": {"minimum": 21.0, "maximum": 42.0},
    }
    assert (
        util.catalog_dataset_metadata_matches_query(
            dataset=mock_catalog_dataset_info, query=query
        )
    ) == expected_match_result


@pytest.mark.parametrize(
    "term_url,has_prefix,expected_result",
    [
        (
            "http://purl.bioontology.org/ontology/SNOMEDCT/1303696008",
            False,
            {
                "id": "1303696008",
                "name": "Robson Ten Group Classification System",
            },
        ),
        (
            "snomed:1303696008",
            True,
            {
                "id": "1303696008",
                "name": "Robson Ten Group Classification System",
            },
        ),
        (
            "snomed:otherterm",
            True,
            {},  # term has a recognized prefix but no entry in vocab
        ),
        (
            "ncit:someterm",
            True,
            {},  # term has a recognized prefix but no entry in vocab
        ),
        (
            "unknownprefix:1303696008",
            True,
            None,  # term has wrong prefix, so should be skipped downstream
        ),
    ],
)
def test_find_matching_term_in_vocab(
    mock_context, term_url, has_prefix, expected_result
):
    mock_vocab = [
        {
            "namespace_prefix": "snomed",
            "namespace_url": "http://purl.bioontology.org/ontology/SNOMEDCT/",
            "vocabulary_name": "Neurobagel vocabulary of Assessment terms",
            "version": "1.0.0",
            "terms": [
                {
                    "id": "1303696008",
                    "name": "Robson Ten Group Classification System",
                },
                {"id": "1304062007", "name": "Malnutrition Screening Tool"},
                {
                    "id": "1332329009",
                    "name": "Interviewer led Chronic Respiratory Questionnaire",
                },
                {
                    "id": "1332330004",
                    "name": "Self-reported Chronic Respiratory Questionnaire",
                },
            ],
        }
    ]

    assert (
        util.find_matching_term_in_vocab(
            term_url=term_url,
            std_trm_vocab=mock_vocab,
            has_prefix=has_prefix,
        )
        == expected_result
    )
