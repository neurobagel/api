import pytest
from starlette.testclient import TestClient

from app.api import utility as util
from app.main import app


@pytest.fixture(scope="module")
def test_app():
    client = TestClient(app)
    yield client


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
    monkeypatch.setenv(util.GRAPH_USERNAME.name, "SomeUser")
    monkeypatch.setenv(util.GRAPH_PASSWORD.name, "SomePassword")


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
        },
    ]


@pytest.fixture
def mock_post_query_to_graph():
    """Mock post_query_to_graph function that returns toy aggregate data containing a dataset with no modalities for testing."""

    def mockreturn(query, timeout=5.0):
        return {
            "head": {
                "vars": [
                    "dataset_uuid",
                    "dataset_name",
                    "dataset_portal_uri",
                    "sub_id",
                    "image_modal",
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
                    },
                ]
            },
        }

    return mockreturn


@pytest.fixture
def mock_query_matching_dataset_sizes():
    """
    Mock query_matching_dataset_sizes function that returns the total number of subjects for a toy dataset 12345.
    Can be used together with mock_post_query_to_graph to mock both the POST step of a cohort query and the corresponding query for dataset size,
    in order to test how the response from the graph is processed by the API (crud.get).
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
    ):
        return test_data

    return _mock_successful_get


@pytest.fixture()
def terms_test_data():
    """Create toy data for terms for testing."""
    return {
        "nb:NeurobagelClass": [
            {"TermURL": "cogatlas:123", "Label": "term 1"},
            {"TermURL": "cogatlas:234", "Label": "term 2"},
            {"TermURL": "cogatlas:345", "Label": "term 3"},
            {"TermURL": "cogatlas:456", "Label": "term 4"},
        ]
    }


@pytest.fixture
def mock_successful_get_terms(terms_test_data):
    """Mock get_terms function that returns non-empty results."""

    async def _mock_successful_get_terms(data_element_URI, term_labels_path):
        return terms_test_data

    return _mock_successful_get_terms
