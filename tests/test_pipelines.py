from app.api import crud

BASE_ROUTE = "/pipelines"


def test_get_pipeline_versions_response(test_app, monkeypatch):
    """
    Given a request to /pipelines/{pipeline_term}/versions with a valid pipeline name,
    returns a dict where the key is the pipeline resource and the value is a list of pipeline versions.
    """

    async def mock_post_query_to_graph(query, timeout=5.0):
        return [
            {"pipeline_version": "23.1.3"},
            {"pipeline_version": "20.2.7"},
        ]

    monkeypatch.setattr(crud, "post_query_to_graph", mock_post_query_to_graph)

    response = test_app.get(f"{BASE_ROUTE}/np:fmriprep/versions")
    assert response.status_code == 200
    assert response.json() == {"np:fmriprep": ["23.1.3", "20.2.7"]}
