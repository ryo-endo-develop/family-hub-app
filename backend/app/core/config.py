from functools import lru_cache
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # .env ファイルから読み込む環境変数
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_SERVER: str
    POSTGRES_PORT: str = "5432"  # デフォルトポート

    # データベース接続URLを構築
    DATABASE_URL: str | None = None

    # Pydantic V2 スタイル: model_post_initを使用
    def model_post_init(self, __context) -> None:
        encoded_password = quote_plus(self.POSTGRES_PASSWORD)
        db_url = f"postgresql+asyncpg://{self.POSTGRES_USER}:{encoded_password}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        self.DATABASE_URL = db_url
        super().model_post_init(__context)

    # .env ファイルを読み込むための設定
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# 設定インスタンスをキャッシュして使い回す
@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
