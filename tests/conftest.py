import pytest
from starlette.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def test_app():
    client = TestClient(app)
    yield client


@pytest.fixture()
def query_test_data():
    """Create toy data for two datasets for testing."""
    return [
        {
            "dataset_uuid": "http://neurobagel.org/vocab/12345",
            "dataset_name": "QPN",
            "dataset_portal_uri": "https://rpq-qpn.ca/en/researchers-section/databases/",
            "num_matching_subjects": 5,
            "subject_data": [
                "/my/happy/path/sub-0051/to/session-01",
                "/my/happy/path/sub-0653/to/session-01",
                "/my/happy/path/sub-1063/to/session-01",
                "/my/happy/path/sub-1113/to/session-01",
                "/my/happy/path/sub-1170/to/session-01",
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
            "subject_data": [
                "/my/happy/path/sub-719238/to/session-01",
                "/my/happy/path/sub-719341/to/session-01",
                "/my/happy/path/sub-719369/to/session-01",
                "/my/happy/path/sub-719238/to/session-02",
                "/my/happy/path/sub-719341/to/session-02",
            ],
            "image_modals": [
                "http://purl.org/nidash/nidm#FlowWeighted",
                "http://purl.org/nidash/nidm#T1Weighted",
            ],
        },
    ]


@pytest.fixture
def mock_successful_get_query(query_test_data):
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
        return query_test_data

    return mockreturn


@pytest.fixture
def mock_invalid_get_query():
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
