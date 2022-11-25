import app.api.utility as util
import os
import httpx


async def get(sex: str):
    response = httpx.post(
        url=util.QUERY_URL,
        data=util.create_query(sex=sex),
        headers=util.QUERY_HEADER,
        auth=httpx.BasicAuth(
            os.environ.get("USER"), os.environ.get("PASSWORD")
        ),
    )

    return response
