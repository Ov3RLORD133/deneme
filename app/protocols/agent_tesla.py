"""
AgentTesla Protocol Handler

Decodes and parses AgentTesla malware exfiltration data.

AgentTesla is a commercial keylogger/RAT that exfiltrates via:
- SMTP (sends HTML emails with stolen data)
- HTTP POST (sends form data)
- FTP (uploads text files)

This handler implements SMTP/HTTP interception and credential extraction.
"""

import re
import base64
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from app.protocols.base import ProtocolHandler
from app.protocols.utils import extract_delimited_strings
from app.core.logging import get_logger

logger = get_logger(__name__)


class AgentTeslaHandler(ProtocolHandler):
    """
    Handler for AgentTesla malware C2 traffic.
    
    AgentTesla sends data in HTML format via SMTP or HTTP POST.
    Format:
        <html><body>
        <b>Time:</b> 2026-01-20 14:30:45<br>
        <b>User Name:</b> VICTIM-PC\\john.doe<br>
        <b>Computer Name:</b> VICTIM-PC<br>
        <b>OSFullName:</b> Microsoft Windows 10 Pro<br>
        <b>CPU:</b> Intel Core i7<br>
        <b>RAM:</b> 16GB<br>
        <b>IP Address:</b> 192.168.1.100<br>
        <b>Screen:</b> Screenshot.png [Base64]<br>
        <b>Clipboard:</b> password123<br>
        <b>Passwords:</b>
        URL: https://gmail.com
        Username: victim@example.com
        Password: MyP@ssw0rd123
        Application: Chrome
        </body></html>
    """
    
    @property
    def name(self) -> str:
        return "AgentTesla"
    
    @property
    def port(self) -> int:
        return 5555  # Custom port for AgentTesla simulation
    
    # Regex patterns for data extraction
    PATTERNS = {
        'time': re.compile(r'<b>Time:</b>\s*([^<]+)', re.IGNORECASE),
        'username': re.compile(r'<b>User Name:</b>\s*([^<]+)', re.IGNORECASE),
        'computer_name': re.compile(r'<b>Computer Name:</b>\s*([^<]+)', re.IGNORECASE),
        'os': re.compile(r'<b>OSFullName:</b>\s*([^<]+)', re.IGNORECASE),
        'cpu': re.compile(r'<b>CPU:</b>\s*([^<]+)', re.IGNORECASE),
        'ram': re.compile(r'<b>RAM:</b>\s*([^<]+)', re.IGNORECASE),
        'ip': re.compile(r'<b>IP Address:</b>\s*([^<]+)', re.IGNORECASE),
        'clipboard': re.compile(r'<b>Clipboard:</b>\s*([^<]+)', re.IGNORECASE),
    }
    
    # Password block extraction
    PASSWORD_BLOCK = re.compile(
        r'<b>Passwords:</b>(.*?)(?:</body>|<b>)',
        re.DOTALL | re.IGNORECASE
    )
    
    # Individual password entry
    PASSWORD_ENTRY = re.compile(
        r'URL:\s*(.+?)\s*Username:\s*(.+?)\s*Password:\s*(.+?)(?:\s*Application:\s*(.+?))?(?:\n|<br>|$)',
        re.DOTALL
    )
    
    async def decrypt(self, data: bytes) -> bytes:
        """
        AgentTesla typically sends data in plain HTML or base64-encoded.
        
        This implementation handles:
        1. Plain HTML data
        2. Base64-encoded HTML
        3. SMTP envelope parsing (extracts body from SMTP DATA command)
        """
        try:
            # Try decoding as UTF-8 first
            decoded = data.decode('utf-8', errors='ignore')
            
            # Check if it's SMTP traffic (contains SMTP commands)
            if 'MAIL FROM:' in decoded or 'RCPT TO:' in decoded:
                # Extract email body from SMTP DATA command
                data_match = re.search(r'DATA\r?\n(.+?)\r?\n\.\r?\n', decoded, re.DOTALL)
                if data_match:
                    decoded = data_match.group(1)
            
            # Check if body is base64 encoded
            if not '<html>' in decoded.lower():
                try:
                    decoded = base64.b64decode(decoded).decode('utf-8', errors='ignore')
                except Exception:
                    pass  # Not base64, use as is
            
            return decoded.encode('utf-8')
            
        except Exception as e:
            logger.error(f"[{self.name}] Decryption failed: {e}")
            return data  # Return original if decryption fails
    
    async def parse(self, decrypted_data: bytes) -> Dict:
        """
        Parse AgentTesla HTML exfiltration data.
        
        Returns:
            {
                'bot_id': 'VICTIM-PC',
                'hostname': 'VICTIM-PC',
                'username': 'john.doe',
                'os_info': 'Microsoft Windows 10 Pro',
                'system_info': {
                    'cpu': 'Intel Core i7',
                    'ram': '16GB',
                    'internal_ip': '192.168.1.100'
                },
                'logs': [
                    {
                        'log_type': 'system_info',
                        'data': '...'
                    },
                    {
                        'log_type': 'clipboard',
                        'data': 'password123'
                    }
                ],
                'credentials': [
                    {
                        'url': 'https://gmail.com',
                        'username': 'victim@example.com',
                        'password': 'MyP@ssw0rd123',
                        'application': 'Chrome'
                    }
                ]
            }
        """
        try:
            html_data = decrypted_data.decode('utf-8', errors='ignore')
            
            result = {
                'bot_id': None,
                'hostname': None,
                'username': None,
                'os_info': None,
                'system_info': {},
                'logs': [],
                'credentials': []
            }
            
            # Extract basic system information
            for field, pattern in self.PATTERNS.items():
                match = pattern.search(html_data)
                if match:
                    value = match.group(1).strip()
                    
                    if field == 'computer_name':
                        result['hostname'] = value
                        result['bot_id'] = value
                    elif field == 'username':
                        result['username'] = value
                    elif field == 'os':
                        result['os_info'] = value
                    elif field == 'clipboard':
                        # Log clipboard data
                        result['logs'].append({
                            'log_type': 'clipboard',
                            'data': value,
                            'captured_at': datetime.utcnow().isoformat()
                        })
                    else:
                        result['system_info'][field] = value
            
            # Create system info log entry
            if result['system_info']:
                result['logs'].append({
                    'log_type': 'system_info',
                    'data': str(result['system_info']),
                    'captured_at': datetime.utcnow().isoformat()
                })
            
            # Extract credentials from password block
            password_block_match = self.PASSWORD_BLOCK.search(html_data)
            if password_block_match:
                password_block = password_block_match.group(1)
                
                # Find all password entries
                for entry_match in self.PASSWORD_ENTRY.finditer(password_block):
                    url = entry_match.group(1).strip()
                    username = entry_match.group(2).strip()
                    password = entry_match.group(3).strip()
                    application = entry_match.group(4).strip() if entry_match.group(4) else None
                    
                    result['credentials'].append({
                        'cred_type': 'password',
                        'url': url if url and url != '-' else None,
                        'username': username if username else None,
                        'password': password if password else None,
                        'application': application,
                        'captured_at': datetime.utcnow().isoformat()
                    })
            
            # Additional credential extraction from plain text patterns
            # (for cases where HTML formatting is broken)
            additional_creds = self._extract_plaintext_credentials(html_data)
            result['credentials'].extend(additional_creds)
            
            logger.info(
                f"[{self.name}] Parsed data: "
                f"Bot={result['bot_id']}, "
                f"Logs={len(result['logs'])}, "
                f"Credentials={len(result['credentials'])}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"[{self.name}] Parse error: {e}")
            return {
                'bot_id': None,
                'hostname': None,
                'username': None,
                'os_info': None,
                'logs': [],
                'credentials': []
            }
    
    def _extract_plaintext_credentials(self, data: str) -> List[Dict]:
        """
        Extract credentials from plain text using pattern matching.
        
        Looks for common patterns:
        - URL: ... Username: ... Password: ...
        - login: username pass: password
        - email@example.com:password123
        """
        credentials = []
        
        # Pattern 1: URL/Username/Password format
        pattern1 = re.compile(
            r'(?:URL|Site|Website):\s*(.+?)\s+'
            r'(?:User|Username|Email):\s*(.+?)\s+'
            r'(?:Pass|Password|Pwd):\s*(.+?)(?:\n|$)',
            re.IGNORECASE
        )
        
        for match in pattern1.finditer(data):
            credentials.append({
                'cred_type': 'password',
                'url': match.group(1).strip(),
                'username': match.group(2).strip(),
                'password': match.group(3).strip(),
                'application': None,
                'captured_at': datetime.utcnow().isoformat()
            })
        
        # Pattern 2: email:password format
        pattern2 = re.compile(
            r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}):([^\s]+)',
            re.IGNORECASE
        )
        
        for match in pattern2.finditer(data):
            credentials.append({
                'cred_type': 'password',
                'url': None,
                'username': match.group(1).strip(),
                'email': match.group(1).strip(),
                'password': match.group(2).strip(),
                'application': None,
                'captured_at': datetime.utcnow().isoformat()
            })
        
        return credentials
    
    async def generate_response(self, parsed_data: Dict) -> bytes:
        """
        Generate response to AgentTesla beacon.
        
        AgentTesla expects:
        - SMTP: "250 OK" response
        - HTTP: "200 OK" with empty body
        """
        # SMTP-style response
        response = "250 OK\r\n"
        return response.encode('utf-8')
