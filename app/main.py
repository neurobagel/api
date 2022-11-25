from fastapi import FastAPI, Depends, HTTPException
from fastapi import Query
from app.api import crud

app = FastAPI()


class NBQuery:
    def __init__(
        self, sex: str = Query(default=None, min_length=4, max_length=6)
    ):
        self.sex = sex


@app.get("/query/")
async def get_query(query: NBQuery = Depends(NBQuery)):
    if query.sex in ["male", "female", None]:
        response = await crud.get(query.sex)
        return response.json()

    raise HTTPException(
        status_code=422, detail=f"{query.sex} is not a valid sex"
    )
