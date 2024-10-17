import httpx
import pytest

from app.api import utility as util


def test_get_instances_endpoint_with_vocab_lookup(
    test_app,
    monkeypatch,
    set_test_credentials,
    # Since this test runs the API startup events to fetch the vocabularies used in the test,
    # we need to disable auth to avoid startup errors about unset auth-related environment variables.
    disable_auth,
):
    """
    Given a GET request to /assessments/ (attribute with an external vocabulary lookup file available),
    test that the endpoint correctly returns graph instances as prefixed term URIs and their human-readable labels
    (where found), and excludes term URIs with unrecognized namespaces with a warning.
    """
    # TODO: Since these mock HTTPX response JSONs are so similar (and useful),
    # we could refactor their creation out into a function.
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
            response = test_app.get("/assessments/")

    assert response.json() == {
        "nb:Assessment": [
            {
                "TermURL": "cogatlas:tsk_U9gDp8utahAfO",
                "Label": "Pittsburgh Stress Battery",
            },
            {"TermURL": "cogatlas:not_found_id", "Label": None},
        ]
    }


def test_get_instances_endpoint_without_vocab_lookup(
    test_app, monkeypatch, set_test_credentials
):
    """
    Given a GET request to /pipelines/ (attribute without a vocabulary lookup file available),
    test that the endpoint correctly returns the found graph instances as prefixed term URIs with empty label fields.
    """
    # Ensure that the API knows about some fake ontologies (with no vocabulary lookup files)
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

    response = test_app.get("/pipelines/")

    assert response.json() == {
        "nb:Pipeline": [
            {"TermURL": "cko:trm_123", "Label": None},
            {"TermURL": "cko:trm_234", "Label": None},
        ]
    }


@pytest.mark.parametrize(
    "attribute, expected_vocab_name, expected_namespace_pfx",
    [
        ("assessments", "Cognitive Atlas Tasks", "cogatlas"),
        ("diagnoses", "SNOMED CT", "snomed"),
    ],
)
def test_get_vocab_endpoint(
    test_app,
    monkeypatch,
    set_test_credentials,
    attribute,
    expected_vocab_name,
    expected_namespace_pfx,
):
    """
    Given a GET request to the /vocab subpath for a specific attribute router,
    test that the endpoint returns a JSON object containing the correct vocabulary name,
    namespace info, and term-label mappings for the attribute.
    """
    # Ensure a temporary vocab term-label lookup file is available for the attribute
    mock_term_labels = {
        "trm_1234": "Generic Vocabulary Term 1",
        "trm_2345": "Generic Vocabulary Term 2",
    }

    def mock_load_json(path):
        return mock_term_labels

    monkeypatch.setattr(util, "load_json", mock_load_json)
    response = test_app.get(f"/{attribute}/vocab")

    assert response.status_code == 200
    assert response.json() == {
        "vocabulary_name": expected_vocab_name,
        "namespace_url": util.CONTEXT[expected_namespace_pfx],
        "namespace_prefix": expected_namespace_pfx,
        "term_labels": mock_term_labels,
    }
