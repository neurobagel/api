from .. import config, crud
from ..models import StandardizedTermVocabularyResponse


def create_get_instances_handler(data_element_uri: str):
    """Create the handler function (path function) for the base path of an attribute router."""

    async def get_instances():
        """
        When a GET request is sent, return a dict with the only key corresponding to the controlled term of a neurobagel class,
        and the value being a list of dictionaries each corresponding to an available class instance term from the graph.
        """
        terms_vocab = config.ALL_VOCABS.get(data_element_uri)
        return await crud.get_terms(
            data_element_URI=data_element_uri, std_trm_vocab=terms_vocab
        )

    return get_instances


def create_get_vocab_handler(data_element_uri: str):
    """Create the handler function (path function) for the `/vocab` endpoint of an attribute router."""

    async def get_vocab():
        """
        When a GET request is sent, return a list of namespace objects, where each object includes
        the metadata and terms of a namespace used in the vocabulary for the specified variable.
        """
        terms_vocab = config.ALL_VOCABS.get(data_element_uri)
        return StandardizedTermVocabularyResponse(terms_vocab)

    return get_vocab
