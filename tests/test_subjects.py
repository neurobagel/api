import pytest

from app.api import crud
from app.main import settings

ROUTE = "/subjects"


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


@pytest.mark.parametrize("mock_query_records", [None], indirect=True)
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
    mock_query_records,
    invalid_dataset_uuids,
    disable_auth,
    monkeypatch,
):
    """
    Ensure that invalid 'dataset_uuids' request body values are rejected with a 422 error.
    """
    monkeypatch.setattr(crud, "post_subjects", mock_query_records)
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
