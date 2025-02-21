"""Test events occurring on app startup or shutdown."""

import warnings

import httpx
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


# TODO: Check that this test is actually useful - it assumes that a graph user already exists.
# This would probably make more sense as an integration test
# Previously, this test was likely passing because the monkeypatched environment variables were not actually being used
# due to import order issues?
@pytest.mark.filterwarnings("ignore:.*NB_API_ALLOWED_ORIGINS")
def test_app_with_invalid_environment_vars(
    test_app, monkeypatch, mock_auth_header, set_mock_verify_token
):
    """Given invalid environment variables for the graph, returns a 401 status code."""
    monkeypatch.setenv(util.GRAPH_USERNAME.name, "something")
    monkeypatch.setenv(util.GRAPH_PASSWORD.name, "cool")

    def mock_httpx_post(**kwargs):
        return httpx.Response(status_code=401)

    monkeypatch.setattr(httpx, "post", mock_httpx_post)
    response = test_app.get("/query", headers=mock_auth_header)
    assert response.status_code == 401


def test_app_with_unset_allowed_origins(
    test_app,
    disable_auth,
    monkeypatch,
):
    """Tests that when the environment variable for allowed origins has not been set, a warning is raised and the app uses a default value."""
    monkeypatch.setattr(settings, "allowed_origins", "")

    with pytest.warns(
        UserWarning,
        match="API was launched without providing any values for the NB_API_ALLOWED_ORIGINS environment variable",
    ):
        with test_app:
            pass

    assert util.parse_origins_as_list(settings.allowed_origins) == [""]


@pytest.mark.parametrize(
    "allowed_origins, parsed_origins, expectation",
    [
        (
            "",
            [""],
            pytest.warns(
                UserWarning,
                match="API was launched without providing any values for the NB_API_ALLOWED_ORIGINS environment variable",
            ),
        ),
        (
            "http://localhost:3000",
            ["http://localhost:3000"],
            warnings.catch_warnings(),
        ),
        (
            "http://localhost:3000 https://localhost:3000",
            ["http://localhost:3000", "https://localhost:3000"],
            warnings.catch_warnings(),
        ),
        (
            " http://localhost:3000 https://localhost:3000  ",
            ["http://localhost:3000", "https://localhost:3000"],
            warnings.catch_warnings(),
        ),
    ],
)
def test_app_with_set_allowed_origins(
    test_app,
    monkeypatch,
    allowed_origins,
    parsed_origins,
    expectation,
    disable_auth,
):
    """
    Test that when the environment variable for allowed origins has been explicitly set, the app correctly parses it into a list
    and raises a warning if the value is an empty string.
    """
    monkeypatch.setattr(settings, "allowed_origins", allowed_origins)

    with expectation:
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
