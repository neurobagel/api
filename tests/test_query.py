"""Test API to query subjects from the graph database who match user-specified criteria."""

import pytest
from fastapi import HTTPException

import app.api.utility as util
from app.api import crud
from app.api.models import QueryModel

ROUTE = "/query"


def test_get_subjects_by_query(monkeypatch):
    """Test that graph results for dataset size queries are correctly parsed into a dictionary."""

    def mock_post_query_to_graph(query, timeout=5.0):
        return {
            "head": {"vars": ["dataset_uuid", "total_subjects"]},
            "results": {
                "bindings": [
                    {
                        "dataset_uuid": {
                            "type": "uri",
                            "value": "http://neurobagel.org/vocab/ds1234",
                        },
                        "total_subjects": {
                            "datatype": "http://www.w3.org/2001/XMLSchema#integer",
                            "type": "literal",
                            "value": "70",
                        },
                    },
                    {
                        "dataset_uuid": {
                            "type": "uri",
                            "value": "http://neurobagel.org/vocab/ds2345",
                        },
                        "total_subjects": {
                            "datatype": "http://www.w3.org/2001/XMLSchema#integer",
                            "type": "literal",
                            "value": "40",
                        },
                    },
                ]
            },
        }

    monkeypatch.setattr(crud, "post_query_to_graph", mock_post_query_to_graph)
    assert crud.query_matching_dataset_sizes(
        [
            "http://neurobagel.org/vocab/ds1234",
            "http://neurobagel.org/vocab/ds2345",
        ]
    ) == {
        "http://neurobagel.org/vocab/ds1234": 70,
        "http://neurobagel.org/vocab/ds2345": 40,
    }


def test_null_modalities(
    test_app,
    mock_post_agg_query_to_graph,
    mock_query_matching_dataset_sizes,
    monkeypatch,
    mock_auth_header,
    set_mock_verify_token,
):
    """Given a response containing a dataset with no recorded modalities, returns an empty list for the imaging modalities."""
    monkeypatch.setattr(
        util, "RETURN_AGG", util.EnvVar(util.RETURN_AGG.name, True)
    )
    monkeypatch.setattr(
        crud, "post_query_to_graph", mock_post_agg_query_to_graph
    )
    monkeypatch.setattr(
        crud, "query_matching_dataset_sizes", mock_query_matching_dataset_sizes
    )

    response = test_app.get(ROUTE, headers=mock_auth_header)
    assert response.json()[0]["image_modals"] == [
        "http://purl.org/nidash/nidm#T1Weighted"
    ]


def test_get_all(
    test_app,
    mock_successful_get,
    monkeypatch,
    mock_auth_header,
    set_mock_verify_token,
):
    """Given no input for any query parameters, returns a 200 status code and a non-empty list of results (should correspond to all subjects in graph)."""

    monkeypatch.setattr(crud, "get", mock_successful_get)
    response = test_app.get(ROUTE, headers=mock_auth_header)
    assert response.status_code == 200
    assert response.json() != []


@pytest.mark.parametrize(
    "valid_min_age, valid_max_age",
    [(30.5, 60), (23, 23)],
)
def test_get_valid_age_range(
    test_app,
    mock_successful_get,
    valid_min_age,
    valid_max_age,
    monkeypatch,
    mock_auth_header,
    set_mock_verify_token,
):
    """Given a valid age range, returns a 200 status code and a non-empty list of results."""

    monkeypatch.setattr(crud, "get", mock_successful_get)
    response = test_app.get(
        f"{ROUTE}?min_age={valid_min_age}&max_age={valid_max_age}",
        headers=mock_auth_header,
    )
    assert response.status_code == 200
    assert response.json() != []


@pytest.mark.parametrize(
    "age_keyval",
    ["min_age=20.75", "max_age=50"],
)
def test_get_valid_age_single_bound(
    test_app,
    mock_successful_get,
    age_keyval,
    monkeypatch,
    mock_auth_header,
    set_mock_verify_token,
):
    """Given only a valid lower/upper age bound, returns a 200 status code and a non-empty list of results."""

    monkeypatch.setattr(crud, "get", mock_successful_get)
    response = test_app.get(f"{ROUTE}?{age_keyval}", headers=mock_auth_header)
    assert response.status_code == 200
    assert response.json() != []


@pytest.mark.parametrize("mock_get", [None], indirect=True)
@pytest.mark.parametrize(
    "invalid_min_age, invalid_max_age",
    [
        ("forty", "fifty"),
        (33, 21),
        (-42.5, -40),
    ],
)
def test_get_invalid_age(
    test_app,
    mock_get,
    invalid_min_age,
    invalid_max_age,
    monkeypatch,
    mock_auth_header,
    set_mock_verify_token,
):
    """Given an invalid age range, returns a 422 status code."""

    monkeypatch.setattr(crud, "get", mock_get)
    response = test_app.get(
        f"{ROUTE}?min_age={invalid_min_age}&max_age={invalid_max_age}",
        headers=mock_auth_header,
    )
    assert response.status_code == 422


@pytest.mark.parametrize(
    "valid_sex",
    ["snomed:248153007", "snomed:248152002", "snomed:32570681000036106"],
)
def test_get_valid_sex(
    test_app,
    mock_successful_get,
    valid_sex,
    monkeypatch,
    mock_auth_header,
    set_mock_verify_token,
):
    """Given a valid sex string, returns a 200 status code and a non-empty list of results."""

    monkeypatch.setattr(crud, "get", mock_successful_get)
    response = test_app.get(
        f"{ROUTE}?sex={valid_sex}", headers=mock_auth_header
    )
    assert response.status_code == 200
    assert response.json() != []


@pytest.mark.parametrize("mock_get", [None], indirect=True)
def test_get_invalid_sex(
    test_app, mock_get, monkeypatch, mock_auth_header, set_mock_verify_token
):
    """Given an invalid sex string, returns a 422 status code."""

    monkeypatch.setattr(crud, "get", mock_get)
    response = test_app.get(f"{ROUTE}?sex=apple", headers=mock_auth_header)
    assert response.status_code == 422


@pytest.mark.parametrize(
    "valid_diagnosis", ["snomed:35489007", "snomed:49049000"]
)
def test_get_valid_diagnosis(
    test_app,
    mock_successful_get,
    valid_diagnosis,
    monkeypatch,
    mock_auth_header,
    set_mock_verify_token,
):
    """Given a valid diagnosis, returns a 200 status code and a non-empty list of results."""

    monkeypatch.setattr(crud, "get", mock_successful_get)
    response = test_app.get(
        f"{ROUTE}?diagnosis={valid_diagnosis}", headers=mock_auth_header
    )
    assert response.status_code == 200
    assert response.json() != []


@pytest.mark.parametrize("mock_get", [None], indirect=True)
@pytest.mark.parametrize(
    "invalid_diagnosis", ["sn0med:35489007", "apple", ":123456"]
)
def test_get_invalid_diagnosis(
    test_app,
    mock_get,
    invalid_diagnosis,
    monkeypatch,
    mock_auth_header,
    set_mock_verify_token,
):
    """Given an invalid diagnosis, returns a 422 status code."""

    monkeypatch.setattr(crud, "get", mock_get)
    response = test_app.get(
        f"{ROUTE}?diagnosis={invalid_diagnosis}", headers=mock_auth_header
    )
    assert response.status_code == 422


@pytest.mark.parametrize("valid_iscontrol", ["true", "True", "TRUE"])
def test_get_valid_iscontrol(
    test_app,
    mock_successful_get,
    valid_iscontrol,
    monkeypatch,
    mock_auth_header,
    set_mock_verify_token,
):
    """Given a valid is_control value, returns a 200 status code and a non-empty list of results."""

    monkeypatch.setattr(crud, "get", mock_successful_get)
    response = test_app.get(
        f"{ROUTE}?is_control={valid_iscontrol}", headers=mock_auth_header
    )
    assert response.status_code == 200
    assert response.json() != []


@pytest.mark.parametrize("valid_iscontrol", ["true", "True", "TRUE"])
def test_valid_iscontrol_parsed_as_bool(valid_iscontrol):
    """Test that valid is_control values do not produce a validation error and are parsed as booleans."""

    example_query = QueryModel(is_control=valid_iscontrol)
    assert example_query.is_control is True


@pytest.mark.parametrize("mock_get", [None], indirect=True)
@pytest.mark.parametrize("invalid_iscontrol", ["false", "FALSE", "all"])
def test_get_invalid_iscontrol(
    test_app,
    mock_get,
    monkeypatch,
    mock_auth_header,
    set_mock_verify_token,
    invalid_iscontrol,
):
    """Given an invalid is_control value, returns a 422 status code and informative error."""

    monkeypatch.setattr(crud, "get", mock_get)
    response = test_app.get(
        f"{ROUTE}?is_control={invalid_iscontrol}", headers=mock_auth_header
    )
    assert response.status_code == 422
    assert "must be either set to 'true' or omitted" in response.text


@pytest.mark.parametrize("mock_get", [None], indirect=True)
def test_get_invalid_control_diagnosis_pair(
    test_app, mock_get, monkeypatch, mock_auth_header, set_mock_verify_token
):
    """Given a non-default diagnosis value and is_control value of True, returns a 422 status code."""

    monkeypatch.setattr(crud, "get", mock_get)
    response = test_app.get(
        f"{ROUTE}?diagnosis=snomed:35489007&is_control=True",
        headers=mock_auth_header,
    )
    assert response.status_code == 422
    assert (
        "Subjects cannot both be healthy controls and have a diagnosis"
        in response.text
    )


# NOTE: Stacked parametrization is a feature of pytest: all combinations of the parameters are tested.
@pytest.mark.parametrize(
    "session_param",
    ["min_num_phenotypic_sessions", "min_num_imaging_sessions"],
)
@pytest.mark.parametrize("valid_min_num_sessions", [0, 1, 2, 4, 7])
def test_get_valid_min_num_sessions(
    test_app,
    mock_successful_get,
    session_param,
    valid_min_num_sessions,
    monkeypatch,
    mock_auth_header,
    set_mock_verify_token,
):
    """Given a valid minimum number of imaging sessions, returns a 200 status code and a non-empty list of results."""

    monkeypatch.setattr(crud, "get", mock_successful_get)
    response = test_app.get(
        f"{ROUTE}?{session_param}={valid_min_num_sessions}",
        headers=mock_auth_header,
    )
    assert response.status_code == 200
    assert response.json() != []


@pytest.mark.parametrize("mock_get", [None], indirect=True)
@pytest.mark.parametrize(
    "session_param",
    ["min_num_phenotypic_sessions", "min_num_imaging_sessions"],
)
@pytest.mark.parametrize("invalid_min_num_sessions", [-3, 2.5, "apple"])
def test_get_invalid_min_num_sessions(
    test_app,
    mock_get,
    session_param,
    invalid_min_num_sessions,
    monkeypatch,
    mock_auth_header,
    set_mock_verify_token,
):
    """Given an invalid minimum number of imaging sessions, returns a 422 status code."""

    monkeypatch.setattr(crud, "get", mock_get)
    response = test_app.get(
        f"{ROUTE}?{session_param}={invalid_min_num_sessions}",
        headers=mock_auth_header,
    )
    response.status_code = 422


def test_get_valid_assessment(
    test_app,
    mock_successful_get,
    monkeypatch,
    mock_auth_header,
    set_mock_verify_token,
):
    """Given a valid assessment, returns a 200 status code and a non-empty list of results."""

    monkeypatch.setattr(crud, "get", mock_successful_get)
    response = test_app.get(
        f"{ROUTE}?assessment=nb:cogAtlas-1234", headers=mock_auth_header
    )
    assert response.status_code == 200
    assert response.json() != []


@pytest.mark.parametrize("mock_get", [None], indirect=True)
@pytest.mark.parametrize(
    "invalid_assessment", ["bg01:cogAtlas-1234", "cogAtlas-1234"]
)
def test_get_invalid_assessment(
    test_app,
    mock_get,
    invalid_assessment,
    monkeypatch,
    mock_auth_header,
    set_mock_verify_token,
):
    """Given an invalid assessment, returns a 422 status code."""

    monkeypatch.setattr(crud, "get", mock_get)
    response = test_app.get(
        f"{ROUTE}?assessment={invalid_assessment}", headers=mock_auth_header
    )
    assert response.status_code == 422


@pytest.mark.parametrize(
    "valid_available_image_modal",
    [
        "nidm:DiffusionWeighted",
        "nidm:EEG",
        "nidm:FlowWeighted",
        "nidm:T1Weighted",
        "nidm:T2Weighted",
    ],
)
def test_get_valid_available_image_modal(
    test_app,
    mock_successful_get,
    valid_available_image_modal,
    monkeypatch,
    mock_auth_header,
    set_mock_verify_token,
):
    """Given a valid and available image modality, returns a 200 status code and a non-empty list of results."""

    monkeypatch.setattr(crud, "get", mock_successful_get)
    response = test_app.get(
        f"{ROUTE}?image_modal={valid_available_image_modal}",
        headers=mock_auth_header,
    )
    assert response.status_code == 200
    assert response.json() != []


@pytest.mark.parametrize("mock_get", [[]], indirect=True)
@pytest.mark.parametrize(
    "valid_unavailable_image_modal",
    ["nidm:Flair", "owl:sameAs", "nb:FlowWeighted", "snomed:something"],
)
def test_get_valid_unavailable_image_modal(
    test_app,
    valid_unavailable_image_modal,
    mock_get,
    monkeypatch,
    mock_auth_header,
    set_mock_verify_token,
):
    """Given a valid, pre-defined, and unavailable image modality, returns a 200 status code and an empty list of results."""

    monkeypatch.setattr(crud, "get", mock_get)
    response = test_app.get(
        f"{ROUTE}?image_modal={valid_unavailable_image_modal}",
        headers=mock_auth_header,
    )

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.parametrize("mock_get", [None], indirect=True)
@pytest.mark.parametrize(
    "invalid_image_modal", ["2nim:EEG", "apple", "some_thing:cool"]
)
def test_get_invalid_image_modal(
    test_app,
    mock_get,
    invalid_image_modal,
    monkeypatch,
    mock_auth_header,
    set_mock_verify_token,
):
    """Given an invalid image modality, returns a 422 status code."""

    monkeypatch.setattr(crud, "get", mock_get)
    response = test_app.get(
        f"{ROUTE}?image_modal={invalid_image_modal}", headers=mock_auth_header
    )
    assert response.status_code == 422


@pytest.mark.parametrize(
    "mock_get_with_exception", [HTTPException(500)], indirect=True
)
@pytest.mark.parametrize(
    "undefined_prefix_image_modal",
    ["dbo:abstract", "sex:apple", "something:cool"],
)
def test_get_undefined_prefix_image_modal(
    test_app,
    undefined_prefix_image_modal,
    mock_get_with_exception,
    monkeypatch,
    mock_auth_header,
    set_mock_verify_token,
):
    """Given a valid and undefined prefix image modality, returns a 500 status code."""

    monkeypatch.setattr(crud, "get", mock_get_with_exception)
    response = test_app.get(
        f"{ROUTE}?image_modal={undefined_prefix_image_modal}",
        headers=mock_auth_header,
    )
    assert response.status_code == 500


@pytest.mark.parametrize(
    "valid_pipeline_version", ["7.3.2", "23.1.3", "v2.0.1", "8.7.0-rc"]
)
def test_get_valid_pipeline_version(
    test_app,
    mock_successful_get,
    monkeypatch,
    mock_auth_header,
    set_mock_verify_token,
    valid_pipeline_version,
):
    """Given a valid pipeline version, returns a 200 status code and a non-empty list of results."""

    monkeypatch.setattr(crud, "get", mock_successful_get)
    response = test_app.get(
        f"{ROUTE}?pipeline_version={valid_pipeline_version}",
        headers=mock_auth_header,
    )
    assert response.status_code == 200
    assert response.json() != []


@pytest.mark.parametrize("mock_get", [None], indirect=True)
@pytest.mark.parametrize("invalid_pipeline_version", ["latest", "7.2", "23"])
def test_get_invalid_pipeline_version(
    test_app,
    mock_get,
    monkeypatch,
    mock_auth_header,
    set_mock_verify_token,
    invalid_pipeline_version,
):
    """Given an invalid pipeline version, returns a 422 status code."""

    monkeypatch.setattr(crud, "get", mock_get)
    response = test_app.get(
        f"{ROUTE}?pipeline_version={invalid_pipeline_version}",
        headers=mock_auth_header,
    )
    assert response.status_code == 422


@pytest.mark.parametrize(
    "valid_pipeline_name", ["np:fmriprep", "np:freesurfer"]
)
def test_get_valid_pipeline_name(
    test_app,
    mock_successful_get,
    monkeypatch,
    mock_auth_header,
    set_mock_verify_token,
    valid_pipeline_name,
):
    """Given a valid pipeline name, returns a 200 status code and a non-empty list of results."""

    monkeypatch.setattr(crud, "get", mock_successful_get)
    response = test_app.get(
        f"{ROUTE}?pipeline_name={valid_pipeline_name}",
        headers=mock_auth_header,
    )
    assert response.status_code == 200
    assert response.json() != []


@pytest.mark.parametrize("mock_get", [None], indirect=True)
@pytest.mark.parametrize(
    "invalid_pipeline_name", ["n2p:coolpipeline", "apple", "some_thing:cool"]
)
def test_get_invalid_pipeline_name(
    test_app,
    mock_get,
    monkeypatch,
    mock_auth_header,
    set_mock_verify_token,
    invalid_pipeline_name,
):
    """Given an invalid pipeline name, returns a 422 status code."""

    monkeypatch.setattr(crud, "get", mock_get)
    response = test_app.get(
        f"{ROUTE}?pipeline_name={invalid_pipeline_name}",
        headers=mock_auth_header,
    )
    assert response.status_code == 422


@pytest.mark.parametrize(
    "valid_pipeline_name, valid_pipeline_version",
    [
        ("np:fmriprep", "v2.0.1"),
        ("np:fmriprep", "23.1.3"),
        ("np:freesurfer", "7.3.2"),
        ("np:freesurfer", "8.7.0-rc"),
    ],
)
def test_get_valid_pipeline_name_version(
    test_app,
    mock_successful_get,
    monkeypatch,
    mock_auth_header,
    set_mock_verify_token,
    valid_pipeline_name,
    valid_pipeline_version,
):
    """Given a valid pipeline name and version, returns a 200 status code and a non-empty list of results."""

    monkeypatch.setattr(crud, "get", mock_successful_get)
    response = test_app.get(
        f"{ROUTE}?pipeline_name={valid_pipeline_name}&pipeline_version={valid_pipeline_version}",
        headers=mock_auth_header,
    )
    assert response.status_code == 200
    assert response.json() != []


def test_aggregate_query_response_structure(
    test_app,
    set_test_credentials,
    mock_post_agg_query_to_graph,
    mock_query_matching_dataset_sizes,
    monkeypatch,
    mock_auth_header,
    set_mock_verify_token,
):
    """Test that when aggregate results are enabled, a cohort query response has the expected structure."""
    monkeypatch.setattr(
        util, "RETURN_AGG", util.EnvVar(util.RETURN_AGG.name, True)
    )
    monkeypatch.setattr(
        crud, "post_query_to_graph", mock_post_agg_query_to_graph
    )
    monkeypatch.setattr(
        crud, "query_matching_dataset_sizes", mock_query_matching_dataset_sizes
    )

    response = test_app.get(ROUTE, headers=mock_auth_header)
    assert all(
        dataset["subject_data"] == "protected" for dataset in response.json()
    )


def test_query_without_token_succeeds_when_auth_disabled(
    test_app,
    mock_successful_get,
    monkeypatch,
    disable_auth,
    set_test_credentials,
):
    """
    Test that when authentication is disabled, a request to the /query route without a token succeeds.
    """
    monkeypatch.setattr(crud, "get", mock_successful_get)
    response = test_app.get(ROUTE)
    assert response.status_code == 200


@pytest.mark.integration
def test_integration_query_without_auth_succeeds(
    test_app, monkeypatch, disable_auth, set_test_credentials
):
    """
    Running a test against a real local test graph
    should succeed when authentication is disabled.
    """
    # Patching the QUERY_URL directly means we don't need to worry about the constituent
    # graph environment variables
    monkeypatch.setattr(
        util, "QUERY_URL", "http://localhost:7200/repositories/my_db"
    )

    response = test_app.get(ROUTE)
    assert response.status_code == 200


def test_derivatives_info_handled_by_agg_api_response(
    test_app,
    mock_post_agg_query_to_graph,
    mock_query_matching_dataset_sizes,
    monkeypatch,
    mock_auth_header,
    set_mock_verify_token,
):
    """
    Test that in the aggregated API mode, pipeline information for matching subjects
    is correctly parsed and formatted in the API response.
    """
    monkeypatch.setattr(
        util, "RETURN_AGG", util.EnvVar(util.RETURN_AGG.name, True)
    )
    monkeypatch.setattr(
        crud, "post_query_to_graph", mock_post_agg_query_to_graph
    )
    monkeypatch.setattr(
        crud, "query_matching_dataset_sizes", mock_query_matching_dataset_sizes
    )

    response = test_app.get(ROUTE, headers=mock_auth_header)
    assert response.status_code == 200

    matching_ds = response.json()[0]
    assert matching_ds["available_pipelines"] == {
        "https://github.com/nipoppy/pipeline-catalog/tree/main/processing/freesurfer": [
            "7.3.2"
        ]
    }


def test_missing_derivatives_info_handled_by_nonagg_api_response(
    test_app,
    mock_post_nonagg_query_to_graph,
    mock_query_matching_dataset_sizes,
    monkeypatch,
    mock_auth_header,
    set_mock_verify_token,
):
    """
    Test that in the non-aggregated API mode, when all matching subjects lack pipeline information,
    the API does not error out and pipeline variables in the API response still have the expected structure.
    """
    monkeypatch.setattr(
        util, "RETURN_AGG", util.EnvVar(util.RETURN_AGG.name, False)
    )
    monkeypatch.setattr(
        crud, "post_query_to_graph", mock_post_nonagg_query_to_graph
    )
    monkeypatch.setattr(
        crud, "query_matching_dataset_sizes", mock_query_matching_dataset_sizes
    )

    response = test_app.get(ROUTE, headers=mock_auth_header)
    assert response.status_code == 200

    matching_ds = response.json()[0]
    assert matching_ds["available_pipelines"] == {}
    for session in matching_ds["subject_data"]:
        assert session["completed_pipelines"] == {}


@pytest.mark.integration
def test_only_imaging_and_phenotypic_sessions_returned_in_query_response(
    test_app, monkeypatch, disable_auth, set_test_credentials
):
    """
    Test that only sessions of type PhenotypicSession and ImagingSession are returned in an unaggregated query response.
    """
    monkeypatch.setattr(
        util, "RETURN_AGG", util.EnvVar(util.RETURN_AGG.name, False)
    )
    monkeypatch.setattr(
        util, "QUERY_URL", "http://localhost:7200/repositories/my_db"
    )

    response = test_app.get(ROUTE)
    assert response.status_code == 200

    matching_ds = response.json()[0]

    sub01_sessions = [
        ses_instance
        for ses_instance in matching_ds["subject_data"]
        if ses_instance["sub_id"] == "sub-01"
    ]
    assert len(sub01_sessions) == 4

    for ses_instance in matching_ds["subject_data"]:
        assert ses_instance["session_type"] in [
            "http://neurobagel.org/vocab/ImagingSession",
            "http://neurobagel.org/vocab/PhenotypicSession",
        ], f'{ses_instance["sub_id"]}, {ses_instance["session_id"]} is of type {ses_instance["session_type"]}'
