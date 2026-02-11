"""
애플리케이션 설정 (Pydantic Settings 기반)
환경변수 또는 .env 파일에서 설정을 로드합니다.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """애플리케이션 설정"""

    # ===== MongoDB =====
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "jbnu_notices"

    # ===== API 설정 =====
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = True

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }


# 전역 설정 인스턴스
settings = Settings()
