"""
TEMPLATE: Protocol handler for a new malware family.

Copy this file to create handlers for real malware protocols.
Replace all TODOs and customize the implementation based on
reverse-engineering analysis.

STEPS TO CREATE A HANDLER:
1. Copy this file to app/protocols/<malware_name>.py
2. Update the class name, protocol name, and port
3. Implement decrypt() with the malware's encryption
4. Implement parse() to extract bot info, logs, and credentials
5. Enable in configuration: KEYCHASER_ENABLED_PROTOCOLS
"""

from datetime import datetime
from typing import Any, Dict

from app.core.logging import get_logger
from app.protocols.base import ProtocolHandler
from app.protocols.utils import (
    aes_decrypt,
    extract_delimited_strings,
    hexdump,
    parse_fixed_format,
    pkcs7_unpad,
    rc4_decrypt,
    xor_decrypt,
)

logger = get_logger(__name__)


class TemplateHandler(ProtocolHandler):
    """
    Protocol handler for [MALWARE_NAME].
    
    TODO: Add detailed description of the malware family, typical behavior,
    and any relevant IOCs or campaign information.
    
    Protocol Specification:
    - Port: [PORT] (TCP/UDP)
    - Encryption: [ALGORITHM] with key [KEY_INFO]
    - Packet Format: [DESCRIPTION]
    - Malware Family: [FAMILY_NAME]
    - Known Variants: [VARIANTS]
    
    References:
    - [Link to analysis blog post]
    - [Link to MITRE ATT&CK entry]
    - [Link to VirusTotal report]
    """
    
    # TODO: Set encryption parameters discovered during reverse engineering
    ENCRYPTION_KEY = b"TODO_SET_KEY"  # XOR key, RC4 key, or AES key
    AES_IV = b"TODO_SET_IV_IF_AES" if False else None  # Set if using AES
    
    @property
    def name(self) -> str:
        """Return protocol/malware family name."""
        return "TODO_MalwareName"  # e.g., "AgentTesla", "RedLine", "Raccoon"
    
    @property
    def port(self) -> int:
        """Return listening port."""
        return 9999  # TODO: Set actual port used by malware
    
    @property
    def use_udp(self) -> bool:
        """Return True if protocol uses UDP instead of TCP."""
        return False  # TODO: Change to True if malware uses UDP
    
    async def decrypt(self, data: bytes) -> bytes:
        """
        Decrypt malware C2 payload.
        
        TODO: Implement the specific decryption algorithm used by this
        malware family. Common options:
        - XOR with static or dynamic key
        - RC4 stream cipher
        - AES-128/256 in CBC or ECB mode
        - Custom algorithms (reverse engineer carefully)
        
        Args:
            data: Encrypted payload from malware
            
        Returns:
            Decrypted plaintext bytes
            
        Raises:
            ValueError: If decryption fails or data is malformed
        """
        if len(data) < 16:  # TODO: Set minimum expected packet size
            raise ValueError(f"Packet too short: {len(data)} bytes")
        
        logger.debug(f"[{self.name}] Decrypting {len(data)} bytes")
        
        try:
            # TODO: Choose appropriate decryption method
            
            # Option 1: XOR Decryption
            decrypted = xor_decrypt(data, self.ENCRYPTION_KEY)
            
            # Option 2: RC4 Decryption
            # decrypted = rc4_decrypt(data, self.ENCRYPTION_KEY)
            
            # Option 3: AES-CBC Decryption
            # decrypted = aes_decrypt(data, self.ENCRYPTION_KEY, self.AES_IV, mode="CBC")
            # decrypted = pkcs7_unpad(decrypted)  # Remove padding
            
            # Option 4: AES-ECB Decryption
            # decrypted = aes_decrypt(data, self.ENCRYPTION_KEY, b"", mode="ECB")
            # decrypted = pkcs7_unpad(decrypted)
            
            # Option 5: Custom Decryption
            # decrypted = self._custom_decrypt(data)
            
            logger.debug(f"[{self.name}] Decryption successful")
            return decrypted
            
        except Exception as e:
            logger.error(f"[{self.name}] Decryption failed: {e}")
            raise ValueError(f"Decryption error: {e}")
    
    async def parse(self, decrypted_data: bytes, client_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse decrypted payload into structured data.
        
        TODO: Implement parsing logic based on the malware's data format.
        Extract:
        - Bot identification (unique ID, HWID, etc.)
        - Victim system information (hostname, username, OS)
        - Keystroke logs
        - Stolen credentials (browser, FTP, email, etc.)
        - Screenshots or clipboard data
        - Any other exfiltrated data
        
        Args:
            decrypted_data: Decrypted payload bytes
            client_info: Dictionary with 'ip' and 'port' of client
            
        Returns:
            Dictionary containing:
                - bot_info: Bot metadata dict
                - logs: List of log entry dicts
                - credentials: List of credential dicts
                
        Raises:
            ValueError: If parsing fails
        """
        try:
            # TODO: Analyze the decrypted payload structure and implement parsing
            
            # PARSING STRATEGY 1: Delimited Fields (common format)
            # Example: "BOT_ID|HOSTNAME|USERNAME|OS|DATA"
            fields = extract_delimited_strings(decrypted_data, b"|")
            
            if len(fields) < 4:  # TODO: Set minimum expected field count
                raise ValueError(f"Invalid field count: {len(fields)}")
            
            bot_id = fields[0]
            hostname = fields[1]
            username = fields[2]
            os_info = fields[3]
            # ... extract additional fields
            
            # PARSING STRATEGY 2: Fixed Binary Format
            # Example: 4 bytes magic, 4 bytes length, 16 bytes bot_id, etc.
            # format_spec = [
            #     ('magic', 0, 4, 'bytes'),
            #     ('length', 4, 4, 'int'),
            #     ('bot_id', 8, 16, 'str'),
            #     ('hostname', 24, 64, 'str'),
            # ]
            # parsed = parse_fixed_format(decrypted_data, format_spec)
            # bot_id = parsed['bot_id']
            # hostname = parsed['hostname']
            
            # PARSING STRATEGY 3: JSON/XML Payload
            # import json
            # payload_dict = json.loads(decrypted_data.decode('utf-8'))
            # bot_id = payload_dict['bot_id']
            # ...
            
            # Build bot information dictionary
            bot_info = {
                "ip_address": client_info["ip"],
                "port": client_info["port"],
                "protocol": self.name,
                "bot_id": bot_id or f"{client_info['ip']}_{self.port}",
                "hostname": hostname or None,
                "username": username or None,
                "os_info": os_info or None,
                # TODO: Add malware-specific fields
                # "malware_version": version,
                # "campaign_id": campaign,
                # "extra_data": json.dumps(additional_data),
            }
            
            # Extract keystroke logs
            logs = []
            # TODO: Parse keystroke data from payload
            # Example:
            # if len(fields) > 4:
            #     keystroke_data = fields[4]
            #     log_entry = {
            #         "log_type": "keystroke",
            #         "window_title": fields[5] if len(fields) > 5 else "Unknown",
            #         "keystroke_data": keystroke_data,
            #         "captured_at": datetime.utcnow(),
            #     }
            #     logs.append(log_entry)
            
            # Extract credentials
            credentials = []
            # TODO: Parse credential data (passwords, cookies, tokens)
            # Example:
            # if "password:" in keystroke_data.lower():
            #     cred = {
            #         "cred_type": "password",
            #         "url": extract_url(keystroke_data),
            #         "username": extract_username(keystroke_data),
            #         "password": extract_password(keystroke_data),
            #         "captured_at": datetime.utcnow(),
            #     }
            #     credentials.append(cred)
            
            logger.info(f"[{self.name}] Parsed data from {bot_id}: "
                       f"{len(logs)} logs, {len(credentials)} credentials")
            
            return {
                "bot_info": bot_info,
                "logs": logs,
                "credentials": credentials,
            }
            
        except Exception as e:
            logger.error(f"[{self.name}] Parsing error: {e}")
            # Log hexdump for debugging
            logger.debug(f"[{self.name}] Failed to parse data:\n{hexdump(decrypted_data)}")
            raise ValueError(f"Parse error: {e}")
    
    async def generate_response(self, parsed_data: Dict[str, Any]) -> bytes | None:
        """
        Generate response to send back to malware (optional).
        
        Some malware expects specific responses:
        - ACK messages
        - Commands (download, execute, update)
        - Status codes
        
        TODO: Implement if malware expects a response. Otherwise return None.
        
        Args:
            parsed_data: Parsed data dictionary
            
        Returns:
            Response bytes or None
        """
        # TODO: Implement if needed
        
        # Example 1: Simple ACK
        # response = b"OK"
        # return xor_encrypt(response, self.ENCRYPTION_KEY)
        
        # Example 2: Status code
        # return struct.pack("<I", 0x00000001)  # Success code
        
        # Example 3: No response needed
        return None
    
    # TODO: Add any custom helper methods needed for this malware
    
    def _custom_decrypt(self, data: bytes) -> bytes:
        """
        Custom decryption algorithm (if needed).
        
        Implement this if the malware uses a non-standard encryption
        algorithm that isn't covered by the utility functions.
        """
        # TODO: Implement custom decryption
        pass
    
    def _extract_credentials(self, text: str) -> list:
        """
        Extract credentials from text using pattern matching.
        
        TODO: Customize patterns for this malware's data format.
        """
        credentials = []
        
        # Example patterns (customize based on malware)
        patterns = {
            "email": r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)",
            "url": r"https?://[^\s]+",
            "password_field": r"password[:\s]+([^\s]+)",
        }
        
        # TODO: Implement pattern matching
        import re
        for pattern_name, regex in patterns.items():
            matches = re.findall(regex, text, re.IGNORECASE)
            for match in matches:
                # Store found credential
                pass
        
        return credentials


# TODO: After implementing:
# 1. Test with real malware samples in isolated environment
# 2. Verify decryption with known samples
# 3. Add to KEYCHASER_ENABLED_PROTOCOLS
# 4. Monitor logs for errors during live operation
# 5. Document findings for threat intelligence
