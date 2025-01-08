import pytest

from app.api import crud
from app.main import app


@pytest.mark.parametrize(
    "route",
    ["/", ""],
)
def test_root(test_app, route, monkeypatch):
    """Given a GET request to the root endpoint, Check for 200 status and expected content."""
    # root_path determines the docs link on the welcome page
    monkeypatch.setattr(app, "root_path", "")
    response = test_app.get(route, follow_redirects=False)

    assert response.status_code == 200
    assert "Welcome to the Neurobagel REST API!" in response.text
    assert '<a href="/docs">documentation</a>' in response.text


@pytest.mark.parametrize(
    "valid_route",
    ["/query", "/query?min_age=20"],
)
def test_request_without_trailing_slash_not_redirected(
    test_app, monkeypatch, mock_successful_get, disable_auth, valid_route
):
    """Test that a request to a route without a / is not redirected to have a trailing slash."""
    monkeypatch.setattr(crud, "get", mock_successful_get)
    response = test_app.get(valid_route, follow_redirects=False)
    assert response.status_code == 200


@pytest.mark.parametrize(
    "invalid_route",
    ["/query/", "/query/?min_age=20", "/attributes/nb:SomeClass/"],
)
def test_request_with_trailing_slash_not_redirected(
    test_app, disable_auth, invalid_route
):
    """
    Test that a request to routes including a trailing slash, where none is expected,
    is *not* redirected to exclude the slash, and returns a 404.
    """
    response = test_app.get(invalid_route)
    assert response.status_code == 404


@pytest.mark.parametrize(
    "test_root_path,expected_status_code",
    [("", 200), ("/api/v1", 200), ("/wrongroot", 404)],
)
def test_docs_work_using_defined_root_path(
    test_app, test_root_path, expected_status_code, monkeypatch
):
    monkeypatch.setattr(app, "root_path", "/api/v1")
    docs_response = test_app.get(
        f"{test_root_path}/docs", follow_redirects=False
    )
    # When the root path is not set correctly, the docs can break due to failure to fetch openapi.json
    # See also https://fastapi.tiangolo.com/advanced/behind-a-proxy/#proxy-with-a-stripped-path-prefix
    schema_response = test_app.get(
        f"{test_root_path}/openapi.json", follow_redirects=False
    )
    assert docs_response.status_code == expected_status_code
    assert schema_response.status_code == expected_status_code
