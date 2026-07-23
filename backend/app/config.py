from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/prediction_radar"
    cors_origins: str = "http://localhost:4321,http://localhost:3000"
    gamma_api_base: str = "https://gamma-api.polymarket.com"
    clob_api_base: str = "https://clob.polymarket.com"
    sync_market_limit: int = 200
    sync_volume_sample: int = 150
    sync_bucket_sample: int = 50
    snapshot_retention_days: int = 7
    min_volume_24h: float = 10000.0
    min_liquidity: float = 5000.0
    min_probability: float = 0.05
    max_probability: float = 0.95
    min_hours_to_end: int = 168
    min_change_24h: float = 0.05
    min_emerging_change_24h: float = 0.03
    min_volume_spike: float = 1.5
    min_confidence: float = 40.0
    history_max_deviation_hours: float = 6.0
    top_movers_limit: int = 10
    emerging_signals_limit: int = 10
    daily_radar_limit: int = 10
    narrative_trends_limit: int = 8
    min_narrative_members: int = 2
    min_narrative_coherence: float = 0.6
    http_timeout_seconds: float = 30.0

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
