"""Test events occurring on app startup or shutdown."""

import logging

import pytest

from app import main
from app.api import env_settings
from app.api import utility as util
from app.main import settings


def test_start_app_without_environment_vars_fails(
    test_app, disable_auth, monkeypatch, caplog
):
    """Given non-existing username and password environment variables, raises an informative RuntimeError."""
    monkeypatch.setattr(settings, "graph_username", None)
    monkeypatch.setattr(settings, "graph_password", None)
    expected_msg = "could not find the NB_GRAPH_USERNAME and / or NB_GRAPH_PASSWORD environment variables"

    with pytest.raises(RuntimeError) as e_info:
        with test_app:
            pass

    errors = [
        record for record in caplog.records if record.levelno == logging.ERROR
    ]
    assert len(errors) == 1
    assert expected_msg in errors[0].getMessage()
    assert expected_msg in str(e_info.value)


def test_app_with_unset_allowed_origins(
    test_app,
    disable_auth,
    monkeypatch,
    caplog,
):
    """Tests that when the environment variable for allowed origins has not been set, a warning is raised and the app uses an empty list."""
    monkeypatch.setattr(settings, "allowed_origins", None)

    with test_app:
        pass

    warnings = [
        record
        for record in caplog.records
        if record.levelno == logging.WARNING
    ]
    assert len(warnings) == 1
    assert (
        "API was launched without providing any values for the NB_API_ALLOWED_ORIGINS environment variable"
        in warnings[0].getMessage()
    )
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
    Test that when the environment variable for allowed origins has been explicitly set,
    the app correctly parses it into a list.
    """
    monkeypatch.setattr(settings, "allowed_origins", allowed_origins)

    with test_app:
        pass

    assert set(parsed_origins).issubset(
        util.parse_origins_as_list(settings.allowed_origins)
    )


def fetched_configs_includes_neurobagel(disable_auth):
    """Test that "Neurobagel" is included among the available configuration names fetched from GitHub."""
    assert "Neurobagel" in main.fetch_available_community_config_names()


def test_app_exits_when_config_unrecognized(
    test_app, disable_auth, monkeypatch, caplog
):
    """Test that when the configuration is set to an unrecognized name, the app raises an error."""
    monkeypatch.setattr(settings, "config", "Unknown-Config")
    expected_msg = "not a recognized Neurobagel community configuration"

    with pytest.raises(RuntimeError) as e_info:
        with test_app:
            pass

    errors = [
        record for record in caplog.records if record.levelno == logging.ERROR
    ]
    assert len(errors) == 1
    assert expected_msg in errors[0].getMessage()
    assert expected_msg in str(e_info.value)


def test_neurobagel_vocabularies_fetched_successfully(
    test_app, disable_auth, monkeypatch
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
    test_app, disable_auth, monkeypatch
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
