import pytest
from starlette.testclient import TestClient

from app.api import utility as util
from app.main import app


@pytest.fixture(scope="module")
def test_app():
    client = TestClient(app)
    yield client


@pytest.fixture
def enable_auth(monkeypatch):
    """Enable the authentication requirement for the API."""
    monkeypatch.setattr("app.api.security.AUTH_ENABLED", True)


@pytest.fixture
def disable_auth(monkeypatch):
    """
    Disable the authentication requirement for the API to skip startup checks
    (for when the tested route does not require authentication).
    """
    monkeypatch.setattr("app.api.security.AUTH_ENABLED", False)


@pytest.fixture(scope="function")
def set_test_credentials(monkeypatch):
    """Set random username and password to avoid error from startup check for set credentials."""
    monkeypatch.setenv(util.GRAPH_USERNAME.name, "DBUSER")
    monkeypatch.setenv(util.GRAPH_PASSWORD.name, "DBPASSWORD")


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

    def mockreturn(query, timeout=5.0):
        return {
            "head": {
                "vars": [
                    "dataset_uuid",
                    "dataset_name",
                    "dataset_portal_uri",
                    "sub_id",
                    "image_modal",
                    "pipeline_name",
                    "pipeline_version",
                ]
            },
            "results": {
                "bindings": [
                    {
                        "dataset_uuid": {
                            "type": "uri",
                            "value": "http://neurobagel.org/vocab/12345",
                        },
                        "dataset_portal_uri": {
                            "type": "literal",
                            "value": "https://rpq-qpn.ca/en/researchers-section/databases/",
                        },
                        "sub_id": {"type": "literal", "value": "sub-ON95534"},
                        "dataset_name": {"type": "literal", "value": "QPN"},
                    },
                    {
                        "dataset_uuid": {
                            "type": "uri",
                            "value": "http://neurobagel.org/vocab/12345",
                        },
                        "dataset_portal_uri": {
                            "type": "literal",
                            "value": "https://rpq-qpn.ca/en/researchers-section/databases/",
                        },
                        "sub_id": {"type": "literal", "value": "sub-ON95535"},
                        "dataset_name": {"type": "literal", "value": "QPN"},
                        "image_modal": {
                            "type": "uri",
                            "value": "http://purl.org/nidash/nidm#T1Weighted",
                        },
                        "pipeline_version": {
                            "type": "literal",
                            "value": "7.3.2",
                        },
                        "pipeline_name": {
                            "type": "uri",
                            "value": "https://github.com/nipoppy/pipeline-catalog/tree/main/processing/freesurfer",
                        },
                    },
                ]
            },
        }

    return mockreturn


@pytest.fixture
def mock_post_nonagg_query_to_graph():
    """
    Mock post_query_to_graph function that returns toy NON-AGGREGATED matching data containing:
    - a dataset with 2 matching subjects, with phenotypic data and raw imaging data only (note: several phenotypic variables are missing)
    """

    def mockreturn(query, timeout=5.0):
        return {
            "head": {
                "vars": [
                    "dataset_uuid",
                    "dataset_name",
                    "dataset_portal_uri",
                    "sub_id",
                    "age",
                    "sex",
                    "diagnosis",
                    "subject_group",
                    "num_matching_phenotypic_sessions",
                    "num_matching_imaging_sessions",
                    "session_id",
                    "session_type",
                    "assessment",
                    "image_modal",
                    "session_file_path",
                    "pipeline_name",
                    "pipeline_version",
                ]
            },
            "results": {
                "bindings": [
                    {
                        "dataset_uuid": {
                            "type": "uri",
                            "value": "http://neurobagel.org/vocab/12345",
                        },
                        "dataset_name": {
                            "type": "literal",
                            "value": "BIDS synthetic",
                        },
                        "sub_id": {"type": "literal", "value": "sub-03"},
                        "age": {
                            "datatype": "http://www.w3.org/2001/XMLSchema#double",
                            "type": "literal",
                            "value": "2.21E1",
                        },
                        "num_matching_phenotypic_sessions": {
                            "datatype": "http://www.w3.org/2001/XMLSchema#integer",
                            "type": "literal",
                            "value": "2",
                        },
                        "num_matching_imaging_sessions": {
                            "datatype": "http://www.w3.org/2001/XMLSchema#integer",
                            "type": "literal",
                            "value": "2",
                        },
                        "session_id": {"type": "literal", "value": "ses-01"},
                        "session_type": {
                            "type": "uri",
                            "value": "http://neurobagel.org/vocab/PhenotypicSession",
                        },
                    },
                    {
                        "dataset_uuid": {
                            "type": "uri",
                            "value": "http://neurobagel.org/vocab/12345",
                        },
                        "dataset_name": {
                            "type": "literal",
                            "value": "BIDS synthetic",
                        },
                        "sub_id": {"type": "literal", "value": "sub-03"},
                        "age": {
                            "datatype": "http://www.w3.org/2001/XMLSchema#double",
                            "type": "literal",
                            "value": "2.32E1",
                        },
                        "num_matching_phenotypic_sessions": {
                            "datatype": "http://www.w3.org/2001/XMLSchema#integer",
                            "type": "literal",
                            "value": "2",
                        },
                        "num_matching_imaging_sessions": {
                            "datatype": "http://www.w3.org/2001/XMLSchema#integer",
                            "type": "literal",
                            "value": "2",
                        },
                        "session_id": {"type": "literal", "value": "ses-02"},
                        "session_type": {
                            "type": "uri",
                            "value": "http://neurobagel.org/vocab/PhenotypicSession",
                        },
                    },
                    {
                        "dataset_uuid": {
                            "type": "uri",
                            "value": "http://neurobagel.org/vocab/12345",
                        },
                        "dataset_name": {
                            "type": "literal",
                            "value": "BIDS synthetic",
                        },
                        "sub_id": {"type": "literal", "value": "sub-03"},
                        "age": {
                            "datatype": "http://www.w3.org/2001/XMLSchema#double",
                            "type": "literal",
                            "value": "2.32E1",
                        },
                        "num_matching_phenotypic_sessions": {
                            "datatype": "http://www.w3.org/2001/XMLSchema#integer",
                            "type": "literal",
                            "value": "2",
                        },
                        "num_matching_imaging_sessions": {
                            "datatype": "http://www.w3.org/2001/XMLSchema#integer",
                            "type": "literal",
                            "value": "2",
                        },
                        "session_id": {"type": "literal", "value": "ses-02"},
                        "session_type": {
                            "type": "uri",
                            "value": "http://neurobagel.org/vocab/PhenotypicSession",
                        },
                    },
                    {
                        "dataset_uuid": {
                            "type": "uri",
                            "value": "http://neurobagel.org/vocab/12345",
                        },
                        "dataset_name": {
                            "type": "literal",
                            "value": "BIDS synthetic",
                        },
                        "sub_id": {"type": "literal", "value": "sub-03"},
                        "num_matching_phenotypic_sessions": {
                            "datatype": "http://www.w3.org/2001/XMLSchema#integer",
                            "type": "literal",
                            "value": "2",
                        },
                        "num_matching_imaging_sessions": {
                            "datatype": "http://www.w3.org/2001/XMLSchema#integer",
                            "type": "literal",
                            "value": "2",
                        },
                        "session_id": {"type": "literal", "value": "ses-01"},
                        "session_type": {
                            "type": "uri",
                            "value": "http://neurobagel.org/vocab/ImagingSession",
                        },
                        "image_modal": {
                            "type": "uri",
                            "value": "http://purl.org/nidash/nidm#T1Weighted",
                        },
                        "session_file_path": {
                            "type": "literal",
                            "value": "/data/neurobagel/bagel-cli/bids-examples/synthetic/sub-03/ses-01",
                        },
                    },
                    {
                        "dataset_uuid": {
                            "type": "uri",
                            "value": "http://neurobagel.org/vocab/12345",
                        },
                        "dataset_name": {
                            "type": "literal",
                            "value": "BIDS synthetic",
                        },
                        "sub_id": {"type": "literal", "value": "sub-03"},
                        "num_matching_phenotypic_sessions": {
                            "datatype": "http://www.w3.org/2001/XMLSchema#integer",
                            "type": "literal",
                            "value": "2",
                        },
                        "num_matching_imaging_sessions": {
                            "datatype": "http://www.w3.org/2001/XMLSchema#integer",
                            "type": "literal",
                            "value": "2",
                        },
                        "session_id": {"type": "literal", "value": "ses-01"},
                        "session_type": {
                            "type": "uri",
                            "value": "http://neurobagel.org/vocab/ImagingSession",
                        },
                        "image_modal": {
                            "type": "uri",
                            "value": "http://purl.org/nidash/nidm#FlowWeighted",
                        },
                        "session_file_path": {
                            "type": "literal",
                            "value": "/data/neurobagel/bagel-cli/bids-examples/synthetic/sub-03/ses-01",
                        },
                    },
                    {
                        "dataset_uuid": {
                            "type": "uri",
                            "value": "http://neurobagel.org/vocab/12345",
                        },
                        "dataset_name": {
                            "type": "literal",
                            "value": "BIDS synthetic",
                        },
                        "sub_id": {"type": "literal", "value": "sub-03"},
                        "num_matching_phenotypic_sessions": {
                            "datatype": "http://www.w3.org/2001/XMLSchema#integer",
                            "type": "literal",
                            "value": "2",
                        },
                        "num_matching_imaging_sessions": {
                            "datatype": "http://www.w3.org/2001/XMLSchema#integer",
                            "type": "literal",
                            "value": "2",
                        },
                        "session_id": {"type": "literal", "value": "ses-02"},
                        "session_type": {
                            "type": "uri",
                            "value": "http://neurobagel.org/vocab/ImagingSession",
                        },
                        "image_modal": {
                            "type": "uri",
                            "value": "http://purl.org/nidash/nidm#T1Weighted",
                        },
                        "session_file_path": {
                            "type": "literal",
                            "value": "/data/neurobagel/bagel-cli/bids-examples/synthetic/sub-03/ses-02",
                        },
                    },
                    {
                        "dataset_uuid": {
                            "type": "uri",
                            "value": "http://neurobagel.org/vocab/12345",
                        },
                        "dataset_name": {
                            "type": "literal",
                            "value": "BIDS synthetic",
                        },
                        "sub_id": {"type": "literal", "value": "sub-03"},
                        "num_matching_phenotypic_sessions": {
                            "datatype": "http://www.w3.org/2001/XMLSchema#integer",
                            "type": "literal",
                            "value": "2",
                        },
                        "num_matching_imaging_sessions": {
                            "datatype": "http://www.w3.org/2001/XMLSchema#integer",
                            "type": "literal",
                            "value": "2",
                        },
                        "session_id": {"type": "literal", "value": "ses-02"},
                        "session_type": {
                            "type": "uri",
                            "value": "http://neurobagel.org/vocab/ImagingSession",
                        },
                        "image_modal": {
                            "type": "uri",
                            "value": "http://purl.org/nidash/nidm#FlowWeighted",
                        },
                        "session_file_path": {
                            "type": "literal",
                            "value": "/data/neurobagel/bagel-cli/bids-examples/synthetic/sub-03/ses-02",
                        },
                    },
                    {
                        "dataset_uuid": {
                            "type": "uri",
                            "value": "http://neurobagel.org/vocab/12345",
                        },
                        "dataset_name": {
                            "type": "literal",
                            "value": "BIDS synthetic",
                        },
                        "sub_id": {"type": "literal", "value": "sub-04"},
                        "age": {
                            "datatype": "http://www.w3.org/2001/XMLSchema#double",
                            "type": "literal",
                            "value": "2.11E1",
                        },
                        "sex": {
                            "type": "uri",
                            "value": "http://purl.bioontology.org/ontology/SNOMEDCT/248152002",
                        },
                        "num_matching_phenotypic_sessions": {
                            "datatype": "http://www.w3.org/2001/XMLSchema#integer",
                            "type": "literal",
                            "value": "2",
                        },
                        "num_matching_imaging_sessions": {
                            "datatype": "http://www.w3.org/2001/XMLSchema#integer",
                            "type": "literal",
                            "value": "2",
                        },
                        "session_id": {"type": "literal", "value": "ses-01"},
                        "session_type": {
                            "type": "uri",
                            "value": "http://neurobagel.org/vocab/PhenotypicSession",
                        },
                    },
                    {
                        "dataset_uuid": {
                            "type": "uri",
                            "value": "http://neurobagel.org/vocab/12345",
                        },
                        "dataset_name": {
                            "type": "literal",
                            "value": "BIDS synthetic",
                        },
                        "sub_id": {"type": "literal", "value": "sub-04"},
                        "age": {
                            "datatype": "http://www.w3.org/2001/XMLSchema#double",
                            "type": "literal",
                            "value": "2.23E1",
                        },
                        "sex": {
                            "type": "uri",
                            "value": "http://purl.bioontology.org/ontology/SNOMEDCT/248152002",
                        },
                        "num_matching_phenotypic_sessions": {
                            "datatype": "http://www.w3.org/2001/XMLSchema#integer",
                            "type": "literal",
                            "value": "2",
                        },
                        "num_matching_imaging_sessions": {
                            "datatype": "http://www.w3.org/2001/XMLSchema#integer",
                            "type": "literal",
                            "value": "2",
                        },
                        "session_id": {"type": "literal", "value": "ses-02"},
                        "session_type": {
                            "type": "uri",
                            "value": "http://neurobagel.org/vocab/PhenotypicSession",
                        },
                    },
                    {
                        "dataset_uuid": {
                            "type": "uri",
                            "value": "http://neurobagel.org/vocab/12345",
                        },
                        "dataset_name": {
                            "type": "literal",
                            "value": "BIDS synthetic",
                        },
                        "sub_id": {"type": "literal", "value": "sub-04"},
                        "age": {
                            "datatype": "http://www.w3.org/2001/XMLSchema#double",
                            "type": "literal",
                            "value": "2.23E1",
                        },
                        "sex": {
                            "type": "uri",
                            "value": "http://purl.bioontology.org/ontology/SNOMEDCT/248152002",
                        },
                        "num_matching_phenotypic_sessions": {
                            "datatype": "http://www.w3.org/2001/XMLSchema#integer",
                            "type": "literal",
                            "value": "2",
                        },
                        "num_matching_imaging_sessions": {
                            "datatype": "http://www.w3.org/2001/XMLSchema#integer",
                            "type": "literal",
                            "value": "2",
                        },
                        "session_id": {"type": "literal", "value": "ses-02"},
                        "session_type": {
                            "type": "uri",
                            "value": "http://neurobagel.org/vocab/PhenotypicSession",
                        },
                    },
                    {
                        "dataset_uuid": {
                            "type": "uri",
                            "value": "http://neurobagel.org/vocab/12345",
                        },
                        "dataset_name": {
                            "type": "literal",
                            "value": "BIDS synthetic",
                        },
                        "sub_id": {"type": "literal", "value": "sub-04"},
                        "num_matching_phenotypic_sessions": {
                            "datatype": "http://www.w3.org/2001/XMLSchema#integer",
                            "type": "literal",
                            "value": "2",
                        },
                        "num_matching_imaging_sessions": {
                            "datatype": "http://www.w3.org/2001/XMLSchema#integer",
                            "type": "literal",
                            "value": "2",
                        },
                        "session_id": {"type": "literal", "value": "ses-01"},
                        "session_type": {
                            "type": "uri",
                            "value": "http://neurobagel.org/vocab/ImagingSession",
                        },
                        "image_modal": {
                            "type": "uri",
                            "value": "http://purl.org/nidash/nidm#T1Weighted",
                        },
                        "session_file_path": {
                            "type": "literal",
                            "value": "/data/neurobagel/bagel-cli/bids-examples/synthetic/sub-04/ses-01",
                        },
                    },
                    {
                        "dataset_uuid": {
                            "type": "uri",
                            "value": "http://neurobagel.org/vocab/12345",
                        },
                        "dataset_name": {
                            "type": "literal",
                            "value": "BIDS synthetic",
                        },
                        "sub_id": {"type": "literal", "value": "sub-04"},
                        "num_matching_phenotypic_sessions": {
                            "datatype": "http://www.w3.org/2001/XMLSchema#integer",
                            "type": "literal",
                            "value": "2",
                        },
                        "num_matching_imaging_sessions": {
                            "datatype": "http://www.w3.org/2001/XMLSchema#integer",
                            "type": "literal",
                            "value": "2",
                        },
                        "session_id": {"type": "literal", "value": "ses-01"},
                        "session_type": {
                            "type": "uri",
                            "value": "http://neurobagel.org/vocab/ImagingSession",
                        },
                        "image_modal": {
                            "type": "uri",
                            "value": "http://purl.org/nidash/nidm#FlowWeighted",
                        },
                        "session_file_path": {
                            "type": "literal",
                            "value": "/data/neurobagel/bagel-cli/bids-examples/synthetic/sub-04/ses-01",
                        },
                    },
                    {
                        "dataset_uuid": {
                            "type": "uri",
                            "value": "http://neurobagel.org/vocab/12345",
                        },
                        "dataset_name": {
                            "type": "literal",
                            "value": "BIDS synthetic",
                        },
                        "sub_id": {"type": "literal", "value": "sub-04"},
                        "num_matching_phenotypic_sessions": {
                            "datatype": "http://www.w3.org/2001/XMLSchema#integer",
                            "type": "literal",
                            "value": "2",
                        },
                        "num_matching_imaging_sessions": {
                            "datatype": "http://www.w3.org/2001/XMLSchema#integer",
                            "type": "literal",
                            "value": "2",
                        },
                        "session_id": {"type": "literal", "value": "ses-02"},
                        "session_type": {
                            "type": "uri",
                            "value": "http://neurobagel.org/vocab/ImagingSession",
                        },
                        "image_modal": {
                            "type": "uri",
                            "value": "http://purl.org/nidash/nidm#T1Weighted",
                        },
                        "session_file_path": {
                            "type": "literal",
                            "value": "/data/neurobagel/bagel-cli/bids-examples/synthetic/sub-04/ses-02",
                        },
                    },
                    {
                        "dataset_uuid": {
                            "type": "uri",
                            "value": "http://neurobagel.org/vocab/12345",
                        },
                        "dataset_name": {
                            "type": "literal",
                            "value": "BIDS synthetic",
                        },
                        "sub_id": {"type": "literal", "value": "sub-04"},
                        "num_matching_phenotypic_sessions": {
                            "datatype": "http://www.w3.org/2001/XMLSchema#integer",
                            "type": "literal",
                            "value": "2",
                        },
                        "num_matching_imaging_sessions": {
                            "datatype": "http://www.w3.org/2001/XMLSchema#integer",
                            "type": "literal",
                            "value": "2",
                        },
                        "session_id": {"type": "literal", "value": "ses-02"},
                        "session_type": {
                            "type": "uri",
                            "value": "http://neurobagel.org/vocab/ImagingSession",
                        },
                        "image_modal": {
                            "type": "uri",
                            "value": "http://purl.org/nidash/nidm#FlowWeighted",
                        },
                        "session_file_path": {
                            "type": "literal",
                            "value": "/data/neurobagel/bagel-cli/bids-examples/synthetic/sub-04/ses-02",
                        },
                    },
                ]
            },
        }

    return mockreturn


@pytest.fixture
def mock_query_matching_dataset_sizes():
    """
    Mock query_matching_dataset_sizes function that returns the total number of subjects for a toy dataset 12345.
    Can be used together with mock_post_*_query_to_graph fixtures to mock both the POST step of a cohort query and
    the corresponding query for dataset size, in order to test how the response from the graph is processed by the API (crud.get).
    """

    def _mock_query_matching_dataset_sizes(dataset_uuids):
        return {"http://neurobagel.org/vocab/12345": 200}

    return _mock_query_matching_dataset_sizes


@pytest.fixture
def mock_get_with_exception(request):
    """
    Mock get function that raises a specified exception.

    A parameter passed to this fixture via indirect parametrization is received by the internal factory function before it is passed to a test.

    Example usage in test function:
        @pytest.mark.parametrize("mock_get_with_exception", [HTTPException(500)], indirect=True)
        (this tells mock_get_with_exception to raise an HTTPException)
    """

    async def _mock_get_with_exception(
        min_age,
        max_age,
        sex,
        diagnosis,
        is_control,
        min_num_imaging_sessions,
        min_num_phenotypic_sessions,
        assessment,
        image_modal,
        pipeline_version,
        pipeline_name,
    ):
        raise request.param

    return _mock_get_with_exception


@pytest.fixture
def mock_get(request):
    """
    Mock get function that returns an arbitrary response or value (can be None). Can be used to testing error handling of bad requests.

    A parameter passed to this fixture via indirect parametrization is received by the internal factory function before it is passed to a test.

    Example usage in test function:
        @pytest.mark.parametrize("mock_get", [None], indirect=True)
        (this tells mock_get to return None)
    """

    async def _mock_get(
        min_age,
        max_age,
        sex,
        diagnosis,
        is_control,
        min_num_imaging_sessions,
        min_num_phenotypic_sessions,
        assessment,
        image_modal,
        pipeline_version,
        pipeline_name,
    ):
        return request.param

    return _mock_get


@pytest.fixture
def mock_successful_get(test_data):
    """Mock get function that returns non-empty, valid aggregate query result data."""

    async def _mock_successful_get(
        min_age,
        max_age,
        sex,
        diagnosis,
        is_control,
        min_num_imaging_sessions,
        min_num_phenotypic_sessions,
        assessment,
        image_modal,
        pipeline_version,
        pipeline_name,
    ):
        return test_data

    return _mock_successful_get
