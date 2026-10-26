"""Application settings loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for VerityAI (placeholders via .env)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "VerityAI"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:5173"

    database_url: str = (
        "postgresql+psycopg2://verityai:verityai@localhost:5432/verityai"
    )

    blockchain_rpc_url: str = "http://127.0.0.1:8545"
    blockchain_chain_id: int = 31337
    blockchain_contract_address: str = ""
    blockchain_private_key: str = ""

    storage_path: str = "../storage"
    max_upload_size_mb: int = 100
    # Comma-separated extensions including the leading dot (AI model artifact types).
    allowed_upload_extensions: str = (
        ".pt,.pth,.onnx,.h5,.hdf5,.pb,.tflite,.pkl,.joblib,.safetensors,.bin,.gguf,.json,.txt"
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def allowed_extension_set(self) -> set[str]:
        return {
            ext.strip().lower()
            for ext in self.allowed_upload_extensions.split(",")
            if ext.strip()
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()
