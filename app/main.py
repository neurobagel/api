"""Main app."""

import logging
import sys
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.responses import HTMLResponse, ORJSONResponse, RedirectResponse

from .api import env_settings
from .api import utility as util
from .api.env_settings import Settings, settings
from .api.logger import get_logger, log_error
from .api.routers import (
    assessments,
    attributes,
    datasets,
    diagnoses,
    imaging_modalities,
    pipelines,
    query,
    subjects,
)
from .api.security import check_client_id

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="[%Y-%m-%d %H:%M:%S]",
)
logger = get_logger(__name__)

favicon_url = "https://raw.githubusercontent.com/neurobagel/documentation/main/docs/imgs/logo/neurobagel_favicon.png"

# Check if code is currently running in a test environment
IS_TESTING = "pytest" in sys.modules


def fetch_available_community_config_names() -> list[str]:
    """Fetch available Neurobagel community configuration names from the specified URL."""
    response = util.request_data(
        util.create_gh_raw_content_url(
            env_settings.NEUROBAGEL_CONFIG_REPO,
            "config_metadata/config_namespace_map.json",
        ),
        "Failed to fetch available Neurobagel community configurations.",
    )
    config_names = [_config["config_name"] for _config in response]

    return config_names


def validate_environment_variables():
    """
    Check that all required environment variables are set, and exit the app if any are missing or invalid.
    """
    if settings.graph_username is None or settings.graph_password is None:
        log_error(
            logger,
            f"The application was launched but could not find the {Settings.model_fields['graph_username'].alias} and / or {Settings.model_fields['graph_password'].alias} environment variables.",
        )

    if settings.allowed_origins is None:
        logger.warning(
            f"The API was launched without providing any values for the {Settings.model_fields['allowed_origins'].alias} environment "
            "variable. "
            "This means that the API will only be accessible from the same origin it is hosted from: "
            "https://developer.mozilla.org/en-US/docs/Web/Security/Same-origin_policy. "
            "If you want to access the API from tools hosted at other origins such as the Neurobagel query tool, "
            f"explicitly set the value of {Settings.model_fields['allowed_origins'].alias} to the origin(s) of these tools (e.g. "
            "http://localhost:3000). "
            "Multiple allowed origins should be separated with spaces in a single string enclosed in quotes."
        )

    available_configs = fetch_available_community_config_names()
    if settings.config not in available_configs:
        log_error(
            logger,
            f"'{settings.config}' is not a recognized Neurobagel community configuration. "
            f"Available community configurations: {', '.join(available_configs)}",
        )


def fetch_vocabularies(config_name: str) -> dict:
    """
    Fetch all standardized term configuration files for the specified community configuration from GitHub.
    """
    # These are the ID parts of standardized variable URIs, which will later be prefixed with the namespace prefix defined in config.json
    configurable_std_var_ids = ["Assessment", "Diagnosis"]
    config_dir_url = util.create_gh_raw_content_url(
        env_settings.NEUROBAGEL_CONFIG_REPO, f"configs/{config_name}"
    )

    std_var_config = util.request_data(
        f"{config_dir_url}/config.json",
        f"Failed to fetch the {config_name if config_name != 'Neurobagel' else 'base'} Neurobagel community configuration.",
    )
    # TODO: For now we only consider the first entry in config.json since
    # we only support a single namespace for standardized variables (the Neurobagel vocab)
    # - refactor once we support custom standardized variables from potentially >1 namespaces
    std_var_config = std_var_config[0]

    all_std_trm_vocabs = {}
    for var_id in configurable_std_var_ids:
        var_uri = f"{std_var_config['namespace_prefix']}:{var_id}"
        std_trm_vocab_file_name = next(
            (
                var["terms_file"]
                for var in std_var_config["standardized_variables"]
                if var["id"] == var_id
            ),
            None,
        )
        if std_trm_vocab_file_name:
            std_trm_vocab = util.request_data(
                f"{config_dir_url}/{std_trm_vocab_file_name}",
                f"Failed to fetch standardized term vocabulary for {var_uri}.",
            )
            all_std_trm_vocabs[var_uri] = std_trm_vocab

    # The imaging modalities vocab is not configurable but is still an external file we need to fetch.
    # Since it is not configurable across communities, the vocab file is not listed in config.json under a standardized variable.
    # So, for now we always fetch it from the Neurobagel config directory.
    # TODO revisit the prefix for this specific variable once we support custom standardized variables.
    imaging_vocab_uri = f"{std_var_config['namespace_prefix']}:Image"
    imaging_vocab_url = util.create_gh_raw_content_url(
        env_settings.NEUROBAGEL_CONFIG_REPO,
        "configs/Neurobagel/imaging_modalities.json",
    )
    imaging_vocab = util.request_data(
        imaging_vocab_url,
        f"Failed to fetch standardized term vocabulary for {imaging_vocab_uri}.",
    )
    all_std_trm_vocabs[imaging_vocab_uri] = imaging_vocab

    return all_std_trm_vocabs


def fetch_supported_namespaces_for_config(config_name: str) -> dict:
    """
    Return a dictionary of supported namespace prefixes and their corresponding full URLs for a given community configuration.
    """
    config_namespaces_mapping = util.request_data(
        util.create_gh_raw_content_url(
            env_settings.NEUROBAGEL_CONFIG_REPO,
            "config_metadata/config_namespace_map.json",
        ),
        "Failed to fetch the recognized namespaces for Neurobagel community configurations.",
    )

    namespaces_for_config = next(
        _config["namespaces"]
        for _config in config_namespaces_mapping
        if _config["config_name"] == config_name
    )

    context = {}
    for namespace_group in namespaces_for_config.values():
        for namespace in namespace_group:
            context[namespace["namespace_prefix"]] = namespace["namespace_url"]

    return context


def setup_app():
    """
    Perform initial setup tasks before the API starts, including:
    - Validating required environment variables.
    - Performing authentication checks.
    - Fetching vocabularies for standardized variables.

    These steps are executed outside of the FastAPI lifespan to exit cleanly and
    with informative messages on failures. Once inside the lifespan,
    intentional exits always produce FastAPI/Starlette tracebacks that cannot be cleanly suppressed.
    (See https://github.com/Kludex/starlette/discussions/2964 for example.)
    """

    # Validate environment variables
    validate_environment_variables()

    # Authentication check
    check_client_id()

    # Initialize vocabularies
    env_settings.ALL_VOCABS = fetch_vocabularies(settings.config)
    # Create context
    env_settings.CONTEXT = fetch_supported_namespaces_for_config(
        settings.config
    )


# TODO: Remove
# def pre_startup():
#     if "pytest" not in sys.modules:
#         setup_app()


# pre_startup()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events.

    On shutdown:
    - Cleans up temporary directories to free resources.
    """
    yield

    # Cleanup
    env_settings.ALL_VOCABS.clear()
    env_settings.CONTEXT.clear()


def create_app(skip_setup: bool = False) -> FastAPI:
    """
    Create and configure the FastAPI app instance.

    Parameters
    ----------
    skip_setup : bool, default False
        Whether to skip the setup steps including environment variable validation and vocabulary fetching.
        Used to prevent setup_app from automatically running when the app is imported during tests.

    Returns
    -------
    FastAPI
        The configured FastAPI app instance.
    """
    if not skip_setup:
        setup_app()

    app = FastAPI(
        root_path=settings.root_path,
        lifespan=lifespan,
        default_response_class=ORJSONResponse,
        docs_url=None,
        redoc_url=None,
        redirect_slashes=False,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=util.parse_origins_as_list(settings.allowed_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/", response_class=HTMLResponse)
    def root(request: Request):
        """
        Display a welcome message and a link to the API documentation.
        """
        return f"""
    <html>
            <head>
                <style>
                    body {{
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        background-color: #f0f0f0;
                        font-family: Arial, sans-serif;
                        margin: 0;
                    }}
                    .container {{
                        text-align: center;
                    }}
                    .logo {{
                        animation: spin 5s linear infinite;
                    }}
                    @keyframes spin {{
                        0% {{ transform: rotate(0deg); }}
                        100% {{ transform: rotate(360deg); }}
                    }}
                    h1 {{
                        color: #333;
                    }}
                    p {{
                        color: #666;
                    }}
                    a {{
                        color: #007bff;
                        text-decoration: none;
                    }}
                    a:hover {{
                        text-decoration: underline;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <img src="https://raw.githubusercontent.com/neurobagel/documentation/main/docs/imgs/logo/neurobagel_logo.png" alt="Neurobagel Logo" class="logo" width="144" height="144">
                    <h1>Welcome to the Neurobagel REST API!</h1>
                    <p>Please visit the <a href="{request.scope.get('root_path', '')}/docs">API documentation</a> to view available API endpoints.</p>
                </div>
            </body>
        </html>
        """

    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon():
        """
        Overrides the default favicon with a custom one.

        NOTE: When the API is behind a reverse proxy that has a stripped path prefix (and root_path is defined),
        the custom favicon doesn't appear to work correctly for any API paths other than the docs,
        as the path in the favicon request isn't automatically adjusted to include the root path prefix.
        """
        return RedirectResponse(url=favicon_url)

    @app.get("/docs", include_in_schema=False)
    def overridden_swagger(request: Request):
        """
        Overrides the Swagger UI HTML for the "/docs" endpoint.
        """
        return get_swagger_ui_html(
            openapi_url=f"{request.scope.get('root_path', '')}/openapi.json",
            title="Neurobagel API",
            swagger_favicon_url=favicon_url,
        )

    @app.get("/redoc", include_in_schema=False)
    def overridden_redoc(request: Request):
        """
        Overrides the Redoc HTML for the "/redoc" endpoint.
        """
        return get_redoc_html(
            openapi_url=f"{request.scope.get('root_path', '')}/openapi.json",
            title="Neurobagel API",
            redoc_favicon_url=favicon_url,
        )

    app.include_router(query.router)
    app.include_router(datasets.router)
    app.include_router(subjects.router)
    app.include_router(attributes.router)
    app.include_router(assessments.router)
    app.include_router(diagnoses.router)
    app.include_router(imaging_modalities.router)
    app.include_router(pipelines.router)

    return app


app = create_app(skip_setup=IS_TESTING)


# Automatically start uvicorn server on execution of main.py
if __name__ == "__main__":
    uvicorn.run("app.main:app", port=8000, reload=True)
