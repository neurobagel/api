"""Test events occurring on app startup or shutdown."""

import pytest

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


@pytest.mark.parametrize(
    "lookup_file",
    ["snomed_disorder", "snomed_assessment"],
)
@pytest.mark.filterwarnings("ignore:.*NB_API_ALLOWED_ORIGINS")
def test_stored_vocab_lookup_file_created_on_startup(
    test_app,
    disable_auth,
    lookup_file,
):
    """Test that on startup, a non-empty temporary lookup file is created for term ID-label mappings for the locally stored SNOMED CT vocabulary."""
    with test_app:
        term_labels_path = test_app.app.state.vocab_lookup_paths[lookup_file]
        assert term_labels_path.exists()
        assert term_labels_path.stat().st_size > 0
