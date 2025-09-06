from fastapi import APIRouter

from ..models import DataElementURI, VocabResponse
from . import route_factory

router = APIRouter(prefix="/assessments", tags=["assessments"])

router.add_api_route(
    path="",
    endpoint=route_factory.create_get_instances_handler(
        data_element_uri=DataElementURI.assessment.value
    ),
    methods=["GET"],
)
router.add_api_route(
    path="/vocab",
    endpoint=route_factory.create_get_vocab_handler(
        data_element_uri=DataElementURI.assessment.value
    ),
    methods=["GET"],
    response_model=VocabResponse,
)
