def test_get_input(test_app):
    response = test_app.get("/subjects/?sex=female")
    assert response.status_code == 200


def test_get_invalid_input(test_app):
    response = test_app.get("/subjects/?sex=apple")
    assert response.status_code == 422
