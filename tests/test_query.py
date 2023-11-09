"""Test API to query subjects from the graph database who match user-specified criteria."""

import json
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


def test_external_vocab_is_fetched_on_startup(test_app, monkeypatch):
    """
    Tests that on startup, a GET request is made to the Cognitive Atlas API and that when the request succeeds,
    the term ID-label mappings from the returned vocab are stored in a temporary lookup file.
    """
    monkeypatch.setenv(util.GRAPH_USERNAME.name, "SomeUser")
    monkeypatch.setenv(util.GRAPH_PASSWORD.name, "SomePassword")
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
        term_labels_path = test_app.app.state.cogatlas_term_lookup_path
        assert term_labels_path.exists()

        with open(term_labels_path, "r") as f:
            term_labels = json.load(f)

        assert term_labels == {
            "tsk_p7cabUkVvQPBS": "Generalized Self-Efficacy Scale",
            "tsk_ccTKYnmv7tOZY": "Verbal Interference Test",
        }


def test_failed_vocab_fetching_on_startup_raises_warning(
    test_app, monkeypatch
):
    """
    Tests that when a GET request to the Cognitive Atlas API fails (e.g., due to service being unavailable),
    a warning is raised and that a term label lookup file is still created using a backup copy of the vocab.
    """
    monkeypatch.setenv(util.GRAPH_USERNAME.name, "SomeUser")
    monkeypatch.setenv(util.GRAPH_PASSWORD.name, "SomePassword")

    def mock_httpx_get(**kwargs):
        return httpx.Response(
            status_code=503, json={}, text="Some error message"
        )

    monkeypatch.setattr(httpx, "get", mock_httpx_get)

    with pytest.warns(UserWarning) as w:
        with test_app:
            assert test_app.app.state.cogatlas_term_lookup_path.exists()

    assert any(
        "unable to fetch the Cognitive Atlas task vocabulary (https://www.cognitiveatlas.org/tasks/a/) from the source and will default to using a local backup copy"
        in str(warn.message)
        for warn in w
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
    "valid_data_element_URI",
    ["nb:Diagnosis", "nb:Assessment"],
)
def test_get_terms_valid_data_element_URI(
    test_app, mock_successful_get_terms, valid_data_element_URI, monkeypatch
):
    """Given a valid data element URI, returns a 200 status code and a non-empty list of terms for that data element."""

    monkeypatch.setattr(crud, "get_terms", mock_successful_get_terms)
    response = test_app.get(f"/attributes/{valid_data_element_URI}")
    assert response.status_code == 200
    first_key = next(iter(response.json()))
    assert response.json()[first_key] != []


@pytest.mark.parametrize(
    "invalid_data_element_URI",
    ["apple", "some_thing:cool"],
)
def test_get_terms_invalid_data_element_URI(
    test_app, invalid_data_element_URI
):
    """Given an invalid data element URI, returns a 422 status code as the validation of the data element URI fails."""

    response = test_app.get(f"/attributes/{invalid_data_element_URI}")
    assert response.status_code == 422


def test_get_terms_for_attribute_with_vocab_lookup(test_app, monkeypatch):
    """
    Given a valid data element URI with a vocabulary lookup file available, returns prefixed term URIs and their human-readable labels (where found)
    for instances of that data element, and excludes terms with unrecognized namespaces with an informative warning.
    """
    monkeypatch.setenv(util.GRAPH_USERNAME.name, "SomeUser")
    monkeypatch.setenv(util.GRAPH_PASSWORD.name, "SomePassword")

    # TODO: Since these mock HTTPX response JSONs are so similar (and useful), refactor their creation out into a function.
    mock_response_json = {
        "head": {"vars": ["termURL"]},
        "results": {
            "bindings": [
                {
                    "termURL": {
                        "type": "uri",
                        "value": "https://www.cognitiveatlas.org/task/id/tsk_U9gDp8utahAfO",
                    }
                },
                {
                    "termURL": {
                        "type": "uri",
                        "value": "https://www.cognitiveatlas.org/task/id/not_found_id",
                    }
                },
                {
                    "termURL": {
                        "type": "uri",
                        "value": "https://www.notanatlas.org/task/id/tsk_alz5hjlUXp4WY",
                    }
                },
            ]
        },
    }

    def mock_httpx_post(**kwargs):
        return httpx.Response(status_code=200, json=mock_response_json)

    monkeypatch.setattr(httpx, "post", mock_httpx_post)

    with pytest.warns(
        UserWarning,
        match="does not come from a vocabulary recognized by Neurobagel",
    ):
        with test_app:
            response = test_app.get("/attributes/nb:Assessment")

    assert response.json() == {
        "nb:Assessment": [
            {
                "TermURL": "cogatlas:tsk_U9gDp8utahAfO",
                "Label": "Pittsburgh Stress Battery",
            },
            {"TermURL": "cogatlas:not_found_id", "Label": None},
        ]
    }


def test_get_terms_for_attribute_without_vocab_lookup(test_app, monkeypatch):
    """
    Given a valid data element URI without any vocabulary lookup file available, returns prefixed term URIs and  instances of that data element, and excludes terms with unrecognized namespaces with an informative warning.
    """
    monkeypatch.setenv(util.GRAPH_USERNAME.name, "SomeUser")
    monkeypatch.setenv(util.GRAPH_PASSWORD.name, "SomePassword")
    # Create a mock context with some fake ontologies (with no vocabulary lookup files)
    monkeypatch.setattr(
        util,
        "CONTEXT",
        {
            "cko": "https://www.coolknownontology.org/task/id/",
            "ako": "https://www.awesomeknownontology.org/vocab/",
        },
    )

    mock_response_json = {
        "head": {"vars": ["termURL"]},
        "results": {
            "bindings": [
                {
                    "termURL": {
                        "type": "uri",
                        "value": "https://www.coolknownontology.org/task/id/trm_123",
                    }
                },
                {
                    "termURL": {
                        "type": "uri",
                        "value": "https://www.coolknownontology.org/task/id/trm_234",
                    }
                },
            ]
        },
    }

    def mock_httpx_post(**kwargs):
        return httpx.Response(status_code=200, json=mock_response_json)

    monkeypatch.setattr(httpx, "post", mock_httpx_post)

    response = test_app.get("/attributes/nb:SomeClass")

    assert response.json() == {
        "nb:SomeClass": [
            {"TermURL": "cko:trm_123", "Label": None},
            {"TermURL": "cko:trm_234", "Label": None},
        ]
    }


def test_get_attributes(
    test_app,
    monkeypatch,
):
    """Given a GET request to the /attributes/ endpoint, successfully returns controlled term attributes with namespaces abbrieviated and as a list."""

    monkeypatch.setenv(util.GRAPH_USERNAME.name, "SomeUser")
    monkeypatch.setenv(util.GRAPH_PASSWORD.name, "SomePassword")

    mock_response_json = {
        "head": {"vars": ["attribute"]},
        "results": {
            "bindings": [
                {
                    "attribute": {
                        "type": "uri",
                        "value": "http://neurobagel.org/vocab/ControlledTerm1",
                    }
                },
                {
                    "attribute": {
                        "type": "uri",
                        "value": "http://neurobagel.org/vocab/ControlledTerm2",
                    }
                },
                {
                    "attribute": {
                        "type": "uri",
                        "value": "http://neurobagel.org/vocab/ControlledTerm3",
                    }
                },
            ]
        },
    }

    def mock_httpx_post(**kwargs):
        return httpx.Response(status_code=200, json=mock_response_json)

    monkeypatch.setattr(httpx, "post", mock_httpx_post)
    response = test_app.get("/attributes/")

    assert response.json() == [
        "nb:ControlledTerm1",
        "nb:ControlledTerm2",
        "nb:ControlledTerm3",
    ]


def test_get_attribute_vocab(test_app, monkeypatch):
    """Given a GET request to the /attributes/{data_element_URI}/vocab endpoint, successfully returns a JSON object containing the vocabulary name, namespace info, and term-label mappings."""
    monkeypatch.setenv(util.GRAPH_USERNAME.name, "SomeUser")
    monkeypatch.setenv(util.GRAPH_PASSWORD.name, "SomePassword")
    mock_term_labels = {
        "tsk_p7cabUkVvQPBS": "Generalized Self-Efficacy Scale",
        "tsk_ccTKYnmv7tOZY": "Verbal Interference Test",
    }

    def mock_load_json(path):
        return mock_term_labels

    monkeypatch.setattr(util, "load_json", mock_load_json)
    response = test_app.get("/attributes/nb:Assessment/vocab")

    assert response.status_code == 200
    assert response.json() == {
        "vocabulary_name": "Cognitive Atlas Tasks",
        "namespace_url": util.CONTEXT["cogatlas"],
        "namespace_prefix": "cogatlas",
        "term_labels": mock_term_labels,
    }
