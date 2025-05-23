import pytest

from app.api import crud

ROUTE = "/datasets"


def test_datasets_response_structure(
    test_app,
    mock_post_agg_query_to_graph,
    mock_query_matching_dataset_sizes,
    disable_auth,
    monkeypatch,
):
    """Test that the datasets endpoint does not include subject data in the response."""
    monkeypatch.setattr(
        crud, "post_query_to_graph", mock_post_agg_query_to_graph
    )
    monkeypatch.setattr(
        crud, "query_matching_dataset_sizes", mock_query_matching_dataset_sizes
    )

    response = test_app.post(ROUTE, json={})
    assert response.status_code == 200
    assert all(
        "subject_data" not in matching_dataset
        for matching_dataset in response.json()
    )


@pytest.mark.parametrize("valid_iscontrol", ["true", True, None])
def test_post_valid_iscontrol(
    test_app,
    mock_successful_query_records,
    valid_iscontrol,
    disable_auth,
    monkeypatch,
):
    monkeypatch.setattr(crud, "query_records", mock_successful_query_records)
    response = test_app.post(ROUTE, json={"is_control": valid_iscontrol})
    assert response.status_code == 200
    assert response.json() != []


@pytest.mark.parametrize("mock_query_records", [None], indirect=True)
@pytest.mark.parametrize("invalid_iscontrol", [False, 0, []])
def test_post_invalid_iscontrol(
    test_app, mock_query_records, invalid_iscontrol, disable_auth, monkeypatch
):
    monkeypatch.setattr(crud, "query_records", mock_query_records)
    response = test_app.post(ROUTE, json={"is_control": invalid_iscontrol})
    assert response.status_code == 422
    assert (
        "'is_control' must be either set to 'true' or omitted from the query"
        in response.json()
    )
