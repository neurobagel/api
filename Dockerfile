# Pre-build stage to make pip compatible lockfile
FROM ghcr.io/astral-sh/uv:latest AS prebuild

WORKDIR /build

COPY pyproject.toml uv.lock ./
RUN uv export --frozen --no-dev --no-hashes -o requirements.txt

# Build stage
FROM python:3.10

WORKDIR /usr/src/
COPY --from=prebuild /build/requirements.txt /usr/src/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /usr/src/requirements.txt

COPY ./app /usr/src/app

# NB_API_PORT, representing the port on which the API will be exposed, 
# is an environment variable that will always have a default value of 8000 when building the image
# but can be overridden when running the container.
ENTRYPOINT uvicorn app.main:app --proxy-headers --forwarded-allow-ips=* --host 0.0.0.0 --port ${NB_API_PORT:-8000}
