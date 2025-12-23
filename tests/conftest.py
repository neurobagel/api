import pytest
from starlette.testclient import TestClient

from app.api import env_settings
from app.main import app, settings


@pytest.fixture(scope="module")
def test_app():
    client = TestClient(app)
    yield client


@pytest.fixture
def enable_auth(monkeypatch):
    """Enable the authentication requirement for the API."""
    monkeypatch.setattr(settings, "auth_enabled", True)


@pytest.fixture
def disable_auth(monkeypatch):
    """
    Disable the authentication requirement for the API to skip startup checks
    (for when the tested route does not require authentication).
    """
    monkeypatch.setattr(settings, "auth_enabled", False)


@pytest.fixture()
def mock_verify_token():
    """Mock a successful token verification that does not raise any exceptions."""

    def _verify_token(token):
        return None

    return _verify_token


@pytest.fixture()
def set_mock_verify_token(monkeypatch, mock_verify_token):
    """Set the verify_token function to a mock that does not raise any exceptions."""
    monkeypatch.setattr(
        "app.api.routers.query.verify_token", mock_verify_token
    )


@pytest.fixture()
def mock_auth_header() -> dict:
    """Create an authorization header with a mock token that is well-formed for testing purposes."""
    return {"Authorization": "Bearer foo"}


@pytest.fixture()
def set_graph_url_vars_for_integration_tests(monkeypatch):
    """
    Set the graph URL to the default value for integration tests.

    NOTE: These should correspond to the default configuration values, but are set explicitly here for clarity and
    to override any environment defined in pytest.ini.
    """
    monkeypatch.setattr(settings, "graph_address", "localhost")
    monkeypatch.setattr(settings, "graph_port", 7200)
    monkeypatch.setattr(settings, "graph_db", "repositories/my_db")


@pytest.fixture()
def mock_context(monkeypatch):
    """Create a mock context for testing to avoid unnecessary requests to GitHub for supported namespaces."""
    monkeypatch.setattr(
        env_settings,
        "CONTEXT",
        {
            "nb": "http://neurobagel.org/vocab/",
            "ncit": "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#",
            "nidm": "http://purl.org/nidash/nidm#",
            "snomed": "http://purl.bioontology.org/ontology/SNOMEDCT/",
            "np": "https://github.com/nipoppy/pipeline-catalog/tree/main/processing/",
        },
    )


@pytest.fixture()
def test_data():
    """Create valid aggregate response data for two toy datasets for testing."""
    return [
        {
            "dataset_uuid": "http://neurobagel.org/vocab/12345",
            "dataset_name": "QPN",
            "dataset_portal_uri": "https://rpq-qpn.ca/en/researchers-section/databases/",
            "dataset_total_subjects": 200,
            "num_matching_subjects": 5,
            "records_protected": True,
            "subject_data": "protected",
            "image_modals": [
                "http://purl.org/nidash/nidm#T1Weighted",
                "http://purl.org/nidash/nidm#T2Weighted",
            ],
            "available_pipelines": {
                "https://github.com/nipoppy/pipeline-catalog/tree/main/processing/freesurfer": [
                    "7.3.2",
                    "2.8.2",
                    "8.7.0-rc",
                ]
            },
        },
        {
            "dataset_uuid": "http://neurobagel.org/vocab/67890",
            "dataset_name": "PPMI",
            "dataset_portal_uri": "https://www.ppmi-info.org/access-data-specimens/download-data",
            "dataset_total_subjects": 3000,
            "num_matching_subjects": 3,
            "records_protected": True,
            "subject_data": "protected",
            "image_modals": [
                "http://purl.org/nidash/nidm#FlowWeighted",
                "http://purl.org/nidash/nidm#T1Weighted",
            ],
            "available_pipelines": {
                "https://github.com/nipoppy/pipeline-catalog/tree/main/processing/freesurfer": [
                    "7.3.2",
                    "2.1.2",
                ],
                "https://github.com/nipoppy/pipeline-catalog/tree/main/processing/fmriprep": [
                    "23.1.3",
                    "22.1.4",
                    "v2.0.1",
                ],
            },
        },
    ]


@pytest.fixture
def mock_post_agg_query_to_graph():
    """
    Mock post_query_to_graph function that returns toy AGGREGATED matching data containing:
    - a subject with phenotypic data only
    - a subject with phenotypic, raw imaging, and pipeline data
    """

    async def mockreturn(query, timeout=5.0):
        return [
            {
                "dataset_uuid": "http://neurobagel.org/vocab/12345",
                "dataset_portal_uri": "https://rpq-qpn.ca/en/researchers-section/databases/",
                "sub_id": "sub-ON95534",
                "dataset_name": "QPN",
            },
            {
                "dataset_uuid": "http://neurobagel.org/vocab/12345",
                "dataset_portal_uri": "https://rpq-qpn.ca/en/researchers-section/databases/",
                "sub_id": "sub-ON95535",
                "dataset_name": "QPN",
                "image_modal": "http://purl.org/nidash/nidm#T1Weighted",
                "pipeline_version": "7.3.2",
                "pipeline_name": "https://github.com/nipoppy/pipeline-catalog/tree/main/processing/freesurfer",
            },
        ]

    return mockreturn


# TODO: Update once /query endpoint is deprecated, after which we will no longer return
# dataset metadata from the graph for a cohort query
@pytest.fixture
def mock_post_nonagg_query_to_graph():
    """
    Mock post_query_to_graph function that returns toy NON-AGGREGATED matching data containing:
    - a dataset with 2 matching subjects, where each subject has 2 sessions
    - each session has both phenotypic data (note: several phenotypic variables are missing) and raw imaging data (T1Weighted, FlowWeighted)
    """

    async def mockreturn(query, timeout=5.0):
        return [
            {
                "dataset_uuid": "http://neurobagel.org/vocab/12345",
                "dataset_name": "BIDS synthetic",
                "sub_id": "sub-03",
                "age": "2.21E1",
                "num_matching_phenotypic_sessions": "2",
                "num_matching_imaging_sessions": "2",
                "session_id": "ses-01",
                "session_type": "http://neurobagel.org/vocab/PhenotypicSession",
            },
            {
                "dataset_uuid": "http://neurobagel.org/vocab/12345",
                "dataset_name": "BIDS synthetic",
                "sub_id": "sub-03",
                "age": "2.32E1",
                "num_matching_phenotypic_sessions": "2",
                "num_matching_imaging_sessions": "2",
                "session_id": "ses-02",
                "session_type": "http://neurobagel.org/vocab/PhenotypicSession",
            },
            {
                "dataset_uuid": "http://neurobagel.org/vocab/12345",
                "dataset_name": "BIDS synthetic",
                "sub_id": "sub-03",
                "num_matching_phenotypic_sessions": "2",
                "num_matching_imaging_sessions": "2",
                "session_id": "ses-01",
                "session_type": "http://neurobagel.org/vocab/ImagingSession",
                "image_modal": "http://purl.org/nidash/nidm#T1Weighted",
                "session_file_path": "/data/neurobagel/bagel-cli/bids-examples/synthetic/sub-03/ses-01",
            },
            {
                "dataset_uuid": "http://neurobagel.org/vocab/12345",
                "dataset_name": "BIDS synthetic",
                "sub_id": "sub-03",
                "num_matching_phenotypic_sessions": "2",
                "num_matching_imaging_sessions": "2",
                "session_id": "ses-01",
                "session_type": "http://neurobagel.org/vocab/ImagingSession",
                "image_modal": "http://purl.org/nidash/nidm#FlowWeighted",
                "session_file_path": "/data/neurobagel/bagel-cli/bids-examples/synthetic/sub-03/ses-01",
            },
            {
                "dataset_uuid": "http://neurobagel.org/vocab/12345",
                "dataset_name": "BIDS synthetic",
                "sub_id": "sub-03",
                "num_matching_phenotypic_sessions": "2",
                "num_matching_imaging_sessions": "2",
                "session_id": "ses-02",
                "session_type": "http://neurobagel.org/vocab/ImagingSession",
                "image_modal": "http://purl.org/nidash/nidm#T1Weighted",
                "session_file_path": "/data/neurobagel/bagel-cli/bids-examples/synthetic/sub-03/ses-02",
            },
            {
                "dataset_uuid": "http://neurobagel.org/vocab/12345",
                "dataset_name": "BIDS synthetic",
                "sub_id": "sub-03",
                "num_matching_phenotypic_sessions": "2",
                "num_matching_imaging_sessions": "2",
                "session_id": "ses-02",
                "session_type": "http://neurobagel.org/vocab/ImagingSession",
                "image_modal": "http://purl.org/nidash/nidm#FlowWeighted",
                "session_file_path": "/data/neurobagel/bagel-cli/bids-examples/synthetic/sub-03/ses-02",
            },
            {
                "dataset_uuid": "http://neurobagel.org/vocab/12345",
                "dataset_name": "BIDS synthetic",
                "sub_id": "sub-04",
                "age": "2.11E1",
                "sex": "http://purl.bioontology.org/ontology/SNOMEDCT/248152002",
                "num_matching_phenotypic_sessions": "2",
                "num_matching_imaging_sessions": "2",
                "session_id": "ses-01",
                "session_type": "http://neurobagel.org/vocab/PhenotypicSession",
            },
            {
                "dataset_uuid": "http://neurobagel.org/vocab/12345",
                "dataset_name": "BIDS synthetic",
                "sub_id": "sub-04",
                "age": "2.23E1",
                "sex": "http://purl.bioontology.org/ontology/SNOMEDCT/248152002",
                "num_matching_phenotypic_sessions": "2",
                "num_matching_imaging_sessions": "2",
                "session_id": "ses-02",
                "session_type": "http://neurobagel.org/vocab/PhenotypicSession",
            },
            {
                "dataset_uuid": "http://neurobagel.org/vocab/12345",
                "dataset_name": "BIDS synthetic",
                "sub_id": "sub-04",
                "num_matching_phenotypic_sessions": "2",
                "num_matching_imaging_sessions": "2",
                "session_id": "ses-01",
                "session_type": "http://neurobagel.org/vocab/ImagingSession",
                "image_modal": "http://purl.org/nidash/nidm#T1Weighted",
                "session_file_path": "/data/neurobagel/bagel-cli/bids-examples/synthetic/sub-04/ses-01",
            },
            {
                "dataset_uuid": "http://neurobagel.org/vocab/12345",
                "dataset_name": "BIDS synthetic",
                "sub_id": "sub-04",
                "num_matching_phenotypic_sessions": "2",
                "num_matching_imaging_sessions": "2",
                "session_id": "ses-01",
                "session_type": "http://neurobagel.org/vocab/ImagingSession",
                "image_modal": "http://purl.org/nidash/nidm#FlowWeighted",
                "session_file_path": "/data/neurobagel/bagel-cli/bids-examples/synthetic/sub-04/ses-01",
            },
            {
                "dataset_uuid": "http://neurobagel.org/vocab/12345",
                "dataset_name": "BIDS synthetic",
                "sub_id": "sub-04",
                "num_matching_phenotypic_sessions": "2",
                "num_matching_imaging_sessions": "2",
                "session_id": "ses-02",
                "session_type": "http://neurobagel.org/vocab/ImagingSession",
                "image_modal": "http://purl.org/nidash/nidm#T1Weighted",
                "session_file_path": "/data/neurobagel/bagel-cli/bids-examples/synthetic/sub-04/ses-02",
            },
            {
                "dataset_uuid": "http://neurobagel.org/vocab/12345",
                "dataset_name": "BIDS synthetic",
                "sub_id": "sub-04",
                "num_matching_phenotypic_sessions": "2",
                "num_matching_imaging_sessions": "2",
                "session_id": "ses-02",
                "session_type": "http://neurobagel.org/vocab/ImagingSession",
                "image_modal": "http://purl.org/nidash/nidm#FlowWeighted",
                "session_file_path": "/data/neurobagel/bagel-cli/bids-examples/synthetic/sub-04/ses-02",
            },
        ]

    return mockreturn


@pytest.fixture
def mock_query_matching_dataset_sizes():
    """
    Mock query_matching_dataset_sizes function that returns the total number of subjects for a toy dataset 12345.
    Can be used together with mock_post_*_query_to_graph fixtures to mock both the POST step of a cohort query and
    the corresponding query for dataset size, in order to test how the response from the graph is processed by the API (crud.query_records).
    """

    async def _mock_query_matching_dataset_sizes(**kwargs):
        return {"http://neurobagel.org/vocab/12345": 200}

    return _mock_query_matching_dataset_sizes


# TODO: Consider renaming fixture once /query endpoint is removed
@pytest.fixture
def mock_get_with_exception(request):
    """
    Mock get function that raises a specified exception.

    A parameter passed to this fixture via indirect parametrization is received by the internal factory function before it is passed to a test.

    Example usage in test function:
        @pytest.mark.parametrize("mock_get_with_exception", [HTTPException(500)], indirect=True)
        (this tells mock_get_with_exception to raise an HTTPException)
    """

    async def _mock_get_with_exception(**kwargs):
        raise request.param

    return _mock_get_with_exception


@pytest.fixture
def mock_query_records(request):
    """
    Mock get function that returns an arbitrary response or value (can be None). Can be used to testing error handling of bad requests.

    A parameter passed to this fixture via indirect parametrization is received by the internal factory function before it is passed to a test.

    Example usage in test function:
        @pytest.mark.parametrize("mock_query_records", [None], indirect=True)
        (this tells mock_query_records to return None)

    TODO: Currently also used to test error handling for POST /subjects. Consider renaming once the /query endpoint is deprecated.
    """

    async def _mock_query_records(**kwargs):
        return request.param

    return _mock_query_records


@pytest.fixture
def mock_successful_query_records(test_data):
    """Mock CRUD function that returns non-empty, valid aggregate query result data for /query endpoint."""

    async def _mock_successful_query_records(**kwargs):
        return test_data

    return _mock_successful_query_records


@pytest.fixture
def mock_successful_post_subjects(test_data):
    """Mock CRUD function that returns non-empty, valid aggregate query result data for /subjects endpoint."""

    async def _mock_successful_post_subjects(query):
        return [
            {
                "dataset_uuid": "http://neurobagel.org/vocab/12345",
                "subject_data": "protected",
            },
            {
                "dataset_uuid": "http://neurobagel.org/vocab/67890",
                "subject_data": "protected",
            },
        ]

    return _mock_successful_post_subjects
