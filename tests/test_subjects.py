import pytest

from app.api import crud, env_settings
from app.main import settings

ROUTE = "/subjects"


def test_empty_post_query_is_successful(
    test_app,
    mock_successful_post_subjects,
    monkeypatch,
    disable_auth,
):
    """Given no input for any query parameters, returns a 200 status code and a non-empty list of results (should correspond to all subjects in graph)."""

    monkeypatch.setattr(crud, "post_subjects", mock_successful_post_subjects)
    response = test_app.post(url=ROUTE, json={})
    assert response.status_code == 200
    assert response.json() != []


@pytest.mark.parametrize(
    "valid_dataset_uuids",
    [
        ["http://neurobagel.org/vocab/12345"],
        [
            "http://neurobagel.org/vocab/12345",
            "http://neurobagel.org/vocab/67890",
        ],
        [],
        None,
    ],
)
def test_post_valid_dataset_uuids_does_not_error(
    test_app,
    mock_successful_post_subjects,
    valid_dataset_uuids,
    disable_auth,
    monkeypatch,
):
    """
    Ensure the 'dataset_uuids' request body field accepts string lists and null values without errors.

    NOTE: This test does not verify the contents of the response depending on the provided dataset_uuids.
    """
    monkeypatch.setattr(crud, "post_subjects", mock_successful_post_subjects)
    response = test_app.post(
        ROUTE, json={"dataset_uuids": valid_dataset_uuids}
    )
    assert response.status_code == 200
    assert response.json() != []


def test_aggregate_query_response_structure(
    test_app,
    mock_post_agg_query_to_graph,
    mock_query_matching_dataset_sizes,
    monkeypatch,
    disable_auth,
):
    """Test that when aggregate results are enabled, a cohort query response has the expected structure."""
    monkeypatch.setattr(settings, "return_agg", True)
    monkeypatch.setattr(
        crud, "post_query_to_graph", mock_post_agg_query_to_graph
    )
    monkeypatch.setattr(
        crud, "query_matching_dataset_sizes", mock_query_matching_dataset_sizes
    )

    response = test_app.post(url=ROUTE, json={})
    assert all(
        dataset["subject_data"] == "protected" for dataset in response.json()
    )


@pytest.mark.integration
def test_app_with_invalid_environment_vars(
    test_app,
    monkeypatch,
    disable_auth,
    set_graph_url_vars_for_integration_tests,
    # set_temp_datasets_metadata_file,
):
    """Given invalid credentials for the graph, returns a 401 status code."""
    monkeypatch.setattr(settings, "graph_username", "wrong_username")
    monkeypatch.setattr(settings, "graph_password", "wrong_password")

    with test_app:
        response = test_app.post(url=ROUTE, json={})
    assert response.status_code == 401


@pytest.mark.integration
def test_integration_query_without_auth_succeeds(
    test_app,
    disable_auth,
    set_graph_url_vars_for_integration_tests,
    # set_temp_datasets_metadata_file,
):
    """
    Running a test against a real local test graph
    should succeed when authentication is disabled.
    """
    with test_app:
        response = test_app.post(url=ROUTE, json={})
    assert response.status_code == 200


def test_missing_derivatives_info_handled_by_nonagg_api_response(
    test_app,
    mock_post_nonagg_query_to_graph,
    mock_query_matching_dataset_sizes,
    monkeypatch,
    disable_auth,
):
    """
    Test that in the non-aggregated API mode, when all matching subjects lack pipeline information,
    the API does not error out and pipeline variables in the API response still have the expected structure.
    """
    monkeypatch.setattr(settings, "return_agg", False)
    monkeypatch.setattr(
        crud, "post_query_to_graph", mock_post_nonagg_query_to_graph
    )
    monkeypatch.setattr(
        crud, "query_matching_dataset_sizes", mock_query_matching_dataset_sizes
    )

    response = test_app.post(url=ROUTE, json={})
    assert response.status_code == 200

    matching_ds = response.json()[0]
    for session in matching_ds["subject_data"]:
        assert session["completed_pipelines"] == {}


@pytest.mark.integration
def test_only_imaging_and_phenotypic_sessions_returned_in_query_response(
    test_app,
    monkeypatch,
    disable_auth,
    set_graph_url_vars_for_integration_tests,
    # set_temp_datasets_metadata_file,
):
    """
    Test that only sessions of type PhenotypicSession and ImagingSession are returned in an unaggregated query response.
    """
    monkeypatch.setattr(settings, "return_agg", False)

    with test_app:
        response = test_app.post(url=ROUTE, json={})

    assert response.status_code == 200

    matching_ds = response.json()[0]

    sub01_sessions = [
        ses_instance
        for ses_instance in matching_ds["subject_data"]
        if ses_instance["sub_id"] == "sub-01"
    ]
    assert len(sub01_sessions) == 4

    for ses_instance in matching_ds["subject_data"]:
        assert ses_instance["session_type"] in [
            "http://neurobagel.org/vocab/ImagingSession",
            "http://neurobagel.org/vocab/PhenotypicSession",
        ], f'{ses_instance["sub_id"]}, {ses_instance["session_id"]} is of type {ses_instance["session_type"]}'


@pytest.mark.integration
def test_min_cell_size_removes_results(
    test_app,
    monkeypatch,
    disable_auth,
    set_graph_url_vars_for_integration_tests,
    # set_temp_datasets_metadata_file,
):
    """
    If the minimum cell size is large enough, all results should be filtered out
    """
    monkeypatch.setattr(settings, "min_cell_size", 100)

    with test_app:
        response = test_app.post(url=ROUTE, json={})

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.parametrize("mock_post_subjects", [None], indirect=True)
@pytest.mark.parametrize(
    "invalid_dataset_uuids",
    [
        [123, 456],
        [None],
        "http://neurobagel.org/vocab/12345",
        True,
    ],
)
def test_post_invalid_dataset_uuids_raises_error(
    test_app,
    mock_post_subjects,
    invalid_dataset_uuids,
    disable_auth,
    monkeypatch,
):
    """
    Ensure that invalid 'dataset_uuids' request body values are rejected with a 422 error.
    """
    monkeypatch.setattr(crud, "post_subjects", mock_post_subjects)
    response = test_app.post(
        ROUTE, json={"dataset_uuids": invalid_dataset_uuids}
    )
    assert response.status_code == 422


def test_post_subjects_returns_no_dataset_metadata(
    test_app, mock_post_agg_query_to_graph, disable_auth, monkeypatch
):
    """
    Ensure that a response from the /subjects endpoint does not include dataset metadata
    for matching datasets such as dataset name, portal, etc.
    """
    monkeypatch.setattr(settings, "return_agg", True)
    monkeypatch.setattr(
        crud, "post_query_to_graph", mock_post_agg_query_to_graph
    )
    response = test_app.post(ROUTE, json={})
    assert response.status_code == 200

    for matching_dataset in response.json():
        assert matching_dataset.keys() == {"dataset_uuid", "subject_data"}


def test_post_subjects_returns_no_matching_subjects_in_catalog_mode(
    test_app, mock_post_agg_query_to_graph, disable_auth, monkeypatch
):
    """
    Test that the /subjects endpoint returns no subject-level results in catalog mode.
    """
    mock_datasets_metadata = {
        "nb:18532368-82dc-42ac-b4fb-fbb187ad6ae1": {
            "dataset_name": "BIDS synthetic",
            "participant_count": 5,
            "repository_url": "https://github.com/bids-standard/bids-examples.git",
            "available_sex": ["snomed:248153007", "snomed:248152002"],
            "available_diagnoses": ["snomed:406506008", "ncit:C94342"],
            "available_assessments": [
                "snomed:859351000000102",
                "snomed:342061000000106",
            ],
            "age_range": {"minimum": 21.0, "maximum": 42.0},
        },
        "nb:80af4d30-0447-4f13-9eaf-98ae8065895a": {
            "dataset_name": "Rhyme judgment",
            "access_link": "https://github.com/OpenNeuroDatasets-JSONLD/ds000003.git",
            "participant_count": 10,
            "available_sex": ["snomed:248153007", "snomed:248152002"],
            "available_diagnoses": ["snomed:406506008", "ncit:C94342"],
            "available_assessments": ["snomed:859351000000102"],
            "age_range": {"minimum": 60.0, "maximum": 80.0},
        },
    }

    monkeypatch.setattr(settings, "catalog_mode", True)
    monkeypatch.setattr(
        env_settings, "DATASETS_METADATA", mock_datasets_metadata
    )

    response = test_app.post(ROUTE, json={})
    assert response.status_code == 200
    assert response.json() == []
