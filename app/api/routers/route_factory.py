from fastapi import Request

from .. import crud


def create_get_instances_endpoint(
    data_element_uri: str, vocab_name: str | None
):
    async def get_instances(request: Request):
        term_labels_path = (
            request.app.state.vocab_lookup_paths[vocab_name]
            if vocab_name is not None
            else None
        )
        return await crud.get_terms(data_element_uri, term_labels_path)

    return get_instances
