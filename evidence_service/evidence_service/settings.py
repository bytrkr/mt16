from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    service_name: str = "evidence_service"

settings = Settings()
