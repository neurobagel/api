FROM python:3.10

WORKDIR /usr/src/

COPY ./requirements.txt /usr/src/app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /usr/src/app/requirements.txt

COPY ./app /usr/src/app

# NB_API_PORT, representing the port on which the API will be exposed, 
# is an environment variable that will always have a default value of 8000 when building the image
# but can be overridden when running the container.
ENTRYPOINT uvicorn app.main:app --proxy-headers --forwarded-allow-ips=* --host 0.0.0.0 --port ${NB_API_PORT:-8000}
