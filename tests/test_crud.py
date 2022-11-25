def test_get_invalid_sex(test_app):
    response = test_app.get("/subjects/?sex=apple")
    assert response.status_code == 422
