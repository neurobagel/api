from fastapi import APIRouter

from ..models import DataElementURI, VocabLabelsResponse
from . import route_factory

EXTERNAL_VOCAB = "cogatlas"
router = APIRouter(prefix="/assessments", tags=["assessments"])

router.add_api_route(
    path="/",
    endpoint=route_factory.create_get_instances_handler(
        data_element_uri=DataElementURI.assessment.value,
        external_vocab=EXTERNAL_VOCAB,
    ),
    methods=["GET"],
)
router.add_api_route(
    path="/vocab",
    endpoint=route_factory.create_get_vocab_handler(
        external_vocab=EXTERNAL_VOCAB, vocab_name="Cognitive Atlas Tasks"
    ),
    methods=["GET"],
    response_model=VocabLabelsResponse,
)
