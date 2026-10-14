"""Test API endpoint for querying standardized variables modeled by Neurobagel."""

import httpx


def test_get_attributes(test_app, monkeypatch, mock_context):
    """Given a GET request to the /attributes endpoint, successfully returns standardized variable URIs with namespaces abbrieviated and as a list."""
    mock_response_json = {
        "head": {"vars": ["attribute"]},
        "results": {
            "bindings": [
                {
                    "attribute": {
                        "type": "uri",
                        "value": "http://neurobagel.org/vocab/StandardizedVariable1",
                    }
                },
                {
                    "attribute": {
                        "type": "uri",
                        "value": "http://neurobagel.org/vocab/StandardizedVariable2",
                    }
                },
                {
                    "attribute": {
                        "type": "uri",
                        "value": "http://neurobagel.org/vocab/StandardizedVariable3",
                    }
                },
            ]
        },
    }

    async def mock_httpx_post(self, **kwargs):
        return httpx.Response(status_code=200, json=mock_response_json)

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_httpx_post)
    response = test_app.get("/attributes")

    assert response.json() == [
        "nb:StandardizedVariable1",
        "nb:StandardizedVariable2",
        "nb:StandardizedVariable3",
    ]
