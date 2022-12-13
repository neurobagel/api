"""Test API to query subjects from the Stardog graph who match user-specified criteria."""

import httpx
import pytest

from app.api import crud


@pytest.fixture
def test_data():
    """Create toy data for two subjects for testing."""
    data = [
        {
            "number_session": "test1",
            "modality": "test1",
            "subject": "test1",
            "sub_id": "test1",
            "sex": "test1",
            "diagnosis": "test1",
            "dataset_name": "test1",
            "dataset": "test1",
            "age": "test1",
        },
        {
            "number_session": "test2",
            "modality": "test2",
            "subject": "test2",
            "sub_id": "test2",
            "sex": "test2",
            "diagnosis": "test2",
            "dataset_name": "test2",
            "dataset": "test2",
            "age": "test2",
        },
    ]
    return data


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


def test_get_all(test_data, test_app, monkeypatch):
    """Given no input for the sex parameter, returns a 200 status code and a non-empty list of results (should correspond to all subjects in graph)."""

    async def mock_get(age_min, age_max, sex):
        return test_data

    monkeypatch.setattr(crud, "get", mock_get)
    response = test_app.get("/query/")
    assert response.status_code == 200
    assert response.json() != []


@pytest.mark.parametrize("valid_sex", ["male", "female", "other"])
def test_get_sex(test_data, test_app, valid_sex, monkeypatch):
    """Given a valid sex string, returns a 200 status code and a non-empty list of results."""

    async def mock_get(age_min, age_max, sex):
        return test_data

    monkeypatch.setattr(crud, "get", mock_get)
    response = test_app.get(f"/query/?sex={valid_sex}")
    assert response.status_code == 200
    assert response.json() != []


def test_get_invalid_sex(test_app, monkeypatch):
    """Given an invalid sex string (i.e., anything other than ["male", "female", None]), returns a 422 status code."""

    async def mock_get(age_min, age_max, sex):
        return None

    monkeypatch.setattr(crud, "get", mock_get)
    response = test_app.get("/query/?sex=apple")
    assert response.status_code == 422


@pytest.mark.parametrize(
    "age_min_keyval, age_max_keyval",
    [
        ("age_min=30.5", "age_max=60"),
        ("age_min=20.75", None),
        (None, "age_max=50"),
    ],
)
def test_get_age(
    test_data, test_app, age_min_keyval, age_max_keyval, monkeypatch
):
    """Given a valid min age and max age, returns a 200 status code and a non-empty list of results."""

    async def mock_get(age_min, age_max, sex):
        return test_data

    monkeypatch.setattr(crud, "get", mock_get)
    response = test_app.get(f"/query/?{age_min_keyval}&{age_max_keyval}")
    assert response.status_code == 200
    assert response.json() != []
