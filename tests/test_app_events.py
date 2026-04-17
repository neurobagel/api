"""Test events occurring on app startup or shutdown."""

import logging
from pathlib import Path

import pytest

from app import main
from app.api import env_settings
from app.main import settings


def test_start_app_without_environment_vars_fails(
    test_app,
    disable_auth,
    set_temp_datasets_metadata_file,
    monkeypatch,
    caplog,
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


def fetched_configs_includes_neurobagel(disable_auth):
    """Test that "Neurobagel" is included among the available configuration names fetched from GitHub."""
    assert "Neurobagel" in main.fetch_available_community_config_names()


def test_app_exits_when_config_unrecognized(
    test_app,
    disable_auth,
    set_temp_datasets_metadata_file,
    monkeypatch,
    caplog,
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


def test_app_exits_when_datasets_metadata_file_not_found(
    test_app, disable_auth, monkeypatch, caplog
):
    """Test that when the provided datasets metadata file path does not exist, the app raises an error."""
    monkeypatch.setattr(
        settings, "datasets_metadata_path", Path("/non/existent/file.json")
    )
    expected_msg = "Datasets metadata file for the node not found"

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
