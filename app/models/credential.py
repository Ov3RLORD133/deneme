"""
Credential model for storing stolen authentication data.

This model tracks credentials (passwords, tokens, cookies) extracted
from malware traffic for tracking credential theft campaigns.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class Credential(Base):
    """
    SQLAlchemy model for stolen credentials and authentication data.
    
    Stores passwords, tokens, cookies, and other authentication material
    extracted from malware payloads for breach analysis.
    """
    
    __tablename__ = "credentials"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Association with Bot
    bot_id = Column(Integer, ForeignKey("bots.id"), nullable=False, index=True)
    
    # Credential Type
    cred_type = Column(
        String(50),
        nullable=False,
        index=True,
        # Types: password, token, cookie, api_key, ssh_key, browser_saved
    )
    
    # Credential Details
    url = Column(Text, nullable=True)  # Associated website/service
    username = Column(String(255), nullable=True)
    password = Column(Text, nullable=True)
    
    # Additional Fields
    email = Column(String(255), nullable=True)
    application = Column(String(255), nullable=True)  # Source application (browser, FTP, etc.)
    
    # Token/Cookie Data
    token = Column(Text, nullable=True)
    cookie_data = Column(Text, nullable=True)
    
    # Metadata
    captured_at = Column(DateTime, nullable=True)
    received_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    def __repr__(self) -> str:
        return f"<Credential(id={self.id}, type={self.cred_type}, username={self.username})>"


# Pydantic Schemas

class CredentialBase(BaseModel):
    """Base schema for credential data."""
    bot_id: int = Field(..., description="Foreign key to associated bot")
    cred_type: str = Field(..., description="Credential type")
    url: Optional[str] = Field(None, description="Associated URL or service")
    username: Optional[str] = Field(None, description="Username or email")
    password: Optional[str] = Field(None, description="Password or secret")
    email: Optional[str] = Field(None, description="Email address")
    application: Optional[str] = Field(None, description="Source application")
    token: Optional[str] = Field(None, description="Authentication token")
    cookie_data: Optional[str] = Field(None, description="Cookie data")
    captured_at: Optional[datetime] = Field(None, description="Capture timestamp")


class CredentialCreate(CredentialBase):
    """Schema for creating a new credential record."""
    pass


class CredentialRead(CredentialBase):
    """Schema for reading credential data from API."""
    id: int
    received_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True
