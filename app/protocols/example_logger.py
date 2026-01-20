"""
Example keylogger protocol handler.

Demonstrates a simple malware protocol that uses XOR encryption
and sends keystrokes in a delimited format. This serves as a template
for implementing real malware family handlers.
"""

from datetime import datetime
from typing import Any, Dict

from app.core.logging import get_logger
from app.protocols.base import ProtocolHandler
from app.protocols.utils import extract_delimited_strings, xor_decrypt

logger = get_logger(__name__)


class ExampleLoggerHandler(ProtocolHandler):
    """
    Example keylogger protocol handler.
    
    Protocol Specification:
    - Port: 4444 (TCP)
    - Encryption: XOR with key "SecretKey123"
    - Format: DELIMITER-separated fields
      Fields: BOT_ID|HOSTNAME|USERNAME|OS|WINDOW|KEYSTROKES
    
    This is a demonstration protocol. Real malware protocols should
    have their own handler classes with proper reverse-engineered logic.
    """
    
    # XOR encryption key (hardcoded in this example malware)
    XOR_KEY = b"SecretKey123"
    
    @property
    def name(self) -> str:
        return "ExampleLogger"
    
    @property
    def port(self) -> int:
        return 4444
    
    async def decrypt(self, data: bytes) -> bytes:
        """
        Decrypt XOR-encrypted payload.
        
        Args:
            data: Encrypted payload from malware
            
        Returns:
            Decrypted plaintext
            
        Raises:
            ValueError: If data is too short or invalid
        """
        if len(data) < 4:
            raise ValueError(f"Payload too short: {len(data)} bytes")
        
        logger.debug(f"[{self.name}] Decrypting {len(data)} bytes with XOR")
        
        try:
            decrypted = xor_decrypt(data, self.XOR_KEY)
            return decrypted
        except Exception as e:
            raise ValueError(f"XOR decryption failed: {e}")
    
    async def parse(self, decrypted_data: bytes, client_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse decrypted payload into structured data.
        
        Expected Format:
            BOT_ID|HOSTNAME|USERNAME|OS_INFO|WINDOW_TITLE|KEYSTROKES
        
        Args:
            decrypted_data: Decrypted payload
            client_info: Client IP and port
            
        Returns:
            Dictionary with bot_info, logs, and credentials
        """
        try:
            # Decode to string
            payload_str = decrypted_data.decode("utf-8", errors="ignore").strip()
            logger.debug(f"[{self.name}] Decoded payload: {payload_str[:100]}...")
            
            # Split by delimiter (pipe symbol)
            fields = payload_str.split("|")
            
            if len(fields) < 6:
                raise ValueError(f"Invalid field count: expected 6, got {len(fields)}")
            
            bot_id, hostname, username, os_info, window_title, keystrokes = fields[:6]
            
            # Build bot information
            bot_info = {
                "ip_address": client_info["ip"],
                "port": client_info["port"],
                "protocol": self.name,
                "bot_id": bot_id or f"{client_info['ip']}_{self.port}",
                "hostname": hostname or None,
                "username": username or None,
                "os_info": os_info or None,
            }
            
            # Build log entry for keystrokes
            logs = []
            if keystrokes:
                log_entry = {
                    "log_type": "keystroke",
                    "window_title": window_title or "Unknown",
                    "keystroke_data": keystrokes,
                    "captured_at": datetime.utcnow(),
                }
                logs.append(log_entry)
                logger.info(f"[{self.name}] Captured keystrokes from {bot_id}: "
                          f"{keystrokes[:50]}...")
            
            # Check for credentials in keystrokes (basic pattern matching)
            credentials = self._extract_credentials(keystrokes, bot_id)
            
            return {
                "bot_info": bot_info,
                "logs": logs,
                "credentials": credentials,
            }
            
        except Exception as e:
            logger.error(f"[{self.name}] Parsing error: {e}")
            raise ValueError(f"Failed to parse payload: {e}")
    
    def _extract_credentials(self, keystrokes: str, bot_id: str) -> list:
        """
        Extract potential credentials from keystroke data.
        
        This is a simple heuristic-based extraction. In real scenarios,
        you would use more sophisticated pattern matching or ML models.
        
        Args:
            keystrokes: Keystroke string
            bot_id: Bot identifier
            
        Returns:
            List of credential dictionaries
        """
        credentials = []
        
        # Look for common patterns (very basic example)
        keywords = ["password:", "pwd:", "pass:", "login:"]
        
        for keyword in keywords:
            if keyword.lower() in keystrokes.lower():
                # Extract context around keyword (basic extraction)
                idx = keystrokes.lower().find(keyword)
                context = keystrokes[max(0, idx-20):min(len(keystrokes), idx+50)]
                
                cred = {
                    "cred_type": "password",
                    "raw_data": context,
                    "captured_at": datetime.utcnow(),
                }
                credentials.append(cred)
                logger.info(f"[{self.name}] Potential credential detected for {bot_id}")
                break  # Only extract first match
        
        return credentials
    
    async def generate_response(self, parsed_data: Dict[str, Any]) -> bytes:
        """
        Generate ACK response for malware.
        
        Some keyloggers expect a response to confirm receipt.
        
        Returns:
            Encrypted "OK" response
        """
        response = b"OK"
        # Encrypt response with same XOR key
        encrypted_response = xor_decrypt(response, self.XOR_KEY)  # XOR is symmetric
        return encrypted_response
