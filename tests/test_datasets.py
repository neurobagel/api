from app.api import crud, env_settings
from app.api.env_settings import settings

ROUTE = "/datasets"


async def test_response_includes_attributes_from_dataset_metadata_file(
    test_app,
    mock_context,  # needed because dataset lookup in the datasets metadata dict uses the prefixed namespace
    mock_query_matching_dataset_sizes,
    disable_auth,
    monkeypatch,
):
    """
    Test that the /datasets endpoint response includes all available metadata for a matching dataset,
    including information from the datasets metadata file.
    """
    mock_datasets_metadata = {
        "nb:12345": {
            "dataset_name": "Quebec Parkinson Network",
            "authors": ["First Author", "Second Author"],
            "homepage": "https://rpq-qpn.ca/en/home/",
            "keywords": ["Parkinson's disease", "Neuroimaging"],
            "access_type": "restricted",
            "access_link": "https://rpq-qpn.ca/en/researchers-section/databases/",
        },
        "nb:67890": {
            "dataset_name": "Other dataset",
            "access_link": "https://otherdataset.org/access",
        },
    }

    # Mock response for two matching subjects from the same dataset
    async def mock_post_datasets_query_to_graph(query):
        return [
            {
                "dataset": "http://neurobagel.org/vocab/12345",
                "subject": "sub-ON95534",
            },
            {
                "dataset": "http://neurobagel.org/vocab/12345",
                "subject": "sub-ON95535",
            },
        ]

    async def mock_query_available_modalities_and_pipelines(dataset_uuids):
        return {
            "http://neurobagel.org/vocab/12345": {
                "subject": "sub-ON95534",
                "image_modals": ["http://purl.org/nidash/nidm#T1Weighted"],
                "available_pipelines": {
                    "https://github.com/nipoppy/pipeline-catalog/tree/main/processing/freesurfer": [
                        "7.3.2"
                    ]
                },
            },
        }

    monkeypatch.setattr(settings, "return_agg", True)
    monkeypatch.setattr(
        env_settings, "DATASETS_METADATA", mock_datasets_metadata
    )
    monkeypatch.setattr(
        crud, "post_query_to_graph", mock_post_datasets_query_to_graph
    )
    monkeypatch.setattr(
        crud,
        "query_available_modalities_and_pipelines",
        mock_query_available_modalities_and_pipelines,
    )
    monkeypatch.setattr(
        crud, "query_matching_dataset_sizes", mock_query_matching_dataset_sizes
    )

    response = test_app.post(ROUTE, json={})
    matching_datasets = response.json()

    assert response.status_code == 200
    assert len(matching_datasets) == 1
    assert matching_datasets[0] == {
        "dataset_uuid": "http://neurobagel.org/vocab/12345",
        "dataset_name": "Quebec Parkinson Network",
        "authors": ["First Author", "Second Author"],
        "homepage": "https://rpq-qpn.ca/en/home/",
        "references_and_links": [],
        "keywords": ["Parkinson's disease", "Neuroimaging"],
        "repository_url": None,
        "access_instructions": None,
        "access_type": "restricted",
        "access_email": None,
        "access_link": "https://rpq-qpn.ca/en/researchers-section/databases/",
        "dataset_total_subjects": 200,
        "records_protected": True,
        "num_matching_subjects": 2,
        "image_modals": ["http://purl.org/nidash/nidm#T1Weighted"],
        "available_pipelines": {
            "https://github.com/nipoppy/pipeline-catalog/tree/main/processing/freesurfer": [
                "7.3.2"
            ]
        },
    }


async def test_imaging_modals_and_pipelines_query(monkeypatch):
    """
    Test that SPARQL query results for available imaging modalities and pipelines are
    processed correctly into a dictionary lookup keyed on dataset UUIDs.
    """
    # Setup
    matching_dataset_uuids = [
        "http://neurobagel.org/vocab/test-001",
        "http://neurobagel.org/vocab/test-002",
        "http://neurobagel.org/vocab/test-003",
    ]

    async def mock_post_query_to_graph(query):
        """Mock response to SPARQL query from graph."""
        return [
            {
                "dataset_uuid": "http://neurobagel.org/vocab/test-001",
                "image_modal": "http://purl.org/nidash/nidm#T1Weighted",
                "pipeline_name": "https://github.com/nipoppy/pipeline-catalog/tree/main/processing/fmriprep",
                "pipeline_version": "23.2.0",
            },
            {
                "dataset_uuid": "http://neurobagel.org/vocab/test-001",
                "image_modal": "http://purl.org/nidash/nidm#T1Weighted",
                "pipeline_name": "https://github.com/nipoppy/pipeline-catalog/tree/main/processing/mriqc",
                "pipeline_version": "22.0.6",
            },
            {
                "dataset_uuid": "http://neurobagel.org/vocab/test-001",
                "image_modal": "http://purl.org/nidash/nidm#FlowWeighted",
                "pipeline_name": "https://github.com/nipoppy/pipeline-catalog/tree/main/processing/fmriprep",
                "pipeline_version": "23.2.0",
            },
            {
                "dataset_uuid": "http://neurobagel.org/vocab/test-001",
                "image_modal": "http://purl.org/nidash/nidm#FlowWeighted",
                "pipeline_name": "https://github.com/nipoppy/pipeline-catalog/tree/main/processing/mriqc",
                "pipeline_version": "22.0.6",
            },
            {
                "dataset_uuid": "http://neurobagel.org/vocab/test-002",
                "image_modal": "http://purl.org/nidash/nidm#T1Weighted",
                "pipeline_name": "https://github.com/nipoppy/pipeline-catalog/tree/main/processing/freesurfer",
                "pipeline_version": "6.0.1",
            },
            {
                "dataset_uuid": "http://neurobagel.org/vocab/test-002",
                "image_modal": "http://purl.org/nidash/nidm#T1Weighted",
                "pipeline_name": "https://github.com/nipoppy/pipeline-catalog/tree/main/processing/freesurfer",
                "pipeline_version": "7.3.2",
            },
            {
                "dataset_uuid": "http://neurobagel.org/vocab/test-002",
                "image_modal": "http://purl.org/nidash/nidm#FlowWeighted",
            },
            {
                "dataset_uuid": "http://neurobagel.org/vocab/test-003",
                "image_modal": "http://purl.org/nidash/nidm#T1Weighted",
            },
            {
                "dataset_uuid": "http://neurobagel.org/vocab/test-003",
                "image_modal": "http://purl.org/nidash/nidm#FlowWeighted",
            },
        ]

    expected_image_modals_and_pipelines = {
        "http://neurobagel.org/vocab/test-001": {
            "image_modals": [
                "http://purl.org/nidash/nidm#T1Weighted",
                "http://purl.org/nidash/nidm#FlowWeighted",
            ],
            "available_pipelines": {
                "https://github.com/nipoppy/pipeline-catalog/tree/main/processing/fmriprep": [
                    "23.2.0"
                ],
                "https://github.com/nipoppy/pipeline-catalog/tree/main/processing/mriqc": [
                    "22.0.6"
                ],
            },
        },
        "http://neurobagel.org/vocab/test-002": {
            "image_modals": [
                "http://purl.org/nidash/nidm#T1Weighted",
                "http://purl.org/nidash/nidm#FlowWeighted",
            ],
            "available_pipelines": {
                "https://github.com/nipoppy/pipeline-catalog/tree/main/processing/freesurfer": [
                    "6.0.1",
                    "7.3.2",
                ]
            },
        },
        "http://neurobagel.org/vocab/test-003": {
            "image_modals": [
                "http://purl.org/nidash/nidm#T1Weighted",
                "http://purl.org/nidash/nidm#FlowWeighted",
            ],
            "available_pipelines": {},
        },
    }

    # Act
    monkeypatch.setattr(crud, "post_query_to_graph", mock_post_query_to_graph)
    image_modals_and_pipelines = (
        await crud.query_available_modalities_and_pipelines(
            dataset_uuids=matching_dataset_uuids
        )
    )

    # Assert
    assert image_modals_and_pipelines == expected_image_modals_and_pipelines
