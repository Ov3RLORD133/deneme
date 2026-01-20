"""
Utility functions for protocol handlers.

Includes hexdump formatting, common cryptographic operations (XOR, RC4, AES),
and data parsing helpers for malware traffic analysis.
"""

from typing import List


def hexdump(data: bytes, length: int = 16, show_ascii: bool = True) -> str:
    """
    Generate a hexdump representation of binary data.
    
    Creates a formatted hexdump similar to the output of the Unix hexdump
    utility, showing offset, hex bytes, and ASCII representation.
    
    Args:
        data: Binary data to format
        length: Number of bytes per line (default: 16)
        show_ascii: Whether to show ASCII representation
        
    Returns:
        Formatted hexdump string
        
    Example:
        >>> hexdump(b"Hello World!")
        00000000  48 65 6c 6c 6f 20 57 6f  72 6c 64 21              |Hello World!|
    """
    if not data:
        return "(empty)"
    
    lines = []
    for i in range(0, len(data), length):
        chunk = data[i:i + length]
        
        # Offset
        offset = f"{i:08x}"
        
        # Hex bytes (split into two groups of 8)
        hex_part1 = " ".join(f"{b:02x}" for b in chunk[:8])
        hex_part2 = " ".join(f"{b:02x}" for b in chunk[8:])
        hex_part = f"{hex_part1:<23}  {hex_part2:<23}"
        
        # ASCII representation
        if show_ascii:
            ascii_part = "".join(
                chr(b) if 32 <= b < 127 else "."
                for b in chunk
            )
            lines.append(f"{offset}  {hex_part} |{ascii_part}|")
        else:
            lines.append(f"{offset}  {hex_part}")
    
    return "\n".join(lines)


def xor_decrypt(data: bytes, key: bytes) -> bytes:
    """
    XOR decryption with repeating key.
    
    Common encryption used by simple keyloggers and RATs.
    
    Args:
        data: Encrypted data
        key: XOR key (repeats if shorter than data)
        
    Returns:
        Decrypted bytes
        
    Example:
        >>> xor_decrypt(b"\\x1f\\x0e\\x1e\\x1e\\x00", b"KEY")
        b'HELLO'
    """
    if not key:
        raise ValueError("XOR key cannot be empty")
    
    key_len = len(key)
    return bytes(data[i] ^ key[i % key_len] for i in range(len(data)))


def rc4_decrypt(data: bytes, key: bytes) -> bytes:
    """
    RC4 stream cipher decryption.
    
    Used by many malware families including some versions of
    AgentTesla, Remcos, and NanoCore.
    
    Args:
        data: Encrypted data
        key: RC4 key
        
    Returns:
        Decrypted bytes
    """
    from Crypto.Cipher import ARC4
    
    cipher = ARC4.new(key)
    return cipher.decrypt(data)


def aes_decrypt(data: bytes, key: bytes, iv: bytes, mode: str = "CBC") -> bytes:
    """
    AES decryption with specified mode.
    
    Supports CBC and ECB modes commonly used in malware.
    
    Args:
        data: Encrypted data (must be multiple of 16 bytes)
        key: AES key (16, 24, or 32 bytes for AES-128/192/256)
        iv: Initialization vector (16 bytes, ignored for ECB)
        mode: Cipher mode ("CBC" or "ECB")
        
    Returns:
        Decrypted bytes (may need PKCS7 unpadding)
        
    Raises:
        ValueError: If key/IV size is invalid
    """
    from Crypto.Cipher import AES
    
    if mode.upper() == "CBC":
        cipher = AES.new(key, AES.MODE_CBC, iv)
    elif mode.upper() == "ECB":
        cipher = AES.new(key, AES.MODE_ECB)
    else:
        raise ValueError(f"Unsupported AES mode: {mode}")
    
    return cipher.decrypt(data)


def pkcs7_unpad(data: bytes) -> bytes:
    """
    Remove PKCS7 padding from decrypted data.
    
    Args:
        data: Padded data
        
    Returns:
        Unpadded data
        
    Raises:
        ValueError: If padding is invalid
    """
    if not data:
        raise ValueError("Cannot unpad empty data")
    
    padding_len = data[-1]
    
    if padding_len == 0 or padding_len > 16:
        raise ValueError(f"Invalid padding length: {padding_len}")
    
    # Verify padding is correct
    if data[-padding_len:] != bytes([padding_len] * padding_len):
        raise ValueError("Invalid PKCS7 padding")
    
    return data[:-padding_len]


def extract_delimited_strings(data: bytes, delimiter: bytes = b"\x00") -> List[str]:
    """
    Extract null-terminated or delimited strings from binary data.
    
    Common in malware payloads where multiple fields are separated
    by null bytes or other delimiters.
    
    Args:
        data: Binary data containing strings
        delimiter: Delimiter bytes (default: null byte)
        
    Returns:
        List of extracted strings
        
    Example:
        >>> extract_delimited_strings(b"user\\x00pass\\x00host\\x00")
        ['user', 'pass', 'host']
    """
    parts = data.split(delimiter)
    strings = []
    
    for part in parts:
        if part:
            try:
                # Try UTF-8 first
                strings.append(part.decode("utf-8", errors="ignore"))
            except Exception:
                # Fallback to latin-1
                strings.append(part.decode("latin-1", errors="ignore"))
    
    return strings


def parse_fixed_format(data: bytes, format_spec: List[tuple]) -> dict:
    """
    Parse binary data with fixed field offsets and lengths.
    
    Useful for malware protocols with structured binary formats.
    
    Args:
        data: Binary data to parse
        format_spec: List of (field_name, offset, length, type) tuples
                    type can be 'str', 'int', 'bytes'
        
    Returns:
        Dictionary mapping field names to values
        
    Example:
        >>> spec = [('magic', 0, 4, 'bytes'), ('length', 4, 2, 'int')]
        >>> parse_fixed_format(b"TEST\\x00\\x10...", spec)
        {'magic': b'TEST', 'length': 16}
    """
    result = {}
    
    for field_name, offset, length, field_type in format_spec:
        if offset + length > len(data):
            result[field_name] = None
            continue
        
        chunk = data[offset:offset + length]
        
        if field_type == "str":
            result[field_name] = chunk.decode("utf-8", errors="ignore").rstrip("\x00")
        elif field_type == "int":
            result[field_name] = int.from_bytes(chunk, byteorder="little")
        elif field_type == "bytes":
            result[field_name] = chunk
        else:
            result[field_name] = chunk
    
    return result
