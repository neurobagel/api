import logging

import httpx
import pytest

from app.api import env_settings
from app.api.env_settings import settings
from app.api.models import DataElementURI


def test_get_instances_endpoint_with_vocab_lookup(
    test_app,
    monkeypatch,
    # Since this test runs the API startup events to fetch the vocabularies used in the test,
    # we need to disable auth to avoid startup errors about unset auth-related environment variables.
    disable_auth,
    mock_context,
    caplog,
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

    expected_warning = [
        "http://unknownvocab.org/123456789",
        "does not come from a vocabulary recognized by Neurobagel",
    ]

    async def mock_httpx_post(self, **kwargs):
        return httpx.Response(status_code=200, json=mock_response_json)

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_httpx_post)

    response = test_app.get("/assessments")

    warnings = [
        record
        for record in caplog.records
        if record.levelno == logging.WARNING
    ]
    assert len(warnings) == 1
    for expected_substr in expected_warning:
        assert expected_substr in warnings[0].getMessage()
    assert response.json() == {
        "nb:Assessment": [
            {
                "TermURL": "snomed:1284852002",
                "Label": "Numeric Pain Rating Scale",
            },
            {"TermURL": "snomed:not_found_id", "Label": None},
        ]
    }


def test_get_imaging_modalities_with_vocab_lookup(
    test_app,
    monkeypatch,
    disable_auth,
    mock_context,
):
    """
    Given a GET request to /imaging-modalities, test that the endpoint returns graph instances
    with labels and imaging-specific metadata (abbreviation, data_type) from the vocabulary.
    """
    monkeypatch.setattr(
        env_settings,
        "ALL_VOCABS",
        {
            DataElementURI.image.value: [
                {
                    "namespace_prefix": "nidm",
                    "namespace_url": "http://purl.org/nidash/nidm#",
                    "vocabulary_name": "Test vocabulary of imaging modalities",
                    "version": "1.0.0",
                    "terms": [
                        {
                            "id": "T1Weighted",
                            "name": "T1-weighted image",
                            "abbreviation": "T1w",
                            "data_type": "anat",
                        },
                        {
                            "id": "FlowWeighted",
                            "name": "Blood-Oxygen-Level Dependent image",
                            "abbreviation": "bold",
                            "data_type": "func",
                        },
                    ],
                }
            ]
        },
    )

    mock_response_json = {
        "head": {"vars": ["termURL"]},
        "results": {
            "bindings": [
                {
                    "termURL": {
                        "type": "uri",
                        "value": "http://purl.org/nidash/nidm#T1Weighted",
                    }
                },
                {
                    "termURL": {
                        "type": "uri",
                        "value": "http://purl.org/nidash/nidm#FlowWeighted",
                    }
                },
            ]
        },
    }

    async def mock_httpx_post(self, **kwargs):
        return httpx.Response(status_code=200, json=mock_response_json)

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_httpx_post)

    response = test_app.get("/imaging-modalities")

    assert response.json() == {
        "nb:Image": [
            {
                "TermURL": "nidm:T1Weighted",
                "Label": "T1-weighted image",
                "Abbreviation": "T1w",
                "DataType": "anat",
            },
            {
                "TermURL": "nidm:FlowWeighted",
                "Label": "Blood-Oxygen-Level Dependent image",
                "Abbreviation": "bold",
                "DataType": "func",
            },
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
        ("imaging-modalities", "nb:Image"),
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
        "nb:Image": [
            {
                "namespace_prefix": "nidm",
                "namespace_url": "http://purl.org/nidash/nidm#",
                "vocabulary_name": "Test vocab of imaging modalities",
                "version": "1.0.0",
                "terms": [
                    {
                        "id": "T1Weighted",
                        "name": "T1-weighted image",
                        "Abbreviation": "T1w",
                        "DataType": "anat",
                    }
                ],
            }
        ],
    }

    monkeypatch.setattr(env_settings, "ALL_VOCABS", mock_all_vocabs)

    response = test_app.get(f"/{attribute}/vocab")

    assert response.status_code == 200
    assert response.json() == mock_all_vocabs[standardized_variable_id]


def test_get_instances_endpoint_in_catalog_mode(
    test_app, monkeypatch, disable_auth, mock_context
):
    """
    Given a GET request to /assessments in catalog mode,
    test that the endpoint correctly returns the unique assessment terms
    found in the catalog dataset metadata.
    """
    mock_datasets_metadata = {
        "nb:18532368-82dc-42ac-b4fb-fbb187ad6ae1": {
            "dataset_name": "BIDS synthetic",
            "participant_count": 5,
            "repository_url": "https://github.com/bids-standard/bids-examples.git",
            "available_sex": [],
            "available_diagnoses": [],
            "available_assessments": [
                "snomed:859351000000102",
                "snomed:342061000000106",
            ],
            "age_range": {"minimum": 21.0, "maximum": 42.0},
        },
        "nb:80af4d30-0447-4f13-9eaf-98ae8065895a": {
            "dataset_name": "Rhyme judgment",
            "access_link": "https://github.com/OpenNeuroDatasets-JSONLD/ds000003.git",
            "participant_count": 10,
            "available_sex": [],
            "available_diagnoses": [],
            "available_assessments": ["snomed:859351000000102"],
            "age_range": {"minimum": 60.0, "maximum": 80.0},
        },
    }

    # Mock local vocabulary lookup
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
                            "id": "859351000000102",
                            "name": "Montreal cognitive assessment",
                        },
                        {
                            "id": "342061000000106",
                            "name": "Unified Parkinsons disease rating scale score",
                        },
                    ],
                }
            ]
        },
    )
    monkeypatch.setattr(settings, "catalog_mode", True)
    monkeypatch.setattr(
        env_settings, "DATASETS_METADATA", mock_datasets_metadata
    )

    response = test_app.get("/assessments")

    assert response.json() == {
        "nb:Assessment": [
            {
                "TermURL": "snomed:342061000000106",
                "Label": "Unified Parkinsons disease rating scale score",
            },
            {
                "TermURL": "snomed:859351000000102",
                "Label": "Montreal cognitive assessment",
            },
        ]
    }


@pytest.mark.parametrize(
    "attribute_path,expected_response",
    [
        ("/imaging-modalities", {"nb:Image": []}),
        ("/pipelines", {"nb:Pipeline": []}),
        ("/pipelines/np:fmriprep/versions", {"np:fmriprep": []}),
    ],
)
def test_no_imaging_variable_instances_returned_in_catalog_mode(
    test_app,
    monkeypatch,
    disable_auth,
    mock_context,
    attribute_path,
    expected_response,
):
    """
    Given a GET request for imaging modality or pipeline instances in catalog mode,
    test that the relevant endpoints return no results.

    TODO: Update once/if imaging metadata is supported for catalog datasets.
    """
    mock_datasets_metadata = {
        "nb:18532368-82dc-42ac-b4fb-fbb187ad6ae1": {
            "dataset_name": "BIDS synthetic",
            "participant_count": 5,
            "repository_url": "https://github.com/bids-standard/bids-examples.git",
            "available_sex": [],
            "available_diagnoses": [],
            "available_assessments": [
                "snomed:859351000000102",
                "snomed:342061000000106",
            ],
            "age_range": {"minimum": 21.0, "maximum": 42.0},
        },
        "nb:80af4d30-0447-4f13-9eaf-98ae8065895a": {
            "dataset_name": "Rhyme judgment",
            "access_link": "https://github.com/OpenNeuroDatasets-JSONLD/ds000003.git",
            "participant_count": 10,
            "available_sex": [],
            "available_diagnoses": [],
            "available_assessments": ["snomed:859351000000102"],
            "age_range": {"minimum": 60.0, "maximum": 80.0},
        },
    }

    # Mock local vocabulary lookup
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
                            "id": "859351000000102",
                            "name": "Montreal cognitive assessment",
                        },
                        {
                            "id": "342061000000106",
                            "name": "Unified Parkinsons disease rating scale score",
                        },
                    ],
                }
            ],
            "nb:Image": [
                {
                    "namespace_prefix": "nidm",
                    "namespace_url": "http://purl.org/nidash/nidm#",
                    "vocabulary_name": "Neurobagel vocabulary of imaging modality terms",
                    "version": "1.0.0",
                    "terms": [
                        {
                            "name": "T1-weighted image",
                            "id": "T1Weighted",
                            "abbreviation": "T1w",
                            "data_type": "anat",
                        },
                        {
                            "name": "T2-weighted image",
                            "id": "T2Weighted",
                            "abbreviation": "T2w",
                            "data_type": "anat",
                        },
                    ],
                }
            ],
        },
    )
    monkeypatch.setattr(settings, "catalog_mode", True)
    monkeypatch.setattr(
        env_settings, "DATASETS_METADATA", mock_datasets_metadata
    )

    response = test_app.get(attribute_path)

    assert response.json() == expected_response
