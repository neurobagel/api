import pytest

from app.api import crud
from app.main import app, favicon_url


@pytest.mark.parametrize(
    "route",
    ["/", ""],
)
def test_root(test_app, route, monkeypatch):
    """Given a GET request to the root endpoint, Check for 200 status and expected content."""
    # root_path determines the path prefix for the docs link on the welcome page
    monkeypatch.setattr(app, "root_path", "")
    response = test_app.get(route, follow_redirects=False)

    assert response.status_code == 200
    assert "Welcome to the Neurobagel REST API!" in response.text
    assert '<a href="/docs">API documentation</a>' in response.text


@pytest.mark.parametrize(
    "valid_route",
    ["/query", "/query?min_age=20"],
)
def test_request_without_trailing_slash_not_redirected(
    test_app, monkeypatch, mock_successful_get, disable_auth, valid_route
):
    """Test that a request to a route without a / is not redirected to have a trailing slash."""
    monkeypatch.setattr(crud, "query_records", mock_successful_get)
    response = test_app.get(valid_route, follow_redirects=False)
    assert response.status_code == 200


@pytest.mark.parametrize(
    "invalid_route",
    [
        "/query/",
        "/query/?min_age=20",
        "/attributes/",
        "/assessments/",
        "/assessments/vocab/",
    ],
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
    "test_route,expected_status_code",
    [("", 200), ("/api/v1", 200), ("/wrongroot", 404)],
)
def test_docs_work_using_defined_root_path(
    test_app, test_route, expected_status_code, monkeypatch
):
    """
    Test that when the API root_path is set to a non-empty string,
    the interactive docs and OpenAPI schema are only reachable with the correct path prefix
    (e.g., mimicking access through a proxy) or without the prefix entirely (e.g., mimicking local access or by a proxy itself).

    Note: We test the OpenAPI schema as well because when the root path is not set correctly,
    the docs break from failure to fetch openapi.json.
    (https://fastapi.tiangolo.com/advanced/behind-a-proxy/#proxy-with-a-stripped-path-prefix)
    """

    monkeypatch.setattr(app, "root_path", "/api/v1")
    docs_response = test_app.get(f"{test_route}/docs", follow_redirects=False)
    schema_response = test_app.get(
        f"{test_route}/openapi.json", follow_redirects=False
    )
    assert docs_response.status_code == expected_status_code
    assert schema_response.status_code == expected_status_code


@pytest.mark.parametrize(
    "test_route,expected_status_code",
    [("/favicon.ico", 307), ("/api/favicon.ico", 307)],
)
def test_favicon_reachable_with_defined_root_path(
    test_app, monkeypatch, test_route, expected_status_code
):
    """
    Test that when the API root_path is set to a non-empty string, the favicon is still reachable
    with the correct root path prefix or without the prefix.

    Adapted from https://github.com/fastapi/fastapi/issues/790#issuecomment-607636599
    """
    monkeypatch.setattr(app, "root_path", "/api")
    # Disable follow_redirects to expose the 307 status, since the favicon route redirects to an external image URL
    response = test_app.get(test_route, follow_redirects=False)
    assert response.status_code == expected_status_code
    assert response.headers["location"] == favicon_url
