from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Data model for settings."""

    # TODO: Make case-sensitive?
    # We don't want Pydantic errors to be raised when the environment variables are not set
    # model_config = SettingsConfigDict(validate_default=False)

    root_path: str = Field(alias="NB_NAPI_BASE_PATH", default="")
    allowed_origins: str = Field(alias="NB_API_ALLOWED_ORIGINS", default="")
    # TODO: Figure out what to do about defaults for username/password
    graph_username: str | None = Field(alias="NB_GRAPH_USERNAME", default=None)
    graph_password: str | None = Field(alias="NB_GRAPH_PASSWORD", default=None)
    graph_address: str = Field(alias="NB_GRAPH_ADDRESS", default="127.0.0.1")
    graph_db: str = Field(alias="NB_GRAPH_DB", default="repositories/my_db")
    graph_port: int = Field(alias="NB_GRAPH_PORT", default=7200)
    # Double check how this is parsed from environment
    return_agg: bool = Field(alias="NB_RETURN_AGG", default=True)
    # Double check how this is parsed from environment
    min_cell_size: int = Field(alias="NB_MIN_CELL_SIZE", default=0)
    auth_enabled: bool = Field(alias="NB_ENABLE_AUTH", default=True)
    client_id: str | None = Field(alias="NB_QUERY_CLIENT_ID", default=None)

    # TODO: Add query url as computed field and query header as constant


settings = Settings()
