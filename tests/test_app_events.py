"""Test events occurring on app startup or shutdown."""

import json
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


@pytest.mark.filterwarnings("ignore:.*NB_API_ALLOWED_ORIGINS")
def test_stored_vocab_lookup_file_created_on_startup(
    test_app,
    set_test_credentials,
    disable_auth,
):
    """Test that on startup, a non-empty temporary lookup file is created for term ID-label mappings for the locally stored SNOMED CT vocabulary."""
    with test_app:
        term_labels_path = test_app.app.state.vocab_lookup_paths["snomed"]
        assert term_labels_path.exists()
        assert term_labels_path.stat().st_size > 0


@pytest.mark.filterwarnings("ignore:.*NB_API_ALLOWED_ORIGINS")
def test_external_vocab_is_fetched_on_startup(
    test_app, monkeypatch, set_test_credentials, disable_auth
):
    """
    Tests that on startup, a GET request is made to the Cognitive Atlas API and that when the request succeeds,
    the term ID-label mappings from the returned vocab are stored in a temporary lookup file.
    """
    mock_vocab_json = [
        {
            "creation_time": 1689609836,
            "last_updated": 1689609836,
            "name": "Generalized Self-Efficacy Scale",
            "definition_text": "The original Generalized Self-Efficacy Scale contains 10 items designed to tap into a global sense of self-efficacy, or belief of an individual in his or her ability (e.g., \u201cI can always solve difficult problems if I try hard enough,\u201d and \u201cI can usually handle whatever comes my way.\u201d) The revised version here includes these 10 items and two, which are repeated and reversed to examine acquiescence bias. Response options range from 1, never true, to 7, always true. Higher scores indicate greater generalized self-efficacy.",
            "id": "tsk_p7cabUkVvQPBS",
        },
        {
            "creation_time": 1689610375,
            "last_updated": 1689610375,
            "name": "Verbal Interference Test",
            "definition_text": "The Verbal Interference Test is a behavioral assessment of cognitive regulation. In this task participants are presented with visual word stimuli that appear with incongruent text and color meaning (e.g., the word \u201cRED\u201d printed in blue, the word \u201cBLUE\u201d printed in green, the word \u201cGREEN\u201d printed in red). There are two phases of the task: Name (Part I) and Color (Part II). In the Name phase, participants are asked to identify the meaning of the word (e.g., red is the correct answer for the word \u201cRED\u201d printed in blue). In the Color phase, participants are asked to identify the color in which the word is printed (e.g., blue is the correct answer for the word \u201cRED\u201d printed in blue). This test assesses aspects of inhibition and interference corresponding to those indexed by the Stroop test.",
            "id": "tsk_ccTKYnmv7tOZY",
        },
    ]

    def mock_httpx_get(**kwargs):
        return httpx.Response(status_code=200, json=mock_vocab_json)

    monkeypatch.setattr(httpx, "get", mock_httpx_get)

    with test_app:
        term_labels_path = test_app.app.state.vocab_lookup_paths["cogatlas"]
        assert term_labels_path.exists()

        with open(term_labels_path, "r") as f:
            term_labels = json.load(f)

        assert term_labels == {
            "tsk_p7cabUkVvQPBS": "Generalized Self-Efficacy Scale",
            "tsk_ccTKYnmv7tOZY": "Verbal Interference Test",
        }


@pytest.mark.filterwarnings("ignore:.*NB_API_ALLOWED_ORIGINS")
def test_failed_vocab_fetching_on_startup_raises_warning(
    test_app, monkeypatch, set_test_credentials, disable_auth
):
    """
    Tests that when a GET request to the Cognitive Atlas API has a non-success response code (e.g., due to service being unavailable),
    a warning is raised and that a term label lookup file is still created using a backup copy of the vocab.
    """

    def mock_httpx_get(**kwargs):
        return httpx.Response(
            status_code=503, json={}, text="Some error message"
        )

    monkeypatch.setattr(httpx, "get", mock_httpx_get)

    with pytest.warns(UserWarning) as w:
        with test_app:
            assert test_app.app.state.vocab_lookup_paths["cogatlas"].exists()

    assert any(
        "unable to fetch the Cognitive Atlas task vocabulary (https://www.cognitiveatlas.org/tasks/a/) from the source and will default to using a local backup copy"
        in str(warn.message)
        for warn in w
    )


@pytest.mark.filterwarnings("ignore:.*NB_API_ALLOWED_ORIGINS")
def test_network_error_on_startup_raises_warning(
    test_app, monkeypatch, set_test_credentials, disable_auth
):
    """
    Tests that when a GET request to the Cognitive Atlas API fails due to a network error (i.e., while issuing the request),
    a warning is raised and that a term label lookup file is still created using a backup copy of the vocab.
    """

    def mock_httpx_get(**kwargs):
        raise httpx.ConnectError("Some network error")

    monkeypatch.setattr(httpx, "get", mock_httpx_get)

    with pytest.warns(UserWarning) as w:
        with test_app:
            assert test_app.app.state.vocab_lookup_paths["cogatlas"].exists()

    assert any(
        "failed due to a network error" in str(warn.message) for warn in w
    )
