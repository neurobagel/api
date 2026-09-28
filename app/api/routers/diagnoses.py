from fastapi import APIRouter

from ..models import (
    StandardizedTermVocabularyResponse,
    StandardizedVariableURI,
)
from . import route_factory

router = APIRouter(prefix="/diagnoses", tags=["diagnoses"])

router.add_api_route(
    path="",
    endpoint=route_factory.create_get_instances_handler(
        std_var_uri=StandardizedVariableURI.diagnosis.value
    ),
    methods=["GET"],
)
router.add_api_route(
    path="/vocab",
    endpoint=route_factory.create_get_vocab_handler(
        std_var_uri=StandardizedVariableURI.diagnosis.value
    ),
    methods=["GET"],
    response_model=StandardizedTermVocabularyResponse,
)
