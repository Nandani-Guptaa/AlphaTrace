from pydantic_settings import BaseSettings
from pydantic import ConfigDict, Field


class Settings(BaseSettings):
    # Application Info
    APP_NAME: str = "AlphaTrace"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    SYNTHETIC_DATA_DISCLAIMER: str = (
        "ALL DATA IN ALPHATRACE IS SYNTHETIC AND DESIGNED SOLELY FOR HACKATHON DEMONSTRATION PURPOSES. "
        "NO REAL TRADES ARE EXECUTED."
    )

    # FalkorDB Graph Database
    FALKORDB_HOST: str = Field(default="localhost", alias="FALKORDB_HOST")
    FALKORDB_PORT: int = Field(default=6379, alias="FALKORDB_PORT")
    FALKORDB_GRAPH: str = Field(default="alphatrace_risk_graph", alias="FALKORDB_GRAPH")
    FALKORDB_PASSWORD: str | None = Field(default=None, alias="FALKORDB_PASSWORD")

    # FastAPI Server
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = False

    # Streamlit Frontend
    STREAMLIT_PORT: int = 8501

    # Agent & Optional LLM
    USE_OLLAMA: bool = False
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"

    model_config = ConfigDict(env_file=".env", extra="ignore")


settings = Settings()
