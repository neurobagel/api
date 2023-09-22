"""Test API to query subjects from the Stardog graph who match user-specified criteria."""

import os
import warnings

import httpx
import pytest
from fastapi import HTTPException

from app.api import crud
from app.api import utility as util


def test_start_app_without_environment_vars_fails(test_app, monkeypatch):
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


def test_app_with_invalid_environment_vars(test_app, monkeypatch):
    """Given invalid environment variables, returns a 401 status code."""
    monkeypatch.setenv(util.GRAPH_USERNAME.name, "something")
    monkeypatch.setenv(util.GRAPH_PASSWORD.name, "cool")

    def mock_httpx_post(**kwargs):
        return httpx.Response(status_code=401)

    monkeypatch.setattr(httpx, "post", mock_httpx_post)
    response = test_app.get("/query/")
    assert response.status_code == 401


def test_app_with_unset_allowed_origins(test_app, monkeypatch):
    """Tests that when the environment variable for allowed origins has not been set, a warning is raised and the app uses a default value."""
    monkeypatch.delenv(util.ALLOWED_ORIGINS.name, raising=False)
    # set random username and password to avoid RuntimeError from other startup check
    monkeypatch.setenv(util.GRAPH_USERNAME.name, "DBUSER")
    monkeypatch.setenv(util.GRAPH_PASSWORD.name, "DBPASSWORD")

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
    test_app, monkeypatch, allowed_origins, parsed_origins, expectation
):
    """
    Test that when the environment variable for allowed origins has been explicitly set, the app correctly parses it into a list
    and raises a warning if the value is an empty string.
    """
    monkeypatch.setenv(util.ALLOWED_ORIGINS.name, allowed_origins)
    # set random username and password to avoid RuntimeError from other startup check
    monkeypatch.setenv(util.GRAPH_USERNAME.name, "DBUSER")
    monkeypatch.setenv(util.GRAPH_PASSWORD.name, "DBPASSWORD")

    with expectation:
        with test_app:
            pass

    assert set(parsed_origins).issubset(
        util.parse_origins_as_list(
            os.environ.get(util.ALLOWED_ORIGINS.name, "")
        )
    )


def test_get_all(test_app, mock_successful_get, monkeypatch):
    """Given no input for the sex parameter, returns a 200 status code and a non-empty list of results (should correspond to all subjects in graph)."""

    monkeypatch.setattr(crud, "get", mock_successful_get)
    response = test_app.get("/query/")
    assert response.status_code == 200
    assert response.json() != []


@pytest.mark.parametrize(
    "valid_min_age, valid_max_age",
    [(30.5, 60), (23, 23)],
)
def test_get_valid_age_range(
    test_app, mock_successful_get, valid_min_age, valid_max_age, monkeypatch
):
    """Given a valid age range, returns a 200 status code and a non-empty list of results."""

    monkeypatch.setattr(crud, "get", mock_successful_get)
    response = test_app.get(
        f"/query/?min_age={valid_min_age}&max_age={valid_max_age}"
    )
    assert response.status_code == 200
    assert response.json() != []


@pytest.mark.parametrize(
    "age_keyval",
    ["min_age=20.75", "max_age=50"],
)
def test_get_valid_age_single_bound(
    test_app, mock_successful_get, age_keyval, monkeypatch
):
    """Given only a valid lower/upper age bound, returns a 200 status code and a non-empty list of results."""

    monkeypatch.setattr(crud, "get", mock_successful_get)
    response = test_app.get(f"/query/?{age_keyval}")
    assert response.status_code == 200
    assert response.json() != []


@pytest.mark.parametrize(
    "invalid_min_age, invalid_max_age",
    [
        ("forty", "fifty"),
        (33, 21),
        (-42.5, -40),
    ],
)
def test_get_invalid_age(
    test_app, mock_invalid_get, invalid_min_age, invalid_max_age, monkeypatch
):
    """Given an invalid age range, returns a 422 status code."""

    monkeypatch.setattr(crud, "get", mock_invalid_get)
    response = test_app.get(
        f"/query/?min_age={invalid_min_age}&max_age={invalid_max_age}"
    )
    assert response.status_code == 422


@pytest.mark.parametrize(
    "valid_sex",
    ["snomed:248153007", "snomed:248152002", "snomed:32570681000036106"],
)
def test_get_valid_sex(test_app, mock_successful_get, valid_sex, monkeypatch):
    """Given a valid sex string, returns a 200 status code and a non-empty list of results."""

    monkeypatch.setattr(crud, "get", mock_successful_get)
    response = test_app.get(f"/query/?sex={valid_sex}")
    assert response.status_code == 200
    assert response.json() != []


def test_get_invalid_sex(test_app, mock_invalid_get, monkeypatch):
    """Given an invalid sex string, returns a 422 status code."""

    monkeypatch.setattr(crud, "get", mock_invalid_get)
    response = test_app.get("/query/?sex=apple")
    assert response.status_code == 422


@pytest.mark.parametrize(
    "valid_diagnosis", ["snomed:35489007", "snomed:49049000"]
)
def test_get_valid_diagnosis(
    test_app, mock_successful_get, valid_diagnosis, monkeypatch
):
    """Given a valid diagnosis, returns a 200 status code and a non-empty list of results."""

    monkeypatch.setattr(crud, "get", mock_successful_get)
    response = test_app.get(f"/query/?diagnosis={valid_diagnosis}")
    assert response.status_code == 200
    assert response.json() != []


@pytest.mark.parametrize(
    "invalid_diagnosis", ["sn0med:35489007", "apple", ":123456"]
)
def test_get_invalid_diagnosis(
    test_app, mock_invalid_get, invalid_diagnosis, monkeypatch
):
    """Given an invalid diagnosis, returns a 422 status code."""

    monkeypatch.setattr(crud, "get", mock_invalid_get)
    response = test_app.get(f"/query/?diagnosis={invalid_diagnosis}")
    assert response.status_code == 422


@pytest.mark.parametrize("valid_iscontrol", [True, False])
def test_get_valid_iscontrol(
    test_app, mock_successful_get, valid_iscontrol, monkeypatch
):
    """Given a valid is_control value, returns a 200 status code and a non-empty list of results."""

    monkeypatch.setattr(crud, "get", mock_successful_get)
    response = test_app.get(f"/query/?is_control={valid_iscontrol}")
    assert response.status_code == 200
    assert response.json() != []


def test_get_invalid_iscontrol(test_app, mock_invalid_get, monkeypatch):
    """Given a non-boolean is_control value, returns a 422 status code."""

    monkeypatch.setattr(crud, "get", mock_invalid_get)
    response = test_app.get("/query/?is_control=apple")
    assert response.status_code == 422


def test_get_invalid_control_diagnosis_pair(
    test_app, mock_invalid_get, monkeypatch
):
    """Given a non-default diagnosis value and is_control value of True, returns a 422 status code."""

    monkeypatch.setattr(crud, "get", mock_invalid_get)
    response = test_app.get(
        "/query/?diagnosis=snomed:35489007&is_control=True"
    )
    assert response.status_code == 422
    assert (
        "Subjects cannot both be healthy controls and have a diagnosis"
        in response.text
    )


@pytest.mark.parametrize("valid_min_num_sessions", [1, 2, 4, 7])
def test_get_valid_min_num_sessions(
    test_app, mock_successful_get, valid_min_num_sessions, monkeypatch
):
    """Given a valid minimum number of imaging sessions, returns a 200 status code and a non-empty list of results."""

    monkeypatch.setattr(crud, "get", mock_successful_get)
    response = test_app.get(
        f"/query/?min_num_sessions={valid_min_num_sessions}"
    )
    assert response.status_code == 200
    assert response.json() != []


@pytest.mark.parametrize("invalid_min_num_sessions", [0, -3, "apple"])
def test_get_invalid_min_num_sessions(
    test_app, mock_invalid_get, invalid_min_num_sessions, monkeypatch
):
    """Given an invalid minimum number of imaging sessions, returns a 422 status code."""

    monkeypatch.setattr(crud, "get", mock_invalid_get)
    response = test_app.get(
        f"/query/?min_num_sessions={invalid_min_num_sessions}"
    )
    response.status_code = 422


def test_get_valid_assessment(test_app, mock_successful_get, monkeypatch):
    """Given a valid assessment, returns a 200 status code and a non-empty list of results."""

    monkeypatch.setattr(crud, "get", mock_successful_get)
    response = test_app.get("/query/?assessment=nb:cogAtlas-1234")
    assert response.status_code == 200
    assert response.json() != []


@pytest.mark.parametrize(
    "invalid_assessment", ["bg01:cogAtlas-1234", "cogAtlas-1234"]
)
def test_get_invalid_assessment(
    test_app, mock_invalid_get, invalid_assessment, monkeypatch
):
    """Given an invalid assessment, returns a 422 status code."""

    monkeypatch.setattr(crud, "get", mock_invalid_get)
    response = test_app.get(f"/query/?assessment={invalid_assessment}")
    assert response.status_code == 422


@pytest.mark.parametrize(
    "valid_available_image_modal",
    [
        "nidm:DiffusionWeighted",
        "nidm:EEG",
        "nidm:FlowWeighted",
        "nidm:T1Weighted",
        "nidm:T2Weighted",
    ],
)
def test_get_valid_available_image_modal(
    test_app, mock_successful_get, valid_available_image_modal, monkeypatch
):
    """Given a valid and available image modality, returns a 200 status code and a non-empty list of results."""

    monkeypatch.setattr(crud, "get", mock_successful_get)
    response = test_app.get(
        f"/query/?image_modal={valid_available_image_modal}"
    )
    assert response.status_code == 200
    assert response.json() != []


@pytest.mark.parametrize(
    "valid_unavailable_image_modal",
    ["nidm:Flair", "owl:sameAs", "nb:FlowWeighted", "snomed:something"],
)
def test_get_valid_unavailable_image_modal(
    test_app, valid_unavailable_image_modal, monkeypatch
):
    """Given a valid, pre-defined, and unavailable image modality, returns a 200 status code and an empty list of results."""

    async def mock_get(
        min_age,
        max_age,
        sex,
        diagnosis,
        is_control,
        min_num_sessions,
        assessment,
        image_modal,
    ):
        return []

    monkeypatch.setattr(crud, "get", mock_get)
    response = test_app.get(
        f"/query/?image_modal={valid_unavailable_image_modal}"
    )

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.parametrize(
    "invalid_image_modal", ["2nim:EEG", "apple", "some_thing:cool"]
)
def test_get_invalid_image_modal(
    test_app, mock_invalid_get, invalid_image_modal, monkeypatch
):
    """Given an invalid image modality, returns a 422 status code."""

    monkeypatch.setattr(crud, "get", mock_invalid_get)
    response = test_app.get(f"/query/?image_modal={invalid_image_modal}")
    assert response.status_code == 422


@pytest.mark.parametrize(
    "undefined_prefix_image_modal",
    ["dbo:abstract", "sex:apple", "something:cool"],
)
def test_get_undefined_prefix_image_modal(
    test_app, undefined_prefix_image_modal, monkeypatch
):
    """Given a valid and undefined prefix image modality, returns a 500 status code."""

    async def mock_get(
        min_age,
        max_age,
        sex,
        diagnosis,
        is_control,
        min_num_sessions,
        assessment,
        image_modal,
    ):
        raise HTTPException(500)

    monkeypatch.setattr(crud, "get", mock_get)
    response = test_app.get(
        f"/query/?image_modal={undefined_prefix_image_modal}"
    )
    assert response.status_code == 500


@pytest.mark.parametrize(
    "valid_attribute_URI",
    ["nb:Diagnosis", "nb:Assessment"],
)
def test_get_terms_valid_attribute_URI(
    test_app, mock_successful_get_terms, valid_attribute_URI, monkeypatch
):
    """Given a valid attribute URI, returns a 200 status code and a non-empty list of terms for that attribute."""

    monkeypatch.setattr(crud, "get_terms", mock_successful_get_terms)
    response = test_app.get(f"/query/attributes/{valid_attribute_URI}")
    assert response.status_code == 200
    first_key = next(iter(response.json()))
    assert response.json()[first_key] != []


@pytest.mark.parametrize(
    "invalid_attribute_URI",
    ["apple", "some_thing:cool"],
)
def test_get_terms_invalid_attribute_URI(
    test_app, mock_invalid_get_terms, invalid_attribute_URI, monkeypatch
):
    """Given a valid attribute URI, returns a 422 status code."""

    monkeypatch.setattr(crud, "get_terms", mock_invalid_get_terms)
    response = test_app.get(f"/query/attributes/{invalid_attribute_URI}")
    assert response.status_code == 422
