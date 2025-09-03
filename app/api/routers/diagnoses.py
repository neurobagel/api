from fastapi import APIRouter

from ..models import DataElementURI, VocabResponse
from . import route_factory

EXTERNAL_VOCAB = "snomed_disorder"
router = APIRouter(prefix="/diagnoses", tags=["diagnoses"])

router.add_api_route(
    path="",
    endpoint=route_factory.create_get_instances_handler(
        data_element_uri=DataElementURI.diagnosis.value,
        external_vocab=EXTERNAL_VOCAB,
    ),
    methods=["GET"],
)
router.add_api_route(
    path="/vocab",
    endpoint=route_factory.create_get_vocab_handler(
        external_vocab=EXTERNAL_VOCAB,
        vocab_name="SNOMED CT Disorder",
        namespace_prefix="snomed",
    ),
    methods=["GET"],
    response_model=VocabResponse,
)
