FROM python:3.10

WORKDIR /usr/src/

COPY ./requirements.txt /usr/src/app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /usr/src/app/requirements.txt

COPY ./app /usr/src/app

ENTRYPOINT ["uvicorn", "app.main:app", "--proxy-headers", "--host", "0.0.0.0"]

CMD ["--port", "8000"]