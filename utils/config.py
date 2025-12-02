from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    bot_token: str
    postgres_dsn: str

    backend_host: str = "127.0.0.1"
    backend_port: int = 8000
    backend_base_url: str = "http://127.0.0.1:8000"

    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str

    # Secret for signing state parameter (CSRF protection)
    state_secret: str = "change_me"

    log_file: str = "bot.log"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings(
    _env_file=".env",
)


