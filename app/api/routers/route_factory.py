from .. import crud, env_settings
from ..env_settings import settings
from ..models import StandardizedTermVocabularyResponse


def create_get_instances_handler(std_var_uri: str):
    """Create the handler function (path function) for the base path of an attribute router."""

    async def get_instances():
        """
        When a GET request is sent, return a dict with the only key corresponding to a standardized variable URI,
        and the value being a list of dictionaries each corresponding to an available instance term from the graph.
        """
        terms_vocab = env_settings.ALL_VOCABS.get(std_var_uri, [])

        if settings.catalog_mode:
            response = await crud.fetch_available_terms_from_catalog_datasets(
                std_var_uri=std_var_uri, std_trm_vocab=terms_vocab
            )
        else:
            response = await crud.get_terms(
                std_var_uri=std_var_uri, std_trm_vocab=terms_vocab
            )

        return response

    return get_instances


def create_get_vocab_handler(std_var_uri: str):
    """Create the handler function (path function) for the `/vocab` endpoint of an attribute router."""

    async def get_vocab():
        """
        When a GET request is sent, return a list of namespace objects, where each object includes
        the metadata and terms of a namespace used in the vocabulary for the specified variable.
        """
        terms_vocab = env_settings.ALL_VOCABS.get(std_var_uri)
        return StandardizedTermVocabularyResponse(terms_vocab)

    return get_vocab
