import httpx
import pytest

from app.api import env_settings


def test_get_instances_endpoint_with_vocab_lookup(
    test_app,
    monkeypatch,
    # Since this test runs the API startup events to fetch the vocabularies used in the test,
    # we need to disable auth to avoid startup errors about unset auth-related environment variables.
    disable_auth,
    mock_context,
):
    """
    Given a GET request to /assessments (attribute with a vocabulary lookup available),
    test that the endpoint correctly returns graph instances as prefixed term URIs and their human-readable labels
    (where found), and excludes term URIs with unrecognized namespaces with a warning.
    """
    monkeypatch.setattr(
        env_settings,
        "ALL_VOCABS",
        {
            "nb:Assessment": [
                {
                    "namespace_prefix": "snomed",
                    "namespace_url": "http://purl.bioontology.org/ontology/SNOMEDCT/",
                    "vocabulary_name": "Test vocabulary of assessment terms",
                    "version": "1.0.0",
                    "terms": [
                        {
                            "id": "1284852002",
                            "name": "Numeric Pain Rating Scale",
                        }
                    ],
                }
            ]
        },
    )

    # TODO: Since these mock HTTPX response JSONs are so similar (and useful),
    # we could refactor their creation out into a function.
    mock_response_json = {
        "head": {"vars": ["termURL"]},
        "results": {
            "bindings": [
                {
                    "termURL": {
                        "type": "uri",
                        "value": "http://purl.bioontology.org/ontology/SNOMEDCT/1284852002",
                    }
                },
                {
                    "termURL": {
                        "type": "uri",
                        "value": "http://purl.bioontology.org/ontology/SNOMEDCT/not_found_id",
                    }
                },
                {
                    "termURL": {
                        "type": "uri",
                        "value": "http://unknownvocab.org/123456789",
                    }
                },
            ]
        },
    }

    async def mock_httpx_post(self, **kwargs):
        return httpx.Response(status_code=200, json=mock_response_json)

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_httpx_post)

    with pytest.warns(
        UserWarning,
        match="does not come from a vocabulary recognized by Neurobagel",
    ):
        response = test_app.get("/assessments")

    assert response.json() == {
        "nb:Assessment": [
            {
                "TermURL": "snomed:1284852002",
                "Label": "Numeric Pain Rating Scale",
            },
            {"TermURL": "snomed:not_found_id", "Label": None},
        ]
    }


def test_get_instances_endpoint_without_vocab_lookup(
    test_app,
    monkeypatch,
):
    """
    Given a GET request to /pipelines (attribute without a vocabulary lookup available),
    test that the endpoint correctly returns the found graph instances as prefixed term URIs with empty label fields.
    """
    # Ensure that the API knows about some fake ontologies (with no vocabulary lookups)
    monkeypatch.setattr(
        env_settings,
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

    async def mock_httpx_post(self, **kwargs):
        return httpx.Response(status_code=200, json=mock_response_json)

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_httpx_post)

    response = test_app.get("/pipelines")

    assert response.json() == {
        "nb:Pipeline": [
            {"TermURL": "cko:trm_123", "Label": None},
            {"TermURL": "cko:trm_234", "Label": None},
        ]
    }


@pytest.mark.parametrize(
    "attribute, standardized_variable_id",
    [
        ("assessments", "nb:Assessment"),
        ("diagnoses", "nb:Diagnosis"),
    ],
)
def test_get_vocab_endpoint(
    test_app,
    monkeypatch,
    attribute,
    standardized_variable_id,
):
    """
    Given a GET request to the /vocab subpath for a specific attribute router,
    test that the endpoint returns a list containing the vocabulary and terms information
    for the relevant standardized variable.
    """
    # Ensure a temporary vocab term-label lookup file is available for the attribute
    mock_all_vocabs = {
        "nb:Assessment": [
            {
                "namespace_prefix": "snomed",
                "namespace_url": "http://purl.bioontology.org/ontology/SNOMEDCT/",
                "vocabulary_name": "Neurobagel vocabulary of Assessment terms",
                "version": "1.0.0",
                "terms": [
                    {"id": "1284852002", "name": "Numeric Pain Rating Scale"}
                ],
            }
        ],
        "nb:Diagnosis": [
            {
                "namespace_prefix": "ncit",
                "namespace_url": "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#",
                "vocabulary_name": "Test vocabulary for healthy control",
                "version": "1.0.0",
                "terms": [{"name": "Healthy Control", "id": "C94342"}],
            },
            {
                "namespace_prefix": "snomed",
                "namespace_url": "http://purl.bioontology.org/ontology/SNOMEDCT/",
                "vocabulary_name": "Test vocabulary of disorder terms",
                "version": "1.0.0",
                "terms": [
                    {"id": "26929004", "name": "Alzheimer's disease"},
                ],
            },
        ],
    }

    monkeypatch.setattr(env_settings, "ALL_VOCABS", mock_all_vocabs)

    response = test_app.get(f"/{attribute}/vocab")

    assert response.status_code == 200
    assert response.json() == mock_all_vocabs[standardized_variable_id]
