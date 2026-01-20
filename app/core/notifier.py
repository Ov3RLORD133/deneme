"""
Telegram Notification System for KeyChaser.

Sends real-time alerts to Telegram when critical events occur
(new infections, credential theft, YARA detections).
"""

import asyncio
from typing import Optional

import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


# Emoji mapping for notification levels
LEVEL_EMOJI = {
    "INFO": "\u2139\ufe0f",      # ℹ️ Information
    "WARNING": "\u26a0\ufe0f",   # ⚠️ Warning
    "ERROR": "\u274c",           # ❌ Error
    "CRITICAL": "\ud83d\udd25",  # 🔥 Fire
    "SUCCESS": "\u2705",         # ✅ Check mark
}


async def send_notification(
    title: str,
    message: str,
    level: str = "INFO"
) -> bool:
    """
    Send notification to Telegram.
    
    This function uses async HTTP requests to avoid blocking the main
    application flow. If Telegram is unavailable or credentials are wrong,
    it logs the error but does not crash.
    
    Args:
        title: Bold title for the notification
        message: Message body (supports HTML formatting)
        level: Severity level (INFO, WARNING, ERROR, CRITICAL, SUCCESS)
        
    Returns:
        True if notification sent successfully, False otherwise
        
    Example:
        await send_notification(
            title="New Infection",
            message="<b>IP:</b> 192.168.1.100",
            level="WARNING"
        )
    """
    # Check if Telegram is configured
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        logger.debug("Telegram notifications disabled (no credentials configured)")
        return False
    
    try:
        # Get emoji for level
        emoji = LEVEL_EMOJI.get(level.upper(), "\ud83d\udd14")  # 🔔 default
        
        # Construct formatted message
        formatted_text = f"{emoji} <b>{title}</b>\n\n{message}"
        
        # Telegram API URL
        url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
        
        # Payload
        payload = {
            "chat_id": settings.telegram_chat_id,
            "text": formatted_text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True  # Prevent URL previews
        }
        
        # Send async HTTP request with timeout
        async with httpx.AsyncClient() as client:
            response = await asyncio.wait_for(
                client.post(url, json=payload),
                timeout=5.0  # 5 second timeout
            )
            
            if response.status_code == 200:
                logger.info(f"Telegram notification sent: {level} - {title}")
                return True
            else:
                logger.warning(
                    f"Telegram API returned status {response.status_code}: "
                    f"{response.text}"
                )
                return False
                
    except asyncio.TimeoutError:
        logger.warning("Telegram notification timeout (API unreachable)")
        return False
    except httpx.HTTPError as e:
        logger.warning(f"Telegram HTTP error: {e}")
        return False
    except Exception as e:
        logger.error(f"Telegram notification failed: {e}")
        return False


async def send_credential_alert(
    bot_id: str,
    ip_address: str,
    cred_type: str,
    url: Optional[str] = None,
    count: int = 1
) -> bool:
    """
    Send alert for stolen credentials.
    
    Args:
        bot_id: Bot identifier
        ip_address: Source IP address
        cred_type: Type of credential (email, browser_password, etc.)
        url: Target URL (if applicable)
        count: Number of credentials stolen
        
    Returns:
        True if notification sent successfully
    """
    url_info = f"\n<b>URL:</b> {url}" if url else ""
    
    return await send_notification(
        title=f"\ud83d\udd11 Credentials Stolen ({count})",
        message=(
            f"<b>Type:</b> {cred_type}\n"
            f"<b>Bot:</b> {bot_id}\n"
            f"<b>IP:</b> {ip_address}"
            f"{url_info}"
        ),
        level="CRITICAL"
    )


async def send_yara_alert(
    ip_address: str,
    protocol: str,
    matched_rules: list[str]
) -> bool:
    """
    Send alert for YARA signature match.
    
    Args:
        ip_address: Source IP address
        protocol: Protocol name
        matched_rules: List of matched YARA rule names
        
    Returns:
        True if notification sent successfully
    """
    rules_list = "\n".join([f"• {rule}" for rule in matched_rules])
    
    return await send_notification(
        title="\ud83d\udea8 YARA Detection",
        message=(
            f"<b>IP:</b> {ip_address}\n"
            f"<b>Protocol:</b> {protocol}\n"
            f"<b>Matched Rules:</b>\n{rules_list}"
        ),
        level="CRITICAL"
    )


async def send_system_alert(message: str, level: str = "INFO") -> bool:
    """
    Send generic system alert.
    
    Args:
        message: Alert message
        level: Severity level
        
    Returns:
        True if notification sent successfully
    """
    return await send_notification(
        title="System Alert",
        message=message,
        level=level
    )
