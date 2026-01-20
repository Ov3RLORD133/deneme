"""
Bot model representing infected machines connecting to the sinkhole.

Each bot record tracks a unique malware infection including victim
system information, malware family, and connection metadata.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class Bot(Base):
    """
    SQLAlchemy model for infected bot/victim machines.
    
    Tracks malware infections that beacon to the sinkhole, storing
    system fingerprints and infection metadata for analysis.
    """
    
    __tablename__ = "bots"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Network Information
    ip_address = Column(String(45), nullable=False, index=True)  # IPv4/IPv6
    port = Column(Integer, nullable=False)
    protocol = Column(String(50), nullable=False, index=True)  # Malware family
    
    # Victim System Information
    bot_id = Column(String(255), unique=True, index=True)  # Unique malware-assigned ID
    hostname = Column(String(255), nullable=True)
    username = Column(String(255), nullable=True)
    os_info = Column(String(255), nullable=True)
    
    # Malware Metadata
    malware_version = Column(String(50), nullable=True)
    campaign_id = Column(String(100), nullable=True, index=True)
    
    # Additional Data (JSON-serializable system info)
    extra_data = Column(Text, nullable=True)
    
    # Timestamps
    first_seen = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_seen = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    def __repr__(self) -> str:
        return f"<Bot(id={self.id}, bot_id={self.bot_id}, ip={self.ip_address}, protocol={self.protocol})>"


# Pydantic Schemas for API validation

class BotBase(BaseModel):
    """Base schema with common bot fields."""
    ip_address: str = Field(..., description="IP address of infected machine")
    port: int = Field(..., ge=1, le=65535, description="Connection port")
    protocol: str = Field(..., description="Malware protocol/family name")
    bot_id: Optional[str] = Field(None, description="Unique bot identifier from malware")
    hostname: Optional[str] = Field(None, description="Victim hostname")
    username: Optional[str] = Field(None, description="Victim username")
    os_info: Optional[str] = Field(None, description="Operating system information")
    malware_version: Optional[str] = Field(None, description="Malware version string")
    campaign_id: Optional[str] = Field(None, description="Campaign/builder identifier")
    extra_data: Optional[str] = Field(None, description="Additional JSON data")


class BotCreate(BotBase):
    """Schema for creating a new bot record."""
    pass


class BotRead(BotBase):
    """Schema for reading bot data from API."""
    id: int
    first_seen: datetime
    last_seen: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True
