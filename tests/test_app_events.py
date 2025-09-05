"""Test events occurring on app startup or shutdown."""

import pytest

from app import main
from app.api import config
from app.api import utility as util
from app.main import settings


@pytest.mark.filterwarnings("ignore:.*NB_API_ALLOWED_ORIGINS")
def test_start_app_without_environment_vars_fails(
    test_app, disable_auth, monkeypatch
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
    assert "Neurobagel" in main.fetch_available_neurobagel_configs(
        main.NEUROBAGEL_CONFIGS_API_URL
    )


def test_app_exits_when_config_unrecognized(
    test_app, disable_auth, monkeypatch
):
    """Test that when the configuration is set to an unrecognized name, the app raises an error."""
    monkeypatch.setattr(settings, "config", "Unknown-Config")

    with pytest.raises(RuntimeError) as e_info:
        with test_app:
            pass
    assert "not a recognized Neurobagel configuration" in str(e_info.value)


def test_neurobagel_vocabularies_fetched_successfully(
    test_app, disable_auth, monkeypatch
):
    """
    Test that for a given configuration, the term vocabularies are fetched and stored
    in the correct shape on the app instance.
    """
    monkeypatch.setattr(settings, "config", "Neurobagel")
    with test_app:
        pass

    assert config.ALL_VOCABS != {}
    for var, vocab in config.ALL_VOCABS.items():
        assert "nb:" in var
        assert isinstance(vocab, list)
        assert "terms" in vocab[0]


def test_neurobagel_namespaces_fetched_successfully(
    test_app, disable_auth, monkeypatch
):
    """
    Test that for a given configuration, the recognized term namespaces are fetched and stored
    in the correct shape on the app instance.
    """
    monkeypatch.setattr(settings, "config", "Neurobagel")
    with test_app:
        pass

    assert config.CONTEXT != {}
    assert "nb" in config.CONTEXT
