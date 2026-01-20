"""
Log model for storing keystroke and screen capture data.

This model stores the actual exfiltrated data (keystrokes, screenshots,
clipboard content) extracted from malware C2 traffic.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class Log(Base):
    """
    SQLAlchemy model for exfiltrated keystroke and activity logs.
    
    Stores the actual malicious payload data (keystrokes, window titles,
    clipboard) extracted from decrypted C2 traffic for forensic analysis.
    """
    
    __tablename__ = "logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Association with Bot
    bot_id = Column(Integer, ForeignKey("bots.id"), nullable=False, index=True)
    
    # Log Classification
    log_type = Column(
        String(50),
        nullable=False,
        index=True,
        # Types: keystroke, clipboard, screenshot, file_upload, system_info
    )
    
    # Keystroke Data
    window_title = Column(String(500), nullable=True)  # Active window when keys pressed
    keystroke_data = Column(Text, nullable=True)  # Actual keystrokes
    
    # Additional Context
    application = Column(String(255), nullable=True)  # Target application
    url = Column(Text, nullable=True)  # URL if browser-based
    
    # Raw Data (for non-keystroke types)
    raw_data = Column(Text, nullable=True)  # Base64 screenshot, clipboard content, etc.
    
    # Metadata
    captured_at = Column(DateTime, nullable=True)  # Timestamp from malware
    received_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    def __repr__(self) -> str:
        return f"<Log(id={self.id}, bot_id={self.bot_id}, type={self.log_type})>"


# Pydantic Schemas

class LogBase(BaseModel):
    """Base schema for log entries."""
    bot_id: int = Field(..., description="Foreign key to associated bot")
    log_type: str = Field(..., description="Type of log (keystroke, clipboard, etc.)")
    window_title: Optional[str] = Field(None, description="Active window title")
    keystroke_data: Optional[str] = Field(None, description="Captured keystrokes")
    application: Optional[str] = Field(None, description="Target application name")
    url: Optional[str] = Field(None, description="Associated URL if applicable")
    raw_data: Optional[str] = Field(None, description="Raw payload data")
    captured_at: Optional[datetime] = Field(None, description="Timestamp from malware")


class LogCreate(LogBase):
    """Schema for creating a new log entry."""
    pass


class LogRead(LogBase):
    """Schema for reading log data from API."""
    id: int
    received_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True
