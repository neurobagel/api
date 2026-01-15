"""Test events occurring on app startup or shutdown."""

from pathlib import Path

import pytest

from app import main
from app.api import env_settings
from app.api import utility as util
from app.main import settings


@pytest.mark.filterwarnings("ignore:.*NB_API_ALLOWED_ORIGINS")
def test_start_app_without_environment_vars_fails(
    test_app, disable_auth, set_temp_datasets_metadata_file, monkeypatch
):
    """Given non-existing username and password environment variables, raises an informative RuntimeError."""
    monkeypatch.setattr(settings, "graph_username", None)
    monkeypatch.setattr(settings, "graph_password", None)

    with pytest.raises(RuntimeError) as e_info:
        with test_app:
            pass
    assert (
        "could not find the NB_GRAPH_USERNAME and / or NB_GRAPH_PASSWORD environment variables"
        in str(e_info.value)
    )


def test_app_with_unset_allowed_origins(
    test_app,
    disable_auth,
    set_temp_datasets_metadata_file,
    monkeypatch,
):
    """Tests that when the environment variable for allowed origins has not been set, a warning is raised and the app uses an empty list."""
    monkeypatch.setattr(settings, "allowed_origins", None)

    with pytest.warns(
        UserWarning,
        match="API was launched without providing any values for the NB_API_ALLOWED_ORIGINS environment variable",
    ):
        with test_app:
            pass

    assert util.parse_origins_as_list(settings.allowed_origins) == []


@pytest.mark.parametrize(
    "allowed_origins, parsed_origins",
    [
        ("http://localhost:3000", ["http://localhost:3000"]),
        (
            "http://localhost:3000 https://localhost:3000",
            ["http://localhost:3000", "https://localhost:3000"],
        ),
        (
            " http://localhost:3000 https://localhost:3000  ",
            ["http://localhost:3000", "https://localhost:3000"],
        ),
    ],
)
def test_app_with_set_allowed_origins(
    test_app,
    monkeypatch,
    allowed_origins,
    parsed_origins,
    disable_auth,
    set_temp_datasets_metadata_file,
):
    """
    Test that when the environment variable for allowed origins has been explicitly set, the app correctly parses it into a list
    and raises a warning if the value is an empty string.
    """
    monkeypatch.setattr(settings, "allowed_origins", allowed_origins)

    with test_app:
        pass

    assert set(parsed_origins).issubset(
        util.parse_origins_as_list(settings.allowed_origins)
    )


def fetched_configs_includes_neurobagel(test_app, disable_app):
    """Test that "Neurobagel" is included among the available configuration names fetched from GitHub."""
    assert "Neurobagel" in main.fetch_available_community_config_names()


def test_app_exits_when_config_unrecognized(
    test_app, disable_auth, set_temp_datasets_metadata_file, monkeypatch
):
    """Test that when the configuration is set to an unrecognized name, the app raises an error."""
    monkeypatch.setattr(settings, "config", "Unknown-Config")

    with pytest.raises(RuntimeError) as e_info:
        with test_app:
            pass
    assert "not a recognized Neurobagel community configuration" in str(
        e_info.value
    )


def test_app_exits_when_datasets_metadata_file_not_found(
    test_app, disable_auth, monkeypatch
):
    """Test that when the provided datasets metadata file path does not exist, the app raises an error."""
    monkeypatch.setattr(
        settings, "datasets_metadata_path", Path("/non/existent/file.json")
    )
    with pytest.raises(RuntimeError) as e_info:
        with test_app:
            pass
    assert "Datasets metadata file for the node not found" in str(e_info.value)


def test_neurobagel_vocabularies_fetched_successfully(
    test_app, disable_auth, set_temp_datasets_metadata_file, monkeypatch
):
    """
    Test that for a given configuration, the term vocabularies are fetched and stored
    in the correct shape on the app instance.
    """
    monkeypatch.setattr(settings, "config", "Neurobagel")
    with test_app:
        fetched_vocabs = env_settings.ALL_VOCABS.copy()

    assert fetched_vocabs != {}
    for var, vocab in fetched_vocabs.items():
        assert "nb:" in var
        assert isinstance(vocab, list)
        assert "terms" in vocab[0]


def test_neurobagel_namespaces_fetched_successfully(
    test_app, disable_auth, set_temp_datasets_metadata_file, monkeypatch
):
    """
    Test that for a given configuration, the recognized term namespaces are fetched and stored
    in the correct shape on the app instance.
    """
    monkeypatch.setattr(settings, "config", "Neurobagel")
    with test_app:
        fetched_context = env_settings.CONTEXT.copy()

    assert fetched_context
    assert "nb" in fetched_context
