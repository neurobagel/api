"""CRUD functions called by path operations."""

import os

import httpx
import pandas as pd
from fastapi import HTTPException, status

from . import utility as util
from .models import CohortQueryResponse

# Order that dataset and subject-level attributes should appear in the API JSON response.
# This order is defined explicitly because when graph-returned results are transformed to a dataframe,
# the default order of columns may be different than the order that variables are given in the SPARQL SELECT state
ATTRIBUTES_ORDER = [
    "sub_id",
    "num_sessions",
    "session_id",
    "session_file_path",
    "age",
    "sex",
    "diagnosis",
    "subject_group",
    "assessment",
    "image_modal",
    "dataset_name",
    "dataset_uuid",
    "dataset_portal_uri",
]


async def get(
    min_age: float,
    max_age: float,
    sex: str,
    diagnosis: str,
    is_control: bool,
    min_num_sessions: int,
    assessment: str,
    image_modal: str,
):
    """
    Makes a POST request to Stardog API using httpx where the payload is a SPARQL query generated by the create_query function.

    Parameters
    ----------
    min_age : float
        Minimum age of subject.
    max_age : float
        Maximum age of subject.
    sex : str
        Sex of subject.
    diagnosis : str
        Subject diagnosis.
    is_control : bool
        Whether or not subject is a control.
    min_num_sessions : int
        Subject minimum number of imaging sessions.
    assessment : str
        Non-imaging assessment completed by subjects.
    image_modal : str
        Imaging modality of subject scans.

    Returns
    -------
    httpx.response
        Response of the POST request.

    """
    try:
        response = httpx.post(
            url=util.QUERY_URL,
            content=util.create_query(
                return_agg=util.RETURN_AGG.val,
                age=(min_age, max_age),
                sex=sex,
                diagnosis=diagnosis,
                is_control=is_control,
                min_num_sessions=min_num_sessions,
                assessment=assessment,
                image_modal=image_modal,
            ),
            headers=util.QUERY_HEADER,
            auth=httpx.BasicAuth(
                os.environ.get(util.GRAPH_USERNAME.name),
                os.environ.get(util.GRAPH_PASSWORD.name),
            ),
        )
    except httpx.ConnectTimeout as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Timed out while connecting to the server. Please confirm that you are connected to the McGill network and try again.",
        ) from exc

    if not response.is_success:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"{response.reason_phrase}: {response.text}",
        )

    results = response.json()

    results_dicts = [
        {k: v["value"] for k, v in res.items()}
        for res in results["results"]["bindings"]
    ]
    results_df = pd.DataFrame(results_dicts).reindex(columns=ATTRIBUTES_ORDER)

    response_obj = []
    dataset_cols = ["dataset_uuid", "dataset_name"]
    if not results_df.empty:
        for (dataset_uuid, dataset_name), group in results_df.groupby(
            by=dataset_cols
        ):
            if util.RETURN_AGG.val:
                subject_data = list(group["session_file_path"].dropna())
            else:
                subject_data = (
                    group.drop(dataset_cols, axis=1)
                    .groupby(by=["sub_id", "session_id"])
                    .agg(
                        {
                            "sub_id": "first",
                            "session_id": "first",
                            "num_sessions": "first",
                            "age": "first",
                            "sex": "first",
                            "diagnosis": lambda x: list(set(x)),
                            "subject_group": "first",
                            "assessment": "first",
                            "image_modal": lambda x: list(set(x)),
                            "session_file_path": "first",
                        }
                    )
                )
                subject_data = list(subject_data.to_dict("records"))

            response_obj.append(
                CohortQueryResponse(
                    dataset_uuid=dataset_uuid,
                    dataset_name=dataset_name,
                    dataset_portal_uri=group["dataset_portal_uri"].iloc[0]
                    if group["dataset_portal_uri"].all()
                    else None,
                    num_matching_subjects=group["sub_id"].nunique(),
                    subject_data=subject_data,
                    image_modals=list(group["image_modal"].unique()),
                )
            )

    return response_obj
