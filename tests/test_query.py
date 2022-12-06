import pytest

"""Test API to query subjects from the Stardog graph who match user-specified criteria."""


def test_get_input(test_app):
    """Given a valid sex string, returns a 200 status code."""
    response = test_app.get("/query/?sex=female")
    assert response.json() != []
    assert response.status_code == 200


def test_get_invalid_input(test_app):
    """Given an invalid sex string (i.e., anything other than ["male", "female", None]), returns a 422 status code."""
    response = test_app.get("/query/?sex=apple")
    assert response.status_code == 422


def test_get_all(test_app):
    """Given no input for the sex parameter, returns a 200 status code and a non-empty list of results (should correspond to all subjects in graph)."""
    response = test_app.get("/query/")
    assert response.status_code == 200
    assert response.json() != []


def test_starting_app_without_environment_vars_fails(test_app, monkeypatch):
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
    monkeypatch.setenv("USER", "something")
    monkeypatch.setenv("PASSWORD", "cool")

    response = test_app.get("/query/")
    assert response.status_code == 401
