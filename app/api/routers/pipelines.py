from fastapi import APIRouter
from pydantic import constr

from .. import crud
from .. import utility as util
from ..models import CONTROLLED_TERM_REGEX

router = APIRouter(prefix="/pipelines", tags=["pipelines"])


@router.get("/{pipeline_term}/versions")
async def get_pipeline_versions(
    pipeline_term: constr(regex=CONTROLLED_TERM_REGEX),
):
    """
    When a GET request is sent, return a list of pipeline versions available in the graph
    for the specified pipeline resource.
    """
    results = crud.post_query_to_graph(
        util.create_pipeline_versions_query(pipeline_term)
    )
    results_dict = {
        pipeline_term: [
            res["pipeline_version"]
            for res in util.unpack_graph_response_json_to_dicts(results)
        ]
    }
    return results_dict
