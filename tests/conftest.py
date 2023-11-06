import pytest
from starlette.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def test_app():
    client = TestClient(app)
    yield client


@pytest.fixture()
def test_data():
    """Create valid aggregate response data for two toy datasets for testing."""
    return [
        {
            "dataset_uuid": "http://neurobagel.org/vocab/12345",
            "dataset_name": "QPN",
            "dataset_portal_uri": "https://rpq-qpn.ca/en/researchers-section/databases/",
            "num_matching_subjects": 5,
            "records_protected": True,
            "subject_data": [
                {"session_file_path": "/my/happy/path/sub-0051/to/session-01"},
                {"session_file_path": "/my/happy/path/sub-0653/to/session-01"},
                {"session_file_path": "/my/happy/path/sub-1063/to/session-01"},
                {"session_file_path": "/my/happy/path/sub-1113/to/session-01"},
                {"session_file_path": "/my/happy/path/sub-1170/to/session-01"},
            ],
            "image_modals": [
                "http://purl.org/nidash/nidm#T1Weighted",
                "http://purl.org/nidash/nidm#T2Weighted",
            ],
        },
        {
            "dataset_uuid": "http://neurobagel.org/vocab/67890",
            "dataset_name": "PPMI",
            "dataset_portal_uri": "https://www.ppmi-info.org/access-data-specimens/download-data",
            "num_matching_subjects": 3,
            "records_protected": True,
            "subject_data": [
                {
                    "session_file_path": "/my/happy/path/sub-719238/to/session-01"
                },
                {
                    "session_file_path": "/my/happy/path/sub-719341/to/session-01"
                },
                {
                    "session_file_path": "/my/happy/path/sub-719369/to/session-01"
                },
                {
                    "session_file_path": "/my/happy/path/sub-719238/to/session-02"
                },
                {
                    "session_file_path": "/my/happy/path/sub-719341/to/session-02"
                },
            ],
            "image_modals": [
                "http://purl.org/nidash/nidm#FlowWeighted",
                "http://purl.org/nidash/nidm#T1Weighted",
            ],
        },
    ]


@pytest.fixture
def mock_successful_get(test_data):
    """Mock get function that returns non-empty query results."""

    async def mockreturn(
        min_age,
        max_age,
        sex,
        diagnosis,
        is_control,
        min_num_sessions,
        assessment,
        image_modal,
    ):
        return test_data

    return mockreturn


@pytest.fixture
def mock_invalid_get():
    """Mock get function that does not return any response (for testing invalid parameter values)."""

    async def mockreturn(
        min_age,
        max_age,
        sex,
        diagnosis,
        is_control,
        min_num_sessions,
        assessment,
        image_modal,
    ):
        return None

    return mockreturn


@pytest.fixture()
def terms_test_data():
    """Create toy data for terms for testing."""
    return {
        "nb:NeurobagelClass": [
            "nb:term1",
            "nb:term2",
            "nb:term3",
            "nb:term4",
            "nb:term5",
        ]
    }


@pytest.fixture
def mock_successful_get_terms(terms_test_data):
    """Mock get_terms function that returns non-empty results."""

    async def mockreturn(data_element_URI):
        return terms_test_data

    return mockreturn
