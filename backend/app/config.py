import os
from pydantic_settings  import BaseSettings

class Settings(BaseSettings):
    # Application Configurations
    APP_NAME: str = "Machine Logs App"
    ENVIRONMENT: str = "development"  # Options: development, testing, production
    DEBUG_MODE: bool = True

    # Database Configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://user:password@localhost/machine_logs_db"
    )

    # Other Configurations (Optional)
    LOG_LEVEL: str = "info"  # Logging levels: debug, info, warning, error, critical

    class Config:
        env_file = ".env"  # Load sensitive settings from a .env file


# Create a settings instance
settings = Settings()
