"""Test API to query subjects from the Stardog graph who match user-specified criteria."""


def test_get_input(test_app):
    """Given a valid sex string, returns a 200 status code."""
    response = test_app.get("/query/?sex=female")
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
