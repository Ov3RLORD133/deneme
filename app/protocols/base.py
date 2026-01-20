"""
Abstract base class for malware protocol handlers.

All protocol handlers must inherit from ProtocolHandler and implement
the required abstract methods for decryption, parsing, and connection handling.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger, get_traffic_logger

logger = get_logger(__name__)
traffic_logger = get_traffic_logger()


class ProtocolHandler(ABC):
    """
    Abstract base class for malware protocol handlers.
    
    Each malware family (e.g., AgentTesla, RedLine) should have its own
    handler that extends this class and implements protocol-specific
    decryption and parsing logic.
    
    Attributes:
        name: Human-readable protocol name
        port: TCP/UDP port to listen on
        use_udp: Whether to use UDP instead of TCP
    """
    
    def __init__(self, db_session_factory):
        """
        Initialize protocol handler.
        
        Args:
            db_session_factory: Async session factory for database operations
        """
        self.db_session_factory = db_session_factory
        self.active_connections: Dict[str, int] = {}  # IP -> connection count
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the human-readable protocol name."""
        pass
    
    @property
    @abstractmethod
    def port(self) -> int:
        """Return the port number this protocol listens on."""
        pass
    
    @property
    def use_udp(self) -> bool:
        """Return True if this protocol uses UDP instead of TCP."""
        return False
    
    @abstractmethod
    async def decrypt(self, data: bytes) -> bytes:
        """
        Decrypt malware C2 payload.
        
        Implement the specific decryption algorithm (XOR, RC4, AES, etc.)
        used by this malware family.
        
        Args:
            data: Encrypted payload from malware
            
        Returns:
            Decrypted plaintext bytes
            
        Raises:
            ValueError: If decryption fails or data is invalid
        """
        pass
    
    @abstractmethod
    async def parse(self, decrypted_data: bytes) -> Dict[str, Any]:
        """
        Parse decrypted payload into structured data.
        
        Extract bot information, keystrokes, credentials, etc. from the
        decrypted payload based on the malware's data format.
        
        Args:
            decrypted_data: Decrypted payload bytes
            
        Returns:
            Dictionary containing:
                - bot_info: Dict with bot metadata (bot_id, hostname, etc.)
                - logs: List of log entries (keystrokes, etc.)
                - credentials: List of credential dictionaries
                
        Raises:
            ValueError: If parsing fails or format is invalid
        """
        pass
    
    async def handle_connection(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter
    ) -> None:
        """
        Handle incoming TCP connection from malware.
        
        This is the main entry point called by asyncio.start_server().
        Orchestrates receiving data, decryption, parsing, and storage.
        
        Args:
            reader: StreamReader for reading from socket
            writer: StreamWriter for writing to socket
        """
        client_addr = writer.get_extra_info('peername')
        client_ip = client_addr[0] if client_addr else "unknown"
        client_port = client_addr[1] if client_addr else 0
        
        logger.info(f"[{self.name}] New connection from {client_ip}:{client_port}")
        
        # Connection rate limiting
        if not self._check_rate_limit(client_ip):
            logger.warning(f"[{self.name}] Rate limit exceeded for {client_ip}")
            writer.close()
            await writer.wait_closed()
            return
        
        try:
            # Read data from malware
            raw_data = await asyncio.wait_for(
                reader.read(65536),  # Max 64KB
                timeout=30.0
            )
            
            if not raw_data:
                logger.warning(f"[{self.name}] Empty data from {client_ip}")
                return
            
            logger.info(f"[{self.name}] Received {len(raw_data)} bytes from {client_ip}")
            
            # Log raw traffic
            from app.protocols.utils import hexdump
            traffic_logger.info(f"\n[{self.name}] RAW DATA from {client_ip}:\n{hexdump(raw_data)}")
            
            # Decrypt payload
            try:
                decrypted_data = await self.decrypt(raw_data)
                traffic_logger.info(f"\n[{self.name}] DECRYPTED DATA from {client_ip}:\n{hexdump(decrypted_data)}")
            except Exception as e:
                logger.error(f"[{self.name}] Decryption failed for {client_ip}: {e}")
                return
            
            # Parse into structured data
            try:
                parsed_data = await self.parse(decrypted_data)
                # Add client info to bot_info
                if "bot_info" not in parsed_data:
                    parsed_data["bot_info"] = {}
                parsed_data["bot_info"]["ip_address"] = client_ip
                parsed_data["bot_info"]["port"] = client_port
                parsed_data["bot_info"]["protocol"] = self.name
            except Exception as e:
                logger.error(f"[{self.name}] Parsing failed for {client_ip}: {e}")
                return
            
            # Store in database
            await self._store_data(parsed_data)
            
            logger.info(f"[{self.name}] Successfully processed data from {client_ip}")
            
            # Send response if needed (some malware expects ACK)
            response = await self.generate_response(parsed_data)
            if response:
                writer.write(response)
                await writer.drain()
            
        except asyncio.TimeoutError:
            logger.warning(f"[{self.name}] Connection timeout from {client_ip}")
        except Exception as e:
            logger.error(f"[{self.name}] Error handling connection from {client_ip}: {e}", exc_info=True)
        finally:
            self._release_rate_limit(client_ip)
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass
    
    async def generate_response(self, parsed_data: Dict[str, Any]) -> Optional[bytes]:
        """
        Generate response to send back to malware.
        
        Some malware expects an ACK or command response. Override this
        method if the protocol requires a response.
        
        Args:
            parsed_data: Parsed data dictionary
            
        Returns:
            Response bytes or None
        """
        return None
    
    def _check_rate_limit(self, ip: str) -> bool:
        """Check if IP is within connection rate limit."""
        from app.core.config import settings
        current = self.active_connections.get(ip, 0)
        if current >= settings.max_connections_per_ip:
            return False
        self.active_connections[ip] = current + 1
        return True
    
    def _release_rate_limit(self, ip: str) -> None:
        """Release connection slot for IP."""
        if ip in self.active_connections:
            self.active_connections[ip] -= 1
            if self.active_connections[ip] <= 0:
                del self.active_connections[ip]
    
    async def _store_data(self, parsed_data: Dict[str, Any]) -> None:
        """
        Store parsed data in database and broadcast WebSocket events.
        
        Args:
            parsed_data: Dictionary with bot_info, logs, and credentials
        """
        from app.models.bot import Bot
        from app.models.credential import Credential
        from app.models.log import Log
        from app.core.websocket import get_connection_manager
        from sqlalchemy import select
        
        manager = get_connection_manager()
        
        async with self.db_session_factory() as session:
            try:
                # Store or update bot information
                bot_info = parsed_data.get("bot_info", {})
                if bot_info:
                    # Set default location values (no GeoIP lookup)
                    bot_info.update({
                        "country": "Unknown Network",
                        "country_code": "XX",
                        "city": "Unknown City",
                        "latitude": "0.0",
                        "longitude": "0.0",
                        "continent": None,
                        "timezone": None,
                    })
                    
                    # Check if bot exists
                    result = await session.execute(
                        select(Bot).where(Bot.bot_id == bot_info.get("bot_id"))
                    )
                    bot = result.scalar_one_or_none()
                    
                    is_new_bot = False
                    if bot:
                        # Update last_seen timestamp
                        bot.last_seen = datetime.utcnow()
                        logger.info(f"Updated existing bot: {bot.bot_id}")
                    else:
                        # Create new bot
                        bot = Bot(**bot_info)
                        session.add(bot)
                        await session.flush()  # Get bot.id
                        logger.info(f"Created new bot: {bot.bot_id}")
                        is_new_bot = True
                    
                    bot_db_id = bot.id
                    
                    # Broadcast new beacon event
                    if is_new_bot:
                        await manager.broadcast("new_beacon", {
                            "bot_id": bot.id,
                            "ip_address": bot.ip_address,
                            "protocol": bot.protocol,
                            "hostname": bot.hostname,
                            "country": bot.country,
                            "country_code": bot.country_code
                        })
                    
                    # Store logs (keystrokes, etc.)
                    for log_entry in parsed_data.get("logs", []):
                        log_entry["bot_id"] = bot_db_id
                        log = Log(**log_entry)
                        session.add(log)
                        
                        # Broadcast new log event
                        await manager.broadcast("new_log", {
                            "log_id": log.id if hasattr(log, 'id') else None,
                            "bot_id": bot_db_id,
                            "log_type": log_entry.get("log_type"),
                            "preview": str(log_entry.get("keystroke_data", ""))[:100]
                        })
                    
                    # Store credentials
                    for cred_entry in parsed_data.get("credentials", []):
                        cred_entry["bot_id"] = bot_db_id
                        credential = Credential(**cred_entry)
                        session.add(credential)
                        
                        # Broadcast credential event
                        await manager.broadcast("new_credential", {
                            "credential_id": credential.id if hasattr(credential, 'id') else None,
                            "bot_id": bot_db_id,
                            "cred_type": cred_entry.get("cred_type"),
                            "url": cred_entry.get("url")
                        })
                    
                    await session.commit()
                    logger.info(f"Stored {len(parsed_data.get('logs', []))} logs and "
                              f"{len(parsed_data.get('credentials', []))} credentials")
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Database storage error: {e}", exc_info=True)
                raise


# Import datetime for _store_data
from datetime import datetime
