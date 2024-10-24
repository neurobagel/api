"""Test utility functions."""

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
