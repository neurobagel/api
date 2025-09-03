from fastapi import Request

from .. import crud


def create_get_instances_handler(data_element_uri: str):
    """Create the handler function (path function) for the base path of an attribute router."""

    async def get_instances(request: Request):
        """
        When a GET request is sent, return a dict with the only key corresponding to the controlled term of a neurobagel class,
        and the value being a list of dictionaries each corresponding to an available class instance term from the graph.
        """
        term_labels_path = request.app.state.vocab_lookup_paths.get(
            data_element_uri
        )
        return await crud.get_terms(data_element_uri, term_labels_path)

    return get_instances


def create_get_vocab_handler(
    external_vocab: str, vocab_name: str, namespace_prefix: str
):
    """Create the handler function (path function) for the `/vocab` endpoint of an attribute router."""

    async def get_vocab(request: Request):
        """
        When a GET request is sent, return a dict containing the name, namespace info,
        and all term ID-label mappings for the vocabulary of the specified variable.
        """
        return await crud.get_term_labels_for_vocab(
            term_labels_path=request.app.state.vocab_lookup_paths[
                external_vocab
            ],
            vocabulary_name=vocab_name,
            namespace_prefix=namespace_prefix,
        )

    return get_vocab
