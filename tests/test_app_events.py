"""Test events occurring on app startup or shutdown."""

import os
import warnings

import httpx
import pytest

from app.api import utility as util


@pytest.mark.filterwarnings("ignore:.*NB_API_ALLOWED_ORIGINS")
def test_start_app_without_environment_vars_fails(
    test_app, monkeypatch, disable_auth
):
    """Given non-existing username and password environment variables, raises an informative RuntimeError."""
    monkeypatch.delenv(util.GRAPH_USERNAME.name, raising=False)
    monkeypatch.delenv(util.GRAPH_PASSWORD.name, raising=False)

    with pytest.raises(RuntimeError) as e_info:
        with test_app:
            pass
    assert (
        f"could not find the {util.GRAPH_USERNAME.name} and / or {util.GRAPH_PASSWORD.name} environment variables"
        in str(e_info.value)
    )


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
    monkeypatch,
    set_test_credentials,
    disable_auth,
):
    """Tests that when the environment variable for allowed origins has not been set, a warning is raised and the app uses a default value."""
    monkeypatch.delenv(util.ALLOWED_ORIGINS.name, raising=False)

    with pytest.warns(
        UserWarning,
        match=f"API was launched without providing any values for the {util.ALLOWED_ORIGINS.name} environment variable",
    ):
        with test_app:
            pass

    assert util.parse_origins_as_list(
        os.environ.get(util.ALLOWED_ORIGINS.name, "")
    ) == [""]


@pytest.mark.parametrize(
    "allowed_origins, parsed_origins, expectation",
    [
        (
            "",
            [""],
            pytest.warns(
                UserWarning,
                match=f"API was launched without providing any values for the {util.ALLOWED_ORIGINS.name} environment variable",
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
    set_test_credentials,
    allowed_origins,
    parsed_origins,
    expectation,
    disable_auth,
):
    """
    Test that when the environment variable for allowed origins has been explicitly set, the app correctly parses it into a list
    and raises a warning if the value is an empty string.
    """
    monkeypatch.setenv(util.ALLOWED_ORIGINS.name, allowed_origins)

    with expectation:
        with test_app:
            pass

    assert set(parsed_origins).issubset(
        util.parse_origins_as_list(
            os.environ.get(util.ALLOWED_ORIGINS.name, "")
        )
    )


@pytest.mark.parametrize(
    "lookup_file",
    ["snomed_disorder", "snomed_assessment"],
)
@pytest.mark.filterwarnings("ignore:.*NB_API_ALLOWED_ORIGINS")
def test_stored_vocab_lookup_file_created_on_startup(
    test_app,
    set_test_credentials,
    disable_auth,
    lookup_file,
):
    """Test that on startup, a non-empty temporary lookup file is created for term ID-label mappings for the locally stored SNOMED CT vocabulary."""
    with test_app:
        term_labels_path = test_app.app.state.vocab_lookup_paths[lookup_file]
        assert term_labels_path.exists()
        assert term_labels_path.stat().st_size > 0
