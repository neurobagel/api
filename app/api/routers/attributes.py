from fastapi import APIRouter, Request
from pydantic import constr

from .. import crud
from ..models import CONTROLLED_TERM_REGEX, DataElementURI, VocabLabelsResponse

router = APIRouter(prefix="/attributes", tags=["attributes"])


@router.get("/{data_element_URI}/vocab", response_model=VocabLabelsResponse)
async def get_term_labels_for_vocab(
    data_element_URI: DataElementURI, request: Request
):
    """When a GET request is sent, return a dict containing the name, namespace info, and all term ID-label mappings for the vocabulary of the specified variable."""
    # TODO: If/when more attribute options are supported, consider refactoring to use match/case (see https://peps.python.org/pep-0634/#the-match-statement)
    if data_element_URI == DataElementURI.assessment:
        return await crud.get_term_labels_for_vocab(
            term_labels_path=request.app.state.cogatlas_term_lookup_path,
            vocabulary_name="Cognitive Atlas Tasks",
            namespace_prefix="cogatlas",
        )
    if data_element_URI == DataElementURI.diagnosis:
        return await crud.get_term_labels_for_vocab(
            term_labels_path=request.app.state.snomed_term_lookup_path,
            vocabulary_name="SNOMED CT",
            namespace_prefix="snomed",
        )


@router.get("/{data_element_URI}")
async def get_terms(
    data_element_URI: constr(regex=CONTROLLED_TERM_REGEX), request: Request
):
    """
    When a GET request is sent, return a dict with the only key corresponding to the controlled term of a neurobagel class,
    and the value being a list of dictionaries each corresponding to an available class instance term from the graph.
    """
    term_labels_path = None

    # TODO: If/when more attribute options are supported, consider refactoring to use match/case (see https://peps.python.org/pep-0634/#the-match-statement)
    if data_element_URI == DataElementURI.assessment:
        term_labels_path = request.app.state.cogatlas_term_lookup_path
    if data_element_URI == DataElementURI.diagnosis:
        term_labels_path = request.app.state.snomed_term_lookup_path

    return await crud.get_terms(data_element_URI, term_labels_path)


@router.get("/", response_model=list)
async def get_attributes():
    """When a GET request is sent, return a list of the harmonized controlled term attributes."""
    response = await crud.get_controlled_term_attributes()

    return response
