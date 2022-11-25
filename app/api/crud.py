from .utility import create_query


async def get(sex: str):
    query_str = create_query(sex=sex)

    return query_str
