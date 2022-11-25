def test_get_input(test_app):
    response = test_app.get("/query/?sex=female")
    assert response.status_code == 200


def test_get_invalid_input(test_app):
    response = test_app.get("/query/?sex=apple")
    assert response.status_code == 422
