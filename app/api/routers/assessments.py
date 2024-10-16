from fastapi import APIRouter, Request

from .. import crud
from ..models import DataElementURI, VocabLabelsResponse
from .route_factory import create_get_instances_endpoint

VOCAB_PFX = "cogatlas"
router = APIRouter(prefix="/assessments", tags=["assessments"])


@router.get("/vocab", response_model=VocabLabelsResponse)
async def get_vocab(request: Request):
    """When a GET request is sent, return a dict containing the name, namespace info, and all term ID-label mappings for the vocabulary of the specified variable."""
    return await crud.get_term_labels_for_vocab(
        term_labels_path=request.app.state.vocab_lookup_paths[VOCAB_PFX],
        vocabulary_name="Cognitive Atlas Tasks",
        namespace_prefix=VOCAB_PFX,
    )


router.add_api_route(
    path="/",
    endpoint=create_get_instances_endpoint(
        data_element_uri=DataElementURI.assessment.value, vocab_name=VOCAB_PFX
    ),
    methods=["GET"],
)
