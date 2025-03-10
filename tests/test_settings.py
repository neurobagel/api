from app.api.config import Settings


def test_settings_read_correctly():
    """Ensure that settings are read correctly from environment variables, with correct types and default values."""
    settings = Settings()

    # Check that defaults are applied correctly for environment variables that are undefined
    # or have been set to empty strings
    assert settings.root_path == ""
    assert settings.graph_address == "127.0.0.1"
    assert settings.graph_db == "repositories/my_db"
    assert settings.auth_enabled is True
    assert settings.client_id is None

    # Check that set environment variables are read and typed correctly
    assert settings.allowed_origins == "*"
    assert settings.graph_username == "DBUSER"
    assert settings.graph_password == "DBPASSWORD"
    assert settings.graph_port == 7201
    assert settings.return_agg is False
    assert settings.min_cell_size == 1
