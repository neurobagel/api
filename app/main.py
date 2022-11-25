from fastapi import FastAPI, Depends, HTTPException
from fastapi import Query
from app.api import crud

app = FastAPI()


class NBQuery:
    def __init__(
        self, sex: str = Query(default=None, min_length=4, max_length=6)
    ):
        self.sex = sex


@app.get("/subjects/")
async def get_subjects(query: NBQuery = Depends(NBQuery)):
    if query.sex in ["male", "female"]:
        response = await crud.get(query.sex)
        return response

    raise HTTPException(
        status_code=422, detail=f"{query.sex} is not a valid sex"
    )

    # return {"Neurobagel": "Hello world!"}
