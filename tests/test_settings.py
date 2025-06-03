from app.api.config import Settings


def test_settings_read_correctly(monkeypatch):
    """Ensure that settings are read correctly from environment variables, with correct types and default values."""
    test_unset_env_vars = [
        "NB_NAPI_BASE_PATH",
        "NB_GRAPH_ADDRESS",
        "NB_ENABLE_AUTH",
        "NB_QUERY_CLIENT_ID",
    ]
    # Explicitly unset environment variables that we expect to be unset based on pytest.ini
    # in order to accurately test default values.
    # This ensures that any variables that have been set in the local environment outside of pytest.ini
    # (i.e., when running tests locally in a dev environment) do not interfere with the test.
    for var in test_unset_env_vars:
        monkeypatch.delenv(var, raising=False)

    settings = Settings()

    # Check that defaults are applied correctly for environment variables that are undefined
    assert settings.root_path == ""
    assert settings.graph_address == "127.0.0.1"
    assert settings.auth_enabled is True
    assert settings.client_id is None

    # Check that defaults are applied correctly for environment variables that
    # have been set to empty strings
    assert settings.graph_db == "repositories/my_db"

    # Check that set environment variables are read and typed correctly
    assert settings.allowed_origins == "*"
    assert settings.graph_username == "DBUSER"
    assert settings.graph_password == "DBPASSWORD"
    assert settings.graph_port == 7201
    assert settings.return_agg is False
    assert settings.min_cell_size == 1
