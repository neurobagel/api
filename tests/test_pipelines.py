from app.api import crud

BASE_ROUTE = "/pipelines"


def test_get_pipeline_versions_response(
    test_app, monkeypatch, set_test_credentials
):
    """
    Given a request to /attributes/nb:Pipeline/{resource}/versions with a valid pipeline name,
    returns a dict where the key is the pipeline resource and the value is a list of pipeline versions.
    """
    mock_graph_response = {
        "head": {"vars": ["pipeline_version"]},
        "results": {
            "bindings": [
                {"pipeline_version": {"type": "literal", "value": "23.1.3"}},
                {"pipeline_version": {"type": "literal", "value": "20.2.7"}},
            ]
        },
    }
    # NOTE: We get away with a single param lambda func here because the API route function
    # (attributes.get_pipeline_versions) that calls post_query_to_graph uses the default timeout,
    # so we don't need to worry about that extra parameter when mocking
    monkeypatch.setattr(
        crud, "post_query_to_graph", lambda x: mock_graph_response
    )

    response = test_app.get(f"{BASE_ROUTE}/np:fmriprep/versions")
    assert response.status_code == 200
    assert response.json() == {"np:fmriprep": ["23.1.3", "20.2.7"]}
