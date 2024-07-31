import pytest

from app.api import crud


@pytest.mark.parametrize(
    "root_path",
    ["/", ""],
)
def test_root(test_app, root_path):
    """Given a GET request to the root endpoint, Check for 200 status and expected content."""

    response = test_app.get(root_path, follow_redirects=False)

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
