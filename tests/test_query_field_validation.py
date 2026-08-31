import pytest
from fastapi import HTTPException

from app.api import crud

ROUTE = "/subjects"


@pytest.mark.parametrize(
    "valid_min_age, valid_max_age",
    [(30.5, 60), (23, 23)],
)
def test_query_valid_age_range(
    test_app,
    mock_successful_post_subjects,
    valid_min_age,
    valid_max_age,
    monkeypatch,
    disable_auth,
):
    """Given a valid age range, returns a 200 status code and a non-empty list of results."""

    monkeypatch.setattr(crud, "post_subjects", mock_successful_post_subjects)
    response = test_app.post(
        url=ROUTE,
        json={"min_age": valid_min_age, "max_age": valid_max_age},
    )
    assert response.status_code == 200
    assert response.json() != []


@pytest.mark.parametrize(
    "age_keyval",
    [{"min_age": 20.75}, {"max_age": 50}],
)
def test_query_valid_age_single_bound(
    test_app,
    mock_successful_post_subjects,
    age_keyval,
    monkeypatch,
    disable_auth,
):
    """Given only a valid lower/upper age bound, returns a 200 status code and a non-empty list of results."""

    monkeypatch.setattr(crud, "post_subjects", mock_successful_post_subjects)
    response = test_app.post(url=ROUTE, json=age_keyval)
    assert response.status_code == 200
    assert response.json() != []


@pytest.mark.parametrize("mock_post_subjects", [None], indirect=True)
@pytest.mark.parametrize(
    "invalid_min_age, invalid_max_age",
    [
        ("forty", "fifty"),
        (33, 21),
        (-42.5, -40),
    ],
)
def test_query_invalid_age(
    test_app,
    mock_post_subjects,
    invalid_min_age,
    invalid_max_age,
    monkeypatch,
    disable_auth,
):
    """Given an invalid age range, returns a 422 status code."""

    monkeypatch.setattr(crud, "post_subjects", mock_post_subjects)
    response = test_app.post(
        url=ROUTE,
        json={
            "min_age": invalid_min_age,
            "max_age": invalid_max_age,
        },
    )
    assert response.status_code == 422


@pytest.mark.parametrize(
    "valid_sex",
    ["snomed:248153007", "snomed:248152002", "snomed:32570681000036106"],
)
def test_query_valid_sex(
    test_app,
    mock_successful_post_subjects,
    valid_sex,
    monkeypatch,
    disable_auth,
):
    """Given a valid sex string, returns a 200 status code and a non-empty list of results."""

    monkeypatch.setattr(crud, "post_subjects", mock_successful_post_subjects)
    response = test_app.post(url=ROUTE, json={"sex": valid_sex})
    assert response.status_code == 200
    assert response.json() != []


@pytest.mark.parametrize("mock_post_subjects", [None], indirect=True)
def test_query_invalid_sex(
    test_app, mock_post_subjects, monkeypatch, disable_auth
):
    """Given an invalid sex string, returns a 422 status code."""

    monkeypatch.setattr(crud, "post_subjects", mock_post_subjects)
    response = test_app.post(url=ROUTE, json={"sex": "apple"})
    assert response.status_code == 422


@pytest.mark.parametrize(
    "valid_diagnosis", ["snomed:35489007", "snomed:49049000", "ncit:C94342"]
)
def test_query_valid_diagnosis(
    test_app,
    mock_successful_post_subjects,
    valid_diagnosis,
    monkeypatch,
    disable_auth,
):
    """Given a valid diagnosis, returns a 200 status code and a non-empty list of results."""

    monkeypatch.setattr(crud, "post_subjects", mock_successful_post_subjects)
    response = test_app.post(url=ROUTE, json={"diagnosis": valid_diagnosis})
    assert response.status_code == 200
    assert response.json() != []


@pytest.mark.parametrize("mock_post_subjects", [None], indirect=True)
@pytest.mark.parametrize(
    "invalid_diagnosis", ["sn0med:35489007", "apple", ":123456"]
)
def test_query_invalid_diagnosis(
    test_app,
    mock_post_subjects,
    invalid_diagnosis,
    monkeypatch,
    disable_auth,
):
    """Given an invalid diagnosis, returns a 422 status code."""

    monkeypatch.setattr(crud, "post_subjects", mock_post_subjects)
    response = test_app.post(url=ROUTE, json={"diagnosis": invalid_diagnosis})
    assert response.status_code == 422


# NOTE: Stacked parametrization is a feature of pytest: all combinations of the parameters are tested.
@pytest.mark.parametrize(
    "session_param",
    ["min_num_phenotypic_sessions", "min_num_imaging_sessions"],
)
@pytest.mark.parametrize("valid_min_num_sessions", [0, 1, 2, 4, 7])
def test_query_valid_min_num_sessions(
    test_app,
    mock_successful_post_subjects,
    session_param,
    valid_min_num_sessions,
    monkeypatch,
    disable_auth,
):
    """Given a valid minimum number of imaging sessions, returns a 200 status code and a non-empty list of results."""

    monkeypatch.setattr(crud, "post_subjects", mock_successful_post_subjects)
    response = test_app.post(
        url=ROUTE,
        json={session_param: valid_min_num_sessions},
    )
    assert response.status_code == 200
    assert response.json() != []


@pytest.mark.parametrize("mock_post_subjects", [None], indirect=True)
@pytest.mark.parametrize(
    "session_param",
    ["min_num_phenotypic_sessions", "min_num_imaging_sessions"],
)
@pytest.mark.parametrize("invalid_min_num_sessions", [-3, 2.5, "apple"])
def test_query_invalid_min_num_sessions(
    test_app,
    mock_post_subjects,
    session_param,
    invalid_min_num_sessions,
    monkeypatch,
    disable_auth,
):
    """Given an invalid minimum number of imaging sessions, returns a 422 status code."""

    monkeypatch.setattr(crud, "post_subjects", mock_post_subjects)
    response = test_app.post(
        url=ROUTE,
        json={session_param: invalid_min_num_sessions},
    )
    assert response.status_code == 422


def test_query_valid_assessment(
    test_app,
    mock_successful_post_subjects,
    monkeypatch,
    disable_auth,
):
    """Given a valid assessment, returns a 200 status code and a non-empty list of results."""

    monkeypatch.setattr(crud, "post_subjects", mock_successful_post_subjects)
    response = test_app.post(
        url=ROUTE, json={"assessment": "nb:cogAtlas-1234"}
    )
    assert response.status_code == 200
    assert response.json() != []


@pytest.mark.parametrize("mock_post_subjects", [None], indirect=True)
@pytest.mark.parametrize(
    "invalid_assessment", ["bg01:cogAtlas-1234", "cogAtlas-1234"]
)
def test_query_invalid_assessment(
    test_app, mock_post_subjects, invalid_assessment, monkeypatch, disable_auth
):
    """Given an invalid assessment, returns a 422 status code."""

    monkeypatch.setattr(crud, "post_subjects", mock_post_subjects)
    response = test_app.post(
        url=ROUTE, json={"assessment": invalid_assessment}
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
def test_query_valid_available_image_modal(
    test_app,
    mock_successful_post_subjects,
    valid_available_image_modal,
    monkeypatch,
    disable_auth,
):
    """Given a valid and available image modality, returns a 200 status code and a non-empty list of results."""

    monkeypatch.setattr(crud, "post_subjects", mock_successful_post_subjects)
    response = test_app.post(
        url=ROUTE, json={"image_modal": valid_available_image_modal}
    )
    assert response.status_code == 200
    assert response.json() != []


@pytest.mark.parametrize("mock_post_subjects", [[]], indirect=True)
@pytest.mark.parametrize(
    "valid_unavailable_image_modal",
    ["nidm:Flair", "owl:sameAs", "nb:FlowWeighted", "snomed:something"],
)
def test_query_valid_unavailable_image_modal(
    test_app,
    valid_unavailable_image_modal,
    mock_post_subjects,
    monkeypatch,
    disable_auth,
):
    """Given a valid, pre-defined, and unavailable image modality, returns a 200 status code and an empty list of results."""

    monkeypatch.setattr(crud, "post_subjects", mock_post_subjects)
    response = test_app.post(
        url=ROUTE,
        json={"image_modal": valid_unavailable_image_modal},
    )

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.parametrize("mock_post_subjects", [None], indirect=True)
@pytest.mark.parametrize(
    "invalid_image_modal", ["2nim:EEG", "apple", "some_thing:cool"]
)
def test_query_invalid_image_modal(
    test_app,
    mock_post_subjects,
    invalid_image_modal,
    monkeypatch,
    disable_auth,
):
    """Given an invalid image modality, returns a 422 status code."""

    monkeypatch.setattr(crud, "post_subjects", mock_post_subjects)
    response = test_app.post(
        url=ROUTE, json={"image_modal": invalid_image_modal}
    )
    assert response.status_code == 422


@pytest.mark.parametrize(
    "mock_post_with_exception", [HTTPException(500)], indirect=True
)
@pytest.mark.parametrize(
    "undefined_prefix_image_modal",
    ["dbo:abstract", "sex:apple", "something:cool"],
)
def test_query_undefined_prefix_image_modal(
    test_app,
    undefined_prefix_image_modal,
    mock_post_with_exception,
    monkeypatch,
    disable_auth,
):
    """Given a valid and undefined prefix image modality, returns a 500 status code."""

    monkeypatch.setattr(crud, "post_subjects", mock_post_with_exception)
    response = test_app.post(
        url=ROUTE, json={"image_modal": undefined_prefix_image_modal}
    )
    assert response.status_code == 500


@pytest.mark.parametrize(
    "valid_pipeline_version", ["7.3.2", "23.1.3", "v2.0.1", "8.7.0-rc"]
)
def test_query_valid_pipeline_version(
    test_app,
    mock_successful_post_subjects,
    monkeypatch,
    disable_auth,
    valid_pipeline_version,
):
    """Given a valid pipeline version, returns a 200 status code and a non-empty list of results."""

    monkeypatch.setattr(crud, "post_subjects", mock_successful_post_subjects)
    response = test_app.post(
        url=ROUTE,
        json={"pipeline_version": valid_pipeline_version},
    )
    assert response.status_code == 200
    assert response.json() != []


@pytest.mark.parametrize("mock_post_subjects", [None], indirect=True)
@pytest.mark.parametrize("invalid_pipeline_version", ["latest", "7.2", "23"])
def test_query_invalid_pipeline_version(
    test_app,
    mock_post_subjects,
    monkeypatch,
    disable_auth,
    invalid_pipeline_version,
):
    """Given an invalid pipeline version, returns a 422 status code."""

    monkeypatch.setattr(crud, "post_subjects", mock_post_subjects)
    response = test_app.post(
        url=ROUTE,
        json={"pipeline_version": invalid_pipeline_version},
    )
    assert response.status_code == 422


@pytest.mark.parametrize(
    "valid_pipeline_name", ["np:fmriprep", "np:freesurfer"]
)
def test_query_valid_pipeline_name(
    test_app,
    mock_successful_post_subjects,
    monkeypatch,
    disable_auth,
    valid_pipeline_name,
):
    """Given a valid pipeline name, returns a 200 status code and a non-empty list of results."""

    monkeypatch.setattr(crud, "post_subjects", mock_successful_post_subjects)
    response = test_app.post(
        url=ROUTE, json={"pipeline_name": valid_pipeline_name}
    )
    assert response.status_code == 200
    assert response.json() != []


@pytest.mark.parametrize("mock_post_subjects", [None], indirect=True)
@pytest.mark.parametrize(
    "invalid_pipeline_name", ["n2p:coolpipeline", "apple", "some_thing:cool"]
)
def test_query_invalid_pipeline_name(
    test_app,
    mock_post_subjects,
    monkeypatch,
    disable_auth,
    invalid_pipeline_name,
):
    """Given an invalid pipeline name, returns a 422 status code."""

    monkeypatch.setattr(crud, "post_subjects", mock_post_subjects)
    response = test_app.post(
        url=ROUTE,
        json={"pipeline_name": invalid_pipeline_name},
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
def test_query_valid_pipeline_name_version(
    test_app,
    mock_successful_post_subjects,
    monkeypatch,
    disable_auth,
    valid_pipeline_name,
    valid_pipeline_version,
):
    """Given a valid pipeline name and version, returns a 200 status code and a non-empty list of results."""

    monkeypatch.setattr(crud, "post_subjects", mock_successful_post_subjects)
    response = test_app.post(
        url=ROUTE,
        json={
            "pipeline_name": valid_pipeline_name,
            "pipeline_version": valid_pipeline_version,
        },
    )
    assert response.status_code == 200
    assert response.json() != []
