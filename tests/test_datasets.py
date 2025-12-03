from app.api import crud

ROUTE = "/datasets"


def test_datasets_response_structure(
    test_app,
    mock_post_agg_query_to_graph,
    mock_query_matching_dataset_sizes,
    disable_auth,
    monkeypatch,
):
    """Test that the datasets endpoint does not include subject data in the response."""
    monkeypatch.setattr(
        crud, "post_query_to_graph", mock_post_agg_query_to_graph
    )
    monkeypatch.setattr(
        crud, "query_matching_dataset_sizes", mock_query_matching_dataset_sizes
    )

    response = test_app.post(ROUTE, json={})
    assert response.status_code == 200
    assert all(
        "subject_data" not in matching_dataset
        for matching_dataset in response.json()
    )


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
