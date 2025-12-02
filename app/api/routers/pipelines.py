from typing import Annotated

from fastapi import APIRouter
from pydantic.types import StringConstraints

from .. import crud
from .. import utility as util
from ..models import CONTROLLED_TERM_REGEX
from . import route_factory

router = APIRouter(prefix="/pipelines", tags=["pipelines"])

router.add_api_route(
    path="",
    endpoint=route_factory.create_get_instances_handler(
        data_element_uri="nb:Pipeline"
    ),
    methods=["GET"],
)


@router.get("/{pipeline_term}/versions")
async def get_pipeline_versions(
    pipeline_term: Annotated[
        str, StringConstraints(pattern=CONTROLLED_TERM_REGEX)
    ],
):
    """
    When a GET request is sent, return a dict keyed on the specified pipeline resource, where the value is
    list of pipeline versions available in the graph for that pipeline.
    """
    db_results = await crud.post_query_to_graph(
        util.create_pipeline_versions_query(pipeline_term)
    )
    versions_for_pipeline = {
        pipeline_term: [res["pipeline_version"] for res in db_results]
    }
    return versions_for_pipeline
