from fastapi import FastAPI, Depends
from fastapi import Query
from app.api import crud

app = FastAPI()


class NBQuery:
    def __init__(self, sex: str = Query(default=None, max_length=10)):
        self.sex = sex


@app.get("/subjects/")
async def get_subjects(query: NBQuery = Depends(NBQuery)):
    response = await crud.get(query.sex)
    # return {"Neurobagel": "Hello world!"}

    return response
