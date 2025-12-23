"""Test utility functions."""

import pandas as pd
import pandas.testing as pdt

from app.api import utility as util


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
