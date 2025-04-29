from app.api import crud


def test_datasets_response_structure(
    test_app,
    mock_post_agg_query_to_graph,
    mock_query_matching_dataset_sizes,
    disable_auth,
    monkeypatch,
):
    """Test that the datasets endpoint returns a list of dicts with the expected keys."""
    monkeypatch.setattr(
        crud, "post_query_to_graph", mock_post_agg_query_to_graph
    )
    monkeypatch.setattr(
        crud, "query_matching_dataset_sizes", mock_query_matching_dataset_sizes
    )

    response = test_app.post("/datasets", json={})
    assert response.status_code == 200
    assert all(
        "subject_data" not in matching_dataset
        for matching_dataset in response.json()
    )
