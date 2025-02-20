from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Data model for settings."""

    nb_napi_base_path: str = ""
    nb_api_allowed_origins: str = ""
    nb_graph_username: str
    nb_graph_password: str
    nb_graph_address: str = "127.0.0.1"
    nb_graph_db: str = "repositories/my_db"
    nb_graph_port: int = 7200
    # Double check how this is parsed from environment
    nb_return_agg: bool = True
    # Double check how this is parsed from environment
    nb_min_cell_size: int = 0
