"""Test API to query subjects from the Stardog graph who match user-specified criteria."""

import pytest

from app.api import crud


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

    response = test_app.get("/query/")
    assert response.status_code == 401


def test_get_all(test_app, monkeypatch):
    """Given no input for the sex parameter, returns a 200 status code and a non-empty list of results (should correspond to all subjects in graph)."""
    test_data = [
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

    async def mock_get(sex):
        return test_data

    monkeypatch.setattr(crud, "get", mock_get)
    response = test_app.get("/query/")
    assert response.status_code == 200
    assert response.json() != []


def test_get_input(test_app, monkeypatch):
    """Given a valid sex string, returns a 200 status code and a non-empty list of results."""
    test_data = [
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

    async def mock_get(sex):
        return test_data

    monkeypatch.setattr(crud, "get", mock_get)
    response = test_app.get("/query/?sex=female")
    assert response.json() != []
    assert response.status_code == 200


def test_get_invalid_input(test_app, monkeypatch):
    """Given an invalid sex string (i.e., anything other than ["male", "female", None]), returns a 422 status code."""

    async def mock_get(sex):
        return None

    monkeypatch.setattr(crud, "get", mock_get)
    response = test_app.get("/query/?sex=apple")
    assert response.status_code == 422
