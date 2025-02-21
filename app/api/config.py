"""Configuration environment variables for the API."""

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Data model for configurable API settings."""

    # NOTE: Environment variables are case-insensitive by default
    # (see https://docs.pydantic.dev/latest/concepts/pydantic_settings/#case-sensitivity)
    root_path: str = Field(alias="NB_NAPI_BASE_PATH", default="")
    allowed_origins: str = Field(alias="NB_API_ALLOWED_ORIGINS", default="")
    graph_username: str | None = Field(alias="NB_GRAPH_USERNAME", default=None)
    graph_password: str | None = Field(alias="NB_GRAPH_PASSWORD", default=None)
    graph_address: str = Field(alias="NB_GRAPH_ADDRESS", default="127.0.0.1")
    graph_db: str = Field(alias="NB_GRAPH_DB", default="repositories/my_db")
    graph_port: int = Field(alias="NB_GRAPH_PORT", default=7200)
    return_agg: bool = Field(alias="NB_RETURN_AGG", default=True)
    min_cell_size: int = Field(alias="NB_MIN_CELL_SIZE", default=0)
    auth_enabled: bool = Field(alias="NB_ENABLE_AUTH", default=True)
    client_id: str | None = Field(alias="NB_QUERY_CLIENT_ID", default=None)

    @computed_field
    def query_url(self) -> str:
        """Construct the URL of the graph store to be queried."""
        return f"http://{self.graph_address}:{self.graph_port}/{self.graph_db}"


settings = Settings()
