# KeyChaser - Quick Start Guide

## 🎯 What You Just Built

KeyChaser is a **production-ready malware C2 sinkhole** with:

✅ **Modular Protocol System** - Drop-in handlers for different malware families  
✅ **Real-time Dashboard** - Dark-themed UI showing live infections  
✅ **Async Architecture** - Handle 1000s of concurrent connections  
✅ **Full Crypto Support** - XOR, RC4, AES decryption built-in  
✅ **SQLite Database** - Portable storage for forensic analysis  
✅ **Traffic Hexdumps** - Raw packet inspection for reverse engineering  

---

## 🚀 Running KeyChaser

### Option 1: Direct Python Execution

```bash
# Navigate to project directory
cd C:\Users\hamza\Downloads\codeShit\project\KeyChaser

# Activate virtual environment (if not active)
.venv\Scripts\activate

# Run the sinkhole
python -m app.main
```

**Expected Output:**
```
============================================================
KeyChaser - Malware C2 Sinkhole Starting...
============================================================
INFO | Initializing database schema...
INFO | Database schema initialized successfully
INFO | Loaded protocol handler: ExampleLogger on port 4444
INFO | Loaded 1 protocol handler(s)
============================================================
Dashboard available at http://0.0.0.0:8000
KeyChaser is ready to intercept malware traffic!
============================================================
INFO | [ExampleLogger] Listening on 0.0.0.0:4444
INFO | Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### Option 2: Docker Deployment

```bash
# Build and run with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f keychaser

# Stop
docker-compose down
```

---

## 🧪 Testing with Simulated Malware

Run the included test script to simulate a malware beacon:

```bash
python test_beacon.py
```

**What it does:**
1. Connects to port 4444 (ExampleLogger protocol)
2. Sends XOR-encrypted keystroke data
3. Simulates captured credentials (Gmail login)
4. Receives ACK response from sinkhole

**Expected Output:**
```
[*] KeyChaser Test Client
[*] Connecting to localhost:4444...
[+] Connected to sinkhole!
[*] Sending 141 bytes of encrypted data...
[+] Data sent!
[+] Received response: OK
[+] Connection closed

[*] Test complete! Check the KeyChaser dashboard at http://localhost:8000
```

---

## 📊 Accessing the Dashboard

Open your browser to: **http://localhost:8000**

### Dashboard Features

**Statistics Cards:**
- Total Bots (infected machines)
- Active Bots (last hour)
- Keystrokes Captured
- Credentials Stolen
- Active Protocols

**Recent Infections Table:**
- Bot ID
- IP Address
- Protocol/Malware Family
- Hostname
- Last Seen timestamp

**Recent Keystrokes Table:**
- Window Title (where keys were typed)
- Keystroke Data (captured keys)
- Bot ID reference
- Capture timestamp

**Auto-refresh:** Dashboard updates every 5 seconds automatically

---

## 🔌 Adding New Malware Protocols

### Step 1: Create Protocol Handler

Create `app/protocols/your_malware.py`:

```python
from app.protocols.base import ProtocolHandler
from app.protocols.utils import rc4_decrypt, extract_delimited_strings

class YourMalwareHandler(ProtocolHandler):
    """Handler for YourMalware keylogger."""
    
    @property
    def name(self) -> str:
        return "YourMalware"
    
    @property
    def port(self) -> int:
        return 5555  # Port malware connects to
    
    async def decrypt(self, data: bytes) -> bytes:
        """Decrypt payload using RC4."""
        return rc4_decrypt(data, b"MalwareKey")
    
    async def parse(self, decrypted_data: bytes, client_info: dict) -> dict:
        """Parse decrypted payload."""
        # Your parsing logic here
        fields = extract_delimited_strings(decrypted_data, b"\x00")
        
        return {
            "bot_info": {
                "ip_address": client_info["ip"],
                "port": client_info["port"],
                "protocol": self.name,
                "bot_id": fields[0],
                "hostname": fields[1],
                "username": fields[2],
            },
            "logs": [
                {
                    "log_type": "keystroke",
                    "keystroke_data": fields[3],
                }
            ],
            "credentials": [],
        }
```

### Step 2: Enable Protocol

Edit `.env` or set environment variable:

```bash
KEYCHASER_ENABLED_PROTOCOLS=["example_logger","your_malware"]
```

### Step 3: Restart KeyChaser

The new handler will automatically load and listen on port 5555!

---

## 📡 API Endpoints

KeyChaser provides a REST API for programmatic access:

### Bots
```bash
# List all bots
GET http://localhost:8000/api/bots

# Get specific bot
GET http://localhost:8000/api/bots/1

# Count bots by protocol
GET http://localhost:8000/api/bots/count?protocol=ExampleLogger

# Delete bot and all data
DELETE http://localhost:8000/api/bots/1
```

### Logs
```bash
# List keystroke logs
GET http://localhost:8000/api/logs?limit=50

# Filter by bot
GET http://localhost:8000/api/logs?bot_id=1

# Search keystrokes
GET http://localhost:8000/api/logs/search?keyword=password
```

### Statistics
```bash
# Overview stats
GET http://localhost:8000/api/stats/overview

# Timeline (hourly data)
GET http://localhost:8000/api/stats/timeline?hours=24

# Top IPs
GET http://localhost:8000/api/stats/top_ips?limit=10

# Protocol stats
GET http://localhost:8000/api/stats/protocols
```

---

## 🔍 Forensic Analysis

### View Traffic Logs

All traffic is logged to `data/logs/traffic.log` with hexdumps:

```bash
tail -f data/logs/traffic.log
```

**Example output:**
```
2026-01-20 16:05:45 | [ExampleLogger] RAW DATA from 127.0.0.1:
00000000  54 45 53 54 2d 42 4f 54  2d 30 30 31 7c 56 49 43  |TEST-BOT-001|VIC|
00000010  54 49 4d 2d 50 43 7c 6a  6f 68 6e 2e 64 6f 65 7c  |TIM-PC|john.doe||
...

2026-01-20 16:05:45 | [ExampleLogger] DECRYPTED DATA from 127.0.0.1:
00000000  54 45 53 54 2d 42 4f 54  2d 30 30 31 7c 56 49 43  |TEST-BOT-001|VIC|
...
```

### Database Analysis

Query the SQLite database directly:

```bash
sqlite3 data/keychaser.db

# View all bots
SELECT * FROM bots;

# View recent keystrokes
SELECT window_title, keystroke_data, received_at FROM logs ORDER BY received_at DESC LIMIT 10;

# Count by protocol
SELECT protocol, COUNT(*) FROM bots GROUP BY protocol;
```

---

## ⚙️ Configuration

All settings are in `app/core/config.py` and can be overridden with environment variables:

| Setting | Default | Description |
|---------|---------|-------------|
| `KEYCHASER_HOST` | `0.0.0.0` | Server bind address |
| `KEYCHASER_API_PORT` | `8000` | Dashboard port |
| `KEYCHASER_DB_PATH` | `data/keychaser.db` | Database location |
| `KEYCHASER_LOG_LEVEL` | `INFO` | Logging verbosity |
| `KEYCHASER_MAX_PACKET_SIZE` | `65536` | Max payload (DoS protection) |
| `KEYCHASER_CONNECTION_TIMEOUT` | `30` | Connection timeout (seconds) |
| `KEYCHASER_MAX_CONNECTIONS_PER_IP` | `10` | Rate limiting |

---

## 🛡️ Security Best Practices

1. **Isolated Network**: Run KeyChaser in a VM or isolated lab network
2. **Firewall Rules**: Restrict dashboard access to localhost or trusted IPs
3. **No Public Internet**: Never expose protocol ports to the internet
4. **Data Encryption**: Consider encrypting the SQLite database at rest
5. **Legal Authorization**: Only use for authorized research/testing

---

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Check what's using port 4444
netstat -ano | findstr :4444

# Kill the process (Windows)
taskkill /PID <PID> /F
```

### Database Locked
```bash
# Close all connections and restart
rm data/keychaser.db
python -m app.main
```

### Protocol Not Loading
```bash
# Check enabled protocols
echo $env:KEYCHASER_ENABLED_PROTOCOLS

# Verify file exists
ls app/protocols/
```

### Connection Refused (Test Client)
- Ensure KeyChaser is running
- Check firewall isn't blocking port 4444
- Verify localhost connectivity

---

## 📈 Performance Tuning

For high-volume malware campaigns:

1. **Increase Connection Limits**:
   ```bash
   export KEYCHASER_MAX_CONNECTIONS_PER_IP=100
   ```

2. **Use PostgreSQL Instead of SQLite**:
   - Edit `app/core/database.py`
   - Update `get_database_url()` to return PostgreSQL URL
   - Install `asyncpg`

3. **Disable Debug Logging**:
   ```bash
   export KEYCHASER_LOG_LEVEL=WARNING
   export KEYCHASER_LOG_TO_FILE=false
   ```

4. **Run Multiple Instances** (different ports):
   ```bash
   # Instance 1 - ports 4444-4999
   KEYCHASER_API_PORT=8000 python -m app.main &
   
   # Instance 2 - ports 5000-5999
   KEYCHASER_API_PORT=8001 python -m app.main &
   ```

---

## 🎓 Next Steps

1. **Reverse Engineer Real Malware**: Use Wireshark/IDA Pro to analyze C2 traffic
2. **Implement Real Protocols**: Create handlers for AgentTesla, RedLine, Raccoon, etc.
3. **Add Alerting**: Integrate with Slack/Discord for real-time notifications
4. **ML Integration**: Train models to detect credential patterns in keystrokes
5. **Threat Intelligence**: Export IOCs (IPs, bot IDs) to MISP/OpenCTI

---

## 📚 Additional Resources

- **Protocol Reverse Engineering**: [Malware Traffic Analysis](https://www.malware-traffic-analysis.net/)
- **FastAPI Docs**: [fastapi.tiangolo.com](https://fastapi.tiangolo.com/)
- **SQLAlchemy Async**: [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- **Python Asyncio**: [docs.python.org/3/library/asyncio.html](https://docs.python.org/3/library/asyncio.html)

---

## 🤝 Support

For issues or questions:
1. Check the logs in `data/logs/`
2. Review the troubleshooting section
3. Consult the code documentation (all modules have detailed docstrings)

---

**Built with ❤️ for Security Researchers**

*Remember: Only use KeyChaser for authorized research in isolated environments.*
