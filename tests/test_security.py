import pytest
from fastapi import HTTPException

from app.api.env_settings import settings
from app.api.security import verify_token


@pytest.mark.filterwarnings("ignore:.*NB_API_ALLOWED_ORIGINS")
def test_missing_client_id_raises_error_when_auth_enabled(
    monkeypatch, test_app, enable_auth, set_temp_datasets_metadata_file
):
    """Test that a missing client ID raises an error on startup when authentication is enabled."""
    # We're using what should be default values of client_id and auth_enabled here
    # (if the corresponding environment variables are unset),
    # but we set the values explicitly here for clarity
    monkeypatch.setattr(settings, "client_id", None)

    with pytest.raises(RuntimeError) as exc_info:
        with test_app:
            pass

    assert "NB_QUERY_CLIENT_ID is not set" in str(exc_info.value)


@pytest.mark.filterwarnings("ignore:.*NB_API_ALLOWED_ORIGINS")
def test_missing_client_id_ignored_when_auth_disabled(
    monkeypatch, test_app, set_temp_datasets_metadata_file
):
    """Test that a missing client ID does not raise an error when authentication is disabled."""
    monkeypatch.setattr(settings, "client_id", None)
    monkeypatch.setattr(settings, "auth_enabled", False)

    with test_app:
        pass


@pytest.mark.parametrize(
    "invalid_token",
    ["Bearer faketoken", "Bearer", "faketoken", "fakescheme faketoken"],
)
def test_invalid_token_raises_error(invalid_token):
    """Test that an invalid token raises an error from the verification process."""
    with pytest.raises(HTTPException) as exc_info:
        verify_token(invalid_token)

    assert exc_info.value.status_code == 401
    assert "Invalid token" in exc_info.value.detail


@pytest.mark.parametrize(
    "invalid_auth_header",
    [{}, {"Authorization": ""}, {"badheader": "badvalue"}],
)
def test_query_with_malformed_auth_header_fails(
    test_app,
    set_mock_verify_token,
    enable_auth,
    invalid_auth_header,
    monkeypatch,
):
    """
    Test that when authentication is enabled, a request to the /query route with a
    missing or malformed authorization header fails.
    """
    monkeypatch.setattr(settings, "client_id", "foo.id")

    response = test_app.get(
        "/query",
        headers=invalid_auth_header,
    )

    assert response.status_code == 403
