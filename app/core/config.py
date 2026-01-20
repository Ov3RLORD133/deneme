"""
Configuration management for KeyChaser using Pydantic Settings.

This module handles all configuration parameters including ports,
database paths, and logging settings. Environment variables are
automatically loaded and validated.
"""

from pathlib import Path
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    
    All settings can be overridden via environment variables prefixed
    with KEYCHASER_ (e.g., KEYCHASER_DB_PATH).
    """
    
    # Application Metadata
    app_name: str = "KeyChaser"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", description="Host to bind API server")
    api_port: int = Field(default=8000, description="FastAPI dashboard port")
    
    # Database Configuration
    db_path: Path = Field(
        default=Path("data/keychaser.db"),
        description="SQLite database file path"
    )
    
    # Logging Configuration
    log_path: Path = Field(
        default=Path("data/logs"),
        description="Directory for log files"
    )
    log_level: str = Field(default="INFO", description="Logging level")
    log_to_file: bool = Field(default=True, description="Enable file logging")
    
    # Protocol Handler Configuration
    protocols_dir: Path = Field(
        default=Path("app/protocols"),
        description="Directory containing protocol handlers"
    )
    enabled_protocols: List[str] = Field(
        default=["example_logger", "agent_tesla"],
        description="List of enabled protocol modules"
    )
    
    # Authentication & Security
    secret_key: str = Field(
        default="CHANGE_ME_IN_PRODUCTION_USE_openssl_rand_hex_32",
        description="JWT secret key (32+ chars, use `openssl rand -hex 32`)"
    )
    
    # Security Settings
    max_packet_size: int = Field(
        default=65536,  # 64KB
        description="Maximum packet size to accept (prevents DoS)"
    )
    connection_timeout: int = Field(
        default=30,
        description="Connection timeout in seconds"
    )
    max_connections_per_ip: int = Field(
        default=10,
        description="Maximum concurrent connections per IP address"
    )
    
    # Dashboard Configuration
    dashboard_refresh_interval: int = Field(
        default=5,
        description="Dashboard auto-refresh interval in seconds"
    )
    
    model_config = SettingsConfigDict(
        env_prefix="KEYCHASER_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    def get_database_url(self) -> str:
        """Generate SQLAlchemy database URL for async SQLite."""
        return f"sqlite+aiosqlite:///{self.db_path}"
    
    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.log_path.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
settings.ensure_directories()
