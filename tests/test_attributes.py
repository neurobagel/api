"""Test API endpoint for querying controlled term attributes modeled by Neurobagel."""

import httpx


def test_get_attributes(
    test_app,
    monkeypatch,
    set_test_credentials,
):
    """Given a GET request to the /attributes/ endpoint, successfully returns controlled term attributes with namespaces abbrieviated and as a list."""
    mock_response_json = {
        "head": {"vars": ["attribute"]},
        "results": {
            "bindings": [
                {
                    "attribute": {
                        "type": "uri",
                        "value": "http://neurobagel.org/vocab/ControlledTerm1",
                    }
                },
                {
                    "attribute": {
                        "type": "uri",
                        "value": "http://neurobagel.org/vocab/ControlledTerm2",
                    }
                },
                {
                    "attribute": {
                        "type": "uri",
                        "value": "http://neurobagel.org/vocab/ControlledTerm3",
                    }
                },
            ]
        },
    }

    def mock_httpx_post(**kwargs):
        return httpx.Response(status_code=200, json=mock_response_json)

    monkeypatch.setattr(httpx, "post", mock_httpx_post)
    response = test_app.get("/attributes/")

    assert response.json() == [
        "nb:ControlledTerm1",
        "nb:ControlledTerm2",
        "nb:ControlledTerm3",
    ]
