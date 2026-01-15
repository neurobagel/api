"""Configuration environment variables for the API."""

from pathlib import Path

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

NEUROBAGEL_CONFIG_REPO = "neurobagel/communities"
DEFAULT_NEUROBAGEL_CONFIG = "Neurobagel"

# NOTE: We store the data fetched or loaded on app startup in globals
# rather than storing them on the app instance (which would require accessing them through the request object;
# see https://www.starlette.io/applications/#storing-state-on-the-app-instance).
# This avoids having to thread the request object through every function that needs access to e.g., the context
# and also makes it easier to mock the configuration during testing.
CONTEXT = {}
ALL_VOCABS = {}
DATASETS_METADATA = {}


class Settings(BaseSettings):
    """Data model for configurable API settings."""

    # Ignore environment variables that are set to empty strings
    model_config = SettingsConfigDict(env_ignore_empty=True)

    # NOTE: Environment variables are case-insensitive by default
    # (see https://docs.pydantic.dev/latest/concepts/pydantic_settings/#case-sensitivity)
    root_path: str = Field(
        alias="NB_NAPI_BASE_PATH",
        default="",
        description="The base URL path prefix for the API. When deployed behind a reverse proxy, set this to the subpath at which the app is mounted (if any), "
        "and configure the proxy to strip this prefix from incoming requests.",
    )
    allowed_origins: str | None = Field(
        alias="NB_API_ALLOWED_ORIGINS", default=None
    )
    graph_username: str | None = Field(alias="NB_GRAPH_USERNAME", default=None)
    graph_password: str | None = Field(alias="NB_GRAPH_PASSWORD", default=None)
    graph_address: str = Field(alias="NB_GRAPH_ADDRESS", default="127.0.0.1")
    graph_db: str = Field(alias="NB_GRAPH_DB", default="repositories/my_db")
    graph_port: int = Field(alias="NB_GRAPH_PORT", default=7200)
    datasets_metadata_path: Path = Field(
        alias="NB_DATASETS_METADATA_PATH",
        default=Path("/data/datasets_metadata.json"),
    )
    return_agg: bool = Field(alias="NB_RETURN_AGG", default=True)
    min_cell_size: int = Field(alias="NB_MIN_CELL_SIZE", default=0)
    auth_enabled: bool = Field(alias="NB_ENABLE_AUTH", default=True)
    client_id: str | None = Field(alias="NB_QUERY_CLIENT_ID", default=None)
    config: str = Field(
        alias="NB_CONFIG",
        default=DEFAULT_NEUROBAGEL_CONFIG,
        description="The name of the community configuration to use to query the graph data.",
    )

    @computed_field
    @property
    def query_url(self) -> str:
        """Construct the URL of the graph store to be queried."""
        return f"http://{self.graph_address}:{self.graph_port}/{self.graph_db}"


settings = Settings()
