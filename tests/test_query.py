"""Test API to query subjects from the Stardog graph who match user-specified criteria."""

import httpx
import pytest
from fastapi import HTTPException

from app.api import crud


@pytest.fixture()
def test_data():
    """Create toy data for two datasets for testing."""
    return [
        {
            "dataset": "http://neurobagel.org/vocab/qpn",
            "dataset_name": "QPN",
            "num_matching_subjects": 50,
        },
        {
            "dataset": "http://neurobagel.org/vocab/ppmi",
            "dataset_name": "PPMI",
            "num_matching_subjects": 40,
        },
    ]


@pytest.fixture
def mock_successful_get(test_data):
    """Mock get function that returns non-empty query results."""

    async def mockreturn(
        age_min,
        age_max,
        sex,
        diagnosis,
        is_control,
        min_num_sessions,
        image_modal,
    ):
        return test_data

    return mockreturn


def test_start_app_without_environment_vars_fails(test_app, monkeypatch):
    """Given non-existing USER and PASSWORD environment variables, raises an informative RuntimeError."""
    monkeypatch.delenv("USER", raising=False)
    monkeypatch.delenv("PASSWORD", raising=False)

    with pytest.raises(RuntimeError) as e_info:
        with test_app:
            pass
    assert (
        "could not find the USER and / or PASSWORD environment variables"
        in str(e_info.value)
    )


def test_app_with_invalid_environment_vars(test_app, monkeypatch):
    """Given invalid environment variables, returns a 401 status code."""
    monkeypatch.setenv("USER", "something")
    monkeypatch.setenv("PASSWORD", "cool")

    def mock_httpx_post(**kwargs):
        return httpx.Response(status_code=401)

    monkeypatch.setattr(httpx, "post", mock_httpx_post)
    response = test_app.get("/query/")
    assert response.status_code == 401


def test_get_all(test_app, mock_successful_get, monkeypatch):
    """Given no input for the sex parameter, returns a 200 status code and at least one dataset with subjects (should correspond to all subjects in graph)."""

    monkeypatch.setattr(crud, "get", mock_successful_get)
    response = test_app.get("/query/")
    assert response.status_code == 200
    assert 0 not in [i["num_matching_subjects"] for i in response.json()]


@pytest.mark.parametrize(
    "valid_age_min, valid_age_max",
    [(30.5, 60), (23, 23)],
)
def test_get_valid_age_range(
    test_app, mock_successful_get, valid_age_min, valid_age_max, monkeypatch
):
    """Given a valid age range, returns a 200 status code and at least one dataset with subjects."""

    monkeypatch.setattr(crud, "get", mock_successful_get)
    response = test_app.get(
        f"/query/?age_min={valid_age_min}&age_max={valid_age_max}"
    )
    assert response.status_code == 200
    assert 0 not in [i["num_matching_subjects"] for i in response.json()]


@pytest.mark.parametrize(
    "age_keyval",
    ["age_min=20.75", "age_max=50"],
)
def test_get_valid_age_single_bound(
    test_app, mock_successful_get, age_keyval, monkeypatch
):
    """Given only a valid lower/upper age bound, returns a 200 status code and at least one dataset with subjects."""

    monkeypatch.setattr(crud, "get", mock_successful_get)
    response = test_app.get(f"/query/?{age_keyval}")
    assert response.status_code == 200
    assert 0 not in [i["num_matching_subjects"] for i in response.json()]


@pytest.mark.parametrize(
    "invalid_age_min, invalid_age_max",
    [
        ("forty", "fifty"),
        (33, 21),
        (-42.5, -40),
    ],
)
def test_get_invalid_age(
    test_app, invalid_age_min, invalid_age_max, monkeypatch
):
    """Given an invalid age range, returns a 422 status code."""

    async def mock_get(
        age_min,
        age_max,
        sex,
        diagnosis,
        is_control,
        min_num_sessions,
        image_modal,
    ):
        return None

    monkeypatch.setattr(crud, "get", mock_get)
    response = test_app.get(
        f"/query/?age_min={invalid_age_min}&age_max={invalid_age_max}"
    )
    assert response.status_code == 422


@pytest.mark.parametrize("valid_sex", ["male", "female", "other"])
def test_get_valid_sex(test_app, mock_successful_get, valid_sex, monkeypatch):
    """Given a valid sex string, returns a 200 status code and at least one dataset with subjects."""

    monkeypatch.setattr(crud, "get", mock_successful_get)
    response = test_app.get(f"/query/?sex={valid_sex}")
    assert response.status_code == 200
    assert 0 not in [i["num_matching_subjects"] for i in response.json()]


def test_get_invalid_sex(test_app, monkeypatch):
    """Given an invalid sex string (i.e., anything other than ["male", "female", None]), returns a 422 status code."""

    async def mock_get(
        age_min,
        age_max,
        sex,
        diagnosis,
        is_control,
        min_num_sessions,
        image_modal,
    ):
        return None

    monkeypatch.setattr(crud, "get", mock_get)
    response = test_app.get("/query/?sex=apple")
    assert response.status_code == 422


@pytest.mark.parametrize(
    "valid_diagnosis", ["snomed:35489007", "snomed:49049000"]
)
def test_get_valid_diagnosis(
    test_app, mock_successful_get, valid_diagnosis, monkeypatch
):
    """Given a valid diagnosis, returns a 200 status code and at least one dataset with subjects."""

    monkeypatch.setattr(crud, "get", mock_successful_get)
    response = test_app.get(f"/query/?diagnosis={valid_diagnosis}")
    assert response.status_code == 200
    assert 0 not in [i["num_matching_subjects"] for i in response.json()]


@pytest.mark.parametrize(
    "invalid_diagnosis", ["sn0med:35489007", "apple", ":123456"]
)
def test_get_invalid_diagnosis(test_app, invalid_diagnosis, monkeypatch):
    """Given an invalid diagnosis, returns a 422 status code."""

    async def mock_get(
        age_min,
        age_max,
        sex,
        diagnosis,
        is_control,
        min_num_sessions,
        image_modal,
    ):
        return None

    monkeypatch.setattr(crud, "get", mock_get)
    response = test_app.get(f"/query/?diagnosis={invalid_diagnosis}")
    assert response.status_code == 422


@pytest.mark.parametrize("valid_iscontrol", [True, False])
def test_get_valid_iscontrol(
    test_app, mock_successful_get, valid_iscontrol, monkeypatch
):
    """Given a valid is_control value, returns a 200 status code and at least one dataset with subjects."""

    monkeypatch.setattr(crud, "get", mock_successful_get)
    response = test_app.get(f"/query/?is_control={valid_iscontrol}")
    assert response.status_code == 200
    assert 0 not in [i["num_matching_subjects"] for i in response.json()]


def test_get_invalid_iscontrol(test_app, monkeypatch):
    """Given a non-boolean is_control value, returns a 422 status code."""

    async def mock_get(
        age_min,
        age_max,
        sex,
        diagnosis,
        is_control,
        min_num_sessions,
        image_modal,
    ):
        return None

    monkeypatch.setattr(crud, "get", mock_get)
    response = test_app.get("/query/?is_control=apple")
    assert response.status_code == 422


def test_get_invalid_control_diagnosis_pair(test_app, monkeypatch):
    """Given a non-default diagnosis value and is_control value of True, returns a 422 status code."""

    async def mock_get(
        age_min,
        age_max,
        sex,
        diagnosis,
        is_control,
        min_num_sessions,
        image_modal,
    ):
        return None

    monkeypatch.setattr(crud, "get", mock_get)
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
    """Given a valid minimum number of imaging sessions, returns a 200 status code and at least one dataset with subjects."""

    monkeypatch.setattr(crud, "get", mock_successful_get)
    response = test_app.get(
        f"/query/?min_num_sessions={valid_min_num_sessions}"
    )
    assert response.status_code == 200
    assert 0 not in [i["num_matching_subjects"] for i in response.json()]


@pytest.mark.parametrize("invalid_min_num_sessions", [0, -3, "apple"])
def test_get_invalid_min_num_sessions(
    test_app, invalid_min_num_sessions, monkeypatch
):
    """Given an invalid minimum number of imaging sessions, returns a 422 status code."""

    async def mock_get(
        age_min,
        age_max,
        sex,
        diagnosis,
        is_control,
        min_num_sessions,
        image_modal,
    ):
        return None

    monkeypatch.setattr(crud, "get", mock_get)
    response = test_app.get(
        f"/query/?min_num_sessions={invalid_min_num_sessions}"
    )
    response.status_code = 422


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
    """Given a valid and available image modality, returns a 200 status code and at least one dataset with subjects."""

    monkeypatch.setattr(crud, "get", mock_successful_get)
    response = test_app.get(
        f"/query/?image_modal={valid_available_image_modal}"
    )
    assert response.status_code == 200
    assert 0 not in [i["num_matching_subjects"] for i in response.json()]


@pytest.mark.parametrize(
    "valid_unavailable_image_modal",
    ["nidm:Flair", "owl:sameAs", "bg:FlowWeighted", "snomed:something"],
)
def test_get_valid_unavailable_image_modal(
    test_app, valid_unavailable_image_modal, monkeypatch
):
    """Given a valid, pre-defined, and unavailable image modality, returns a 200 status code and 0 matching subjects."""

    async def mock_get(
        age_min,
        age_max,
        sex,
        diagnosis,
        is_control,
        min_num_sessions,
        image_modal,
    ):
        return [
            {"dataset": None, "dataset_name": None, "num_matching_subjects": 0}
        ]

    monkeypatch.setattr(crud, "get", mock_get)
    response = test_app.get(
        f"/query/?image_modal={valid_unavailable_image_modal}"
    )
    assert response.status_code == 200
    assert response.json()[0]["num_matching_subjects"] == 0


@pytest.mark.parametrize(
    "invalid_image_modal", ["2nim:EEG", "apple", "some_thing:cool"]
)
def test_get_invalid_image_modal(test_app, invalid_image_modal, monkeypatch):
    """Given an invalid image modality, returns a 422 status code."""

    async def mock_get(
        age_min,
        age_max,
        sex,
        diagnosis,
        is_control,
        min_num_sessions,
        image_modal,
    ):
        return None

    monkeypatch.setattr(crud, "get", mock_get)
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
        age_min,
        age_max,
        sex,
        diagnosis,
        is_control,
        min_num_sessions,
        image_modal,
    ):
        raise HTTPException(500)

    monkeypatch.setattr(crud, "get", mock_get)
    response = test_app.get(
        f"/query/?image_modal={undefined_prefix_image_modal}"
    )
    assert response.status_code == 500
