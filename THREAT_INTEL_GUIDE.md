# Threat Intelligence Integration Guide

## Overview

KeyChaser now automatically enriches captured data with threat intelligence from:
- **VirusTotal** - File hash reputation (malware detection by 60+ AV vendors)
- **AbuseIPDB** - IP reputation (botnet/scanner/abuse detection)

This enrichment happens automatically in the background without blocking C2 traffic processing.

---

## Features

### 🔍 Automatic IP Reputation Checks

When a **new bot** connects:
1. IP is queried against AbuseIPDB
2. Reputation data stored in `bot.extra_data`
3. High abuse IPs (>80% confidence) tagged as "SCANNER"
4. Telegram alert sent for malicious IPs

**Result Example:**
```json
{
  "ip_reputation": {
    "abuse_score": 95,
    "isp": "Digital Ocean",
    "country": "US",
    "usage_type": "Data Center/Web Hosting/Transit",
    "total_reports": 127,
    "whitelisted": false
  }
}
```

### 🦠 Automatic Malware Hash Analysis

When **payloads are captured** (keystrokes, clipboard):
1. SHA256 hash calculated
2. Hash queried against VirusTotal
3. Detection results stored in `log.extra_data`
4. Telegram alert sent if known malware detected

**Result Example:**
```json
{
  "virustotal": {
    "sha256": "abc123...",
    "malicious": 55,
    "suspicious": 3,
    "total_vendors": 60,
    "detection_names": ["Trojan.Generic", "Win32.AgentTesla"]
  }
}
```

---

## Setup Instructions

### Step 1: Get API Keys

#### **AbuseIPDB** (Free: 1,000 checks/day)
1. Visit https://www.abuseipdb.com/account/api
2. Sign up for free account
3. Generate API key from dashboard
4. Copy the key (looks like: `abc123def456...`)

#### **VirusTotal** (Free: 4 requests/minute, 500/day)
1. Visit https://www.virustotal.com/gui/my-apikey
2. Sign up for free account
3. Copy API key from "API Key" section
4. Key looks like: `abc123def456...789`

**Note:** Free tiers are sufficient for most sinkhole deployments. Paid plans available for higher limits.

### Step 2: Configure KeyChaser

Edit `.env` file:

```env
# Threat Intelligence APIs
KEYCHASER_VIRUSTOTAL_API_KEY=your_virustotal_key_here
KEYCHASER_ABUSEIPDB_API_KEY=your_abuseipdb_key_here
```

**Optional:** Leave keys empty to disable enrichment (graceful degradation).

### Step 3: Restart Server

```powershell
python -m app.main
```

**Expected Log Output:**
```
INFO  [enrichment] AbuseIPDB: 192.168.1.100 - Confidence: 25%, Reports: 5
INFO  [enrichment] VirusTotal: abc123... - Malicious: 0/60
```

---

## Integration Points

### 1. IP Reputation Check (New Bots)

**Location:** `app/protocols/base.py` → `_store_data()` method

**Code:**
```python
if is_new_bot:
    from app.core.enrichment import enrich_bot_with_ip_reputation
    asyncio.create_task(
        enrich_bot_with_ip_reputation(bot.ip_address, bot, session)
    )
```

**What Happens:**
- Runs as **background task** (doesn't block bot registration)
- Queries AbuseIPDB API with 10-second timeout
- Updates `bot.extra_data` with reputation info
- Tags bot as "SCANNER" if abuse score > 80%
- Sends Telegram alert for malicious IPs

**Telegram Alert Example:**
```
🚨 Malicious IP Detected

IP: 203.0.113.42
Abuse Score: 95%
ISP: Shady Hosting Inc
Reports: 127
Usage: Data Center/Web Hosting/Transit
```

### 2. Payload Hash Check (Logs)

**Location:** `app/protocols/base.py` → `_store_data()` method (log storage loop)

**Code:**
```python
if keystroke_data and len(keystroke_data) > 100:
    from app.core.enrichment import enrich_payload_with_hash_check
    payload_bytes = keystroke_data.encode('utf-8')
    asyncio.create_task(
        enrich_payload_with_hash_check(payload_bytes, log, session)
    )
```

**What Happens:**
- Only analyzes payloads > 100 bytes (reduces API calls)
- Calculates SHA256 hash of payload
- Queries VirusTotal API with 10-second timeout
- Updates `log.extra_data` with VT results
- Sends alert if `malicious > 0`

**Telegram Alert Example:**
```
🚨 Known Malware Detected (VT Score: 55/60)

SHA256: abc123def456...
Detections: 55/60 vendors
Names: Trojan.Generic, Win32.AgentTesla, HEUR:Backdoor.Win32
First Seen: 2024-01-15
```

---

## Database Schema Changes

### Bot Model (`extra_data` field)

```json
{
  "ip_reputation": {
    "abuse_score": 85,
    "isp": "Example ISP",
    "country": "US",
    "usage_type": "Data Center",
    "total_reports": 42,
    "whitelisted": false
  }
}
```

### Log Model (`extra_data` field)

```json
{
  "virustotal": {
    "sha256": "abc123...",
    "malicious": 55,
    "suspicious": 3,
    "total_vendors": 60,
    "detection_names": ["Trojan.Generic", "Win32.Malware"]
  }
}
```

**Note:** `extra_data` is a JSON field - no migration needed!

---

## API Rate Limits

### AbuseIPDB (Free Tier)
- **Daily Limit:** 1,000 checks/day
- **Rate Limit:** No specific per-minute limit
- **Status Code:** 429 (Too Many Requests)

**Best Practice:**
- Only check new bots (not on every connection)
- Cache results per IP for 24 hours (optional)

### VirusTotal (Free Tier)
- **Daily Limit:** 500 lookups/day
- **Rate Limit:** 4 requests/minute
- **Status Code:** 429 (Too Many Requests)

**Best Practice:**
- Only analyze large payloads (>100 bytes)
- Skip duplicate hashes (optional enhancement)

---

## Error Handling

### Graceful Degradation

All enrichment functions handle errors gracefully:

```python
try:
    reputation = await check_ip_reputation(ip)
except Exception:
    # Logs warning but doesn't crash
    return None
```

**Failure Scenarios:**
1. **No API Key** → Silently skips enrichment (debug log)
2. **API Timeout** → Returns None, logs warning
3. **Rate Limit** → Returns None, logs warning
4. **Invalid Key** → Logs error once, returns None
5. **Network Error** → Returns None, logs warning

**Impact:** Bot processing continues normally - enrichment is optional.

---

## Testing

### Test IP Reputation

```python
# Send test traffic from "known bad" IP
import socket
s = socket.socket()
s.connect(('localhost', 4444))
s.send(b'TEST-BOT|SCANNER-PC|hacker|Kali Linux')
s.close()

# Check logs:
# INFO  [enrichment] AbuseIPDB: 127.0.0.1 - Confidence: 0%, Reports: 0
# (localhost has 0% abuse - expected)
```

**Test with Real Malicious IP:**
Set up SSH tunnel or VPN to test with known scanner IP (e.g., from tor exit nodes).

### Test VirusTotal

```python
# Create large payload to trigger VT check
import socket
s = socket.socket()
s.connect(('localhost', 4444))
# Send 200-byte payload
s.send(b'A' * 200 + b'|BOT|PC|user|Win10')
s.close()

# Check logs:
# INFO  [enrichment] VirusTotal: abc123... - Malicious: 0/60
```

**Test Known Malware Hash:**
```python
from app.core.enrichment import check_file_hash

# EICAR test file hash (known malware signature)
eicar_hash = "275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f"
result = await check_file_hash(eicar_hash)
# Should return: malicious > 50
```

---

## Customization

### Change Abuse Threshold

```python
# In enrichment.py → enrich_bot_with_ip_reputation
if abuse_score > 50:  # Changed from 80 to 50 (more aggressive)
    bot_obj.campaign_id = "SCANNER"
```

### Disable VT for Specific Protocols

```python
# In base.py
if self.name != "ExampleLogger" and keystroke_data:
    # Only check AgentTesla payloads
    asyncio.create_task(enrich_payload_with_hash_check(...))
```

### Cache Results (Reduce API Calls)

```python
# Add to enrichment.py
IP_CACHE = {}  # IP -> (timestamp, reputation)

async def check_ip_reputation(ip: str):
    # Check cache first
    if ip in IP_CACHE:
        timestamp, data = IP_CACHE[ip]
        if time.time() - timestamp < 86400:  # 24 hours
            return data
    
    # Query API
    result = await _query_abuseipdb(ip)
    IP_CACHE[ip] = (time.time(), result)
    return result
```

---

## Dashboard Integration (Future)

Planned enhancements:

### Show Reputation in Bot Grid

```typescript
// In BotDataGrid.tsx
{bot.extra_data?.ip_reputation?.abuse_score > 80 && (
  <span className="badge badge-danger">
    🚨 Malicious IP ({bot.extra_data.ip_reputation.abuse_score}%)
  </span>
)}
```

### VirusTotal Badge

```typescript
// In Log detail view
{log.extra_data?.virustotal?.malicious > 0 && (
  <span className="badge badge-critical">
    🦠 Malware Detected ({log.extra_data.virustotal.malicious}/60)
  </span>
)}
```

---

## Security Considerations

### Protecting API Keys

**DO NOT commit `.env` to git!** (.gitignore already excludes it)

**Best Practice:**
```bash
# Use environment variables in production
export KEYCHASER_VIRUSTOTAL_API_KEY="..."
export KEYCHASER_ABUSEIPDB_API_KEY="..."
```

### Data Privacy

- IP reputation checks send **only the IP address** to AbuseIPDB
- VT checks send **only the hash** (not the actual payload)
- No sensitive data (passwords, credentials) is sent to external APIs

### Rate Limiting

Monitor API usage to avoid quota exhaustion:

```python
# Add to enrichment.py
API_CALLS = {"abuseipdb": 0, "virustotal": 0}

async def check_ip_reputation(ip: str):
    if API_CALLS["abuseipdb"] >= 1000:
        logger.warning("Daily AbuseIPDB quota reached")
        return None
    
    API_CALLS["abuseipdb"] += 1
    # ... rest of logic
```

---

## Troubleshooting

### "AbuseIPDB: Invalid API key"

**Cause:** API key is wrong or expired  
**Fix:**
1. Regenerate key at https://www.abuseipdb.com/account/api
2. Update `.env` with new key
3. Restart server

### "VirusTotal: Rate limit exceeded"

**Cause:** >4 requests/minute (free tier)  
**Fix:**
1. Reduce payload analysis frequency
2. Add hash caching (see Customization)
3. Upgrade to paid plan ($$$)

### Enrichment Not Working

**Checklist:**
- [ ] API keys set in `.env` (no extra spaces)
- [ ] Server restarted after `.env` changes
- [ ] Check logs: `grep "enrichment" data/logs/*.log`
- [ ] Test API manually: `curl -H "Key: YOUR_KEY" https://api.abuseipdb.com/api/v2/check?ipAddress=8.8.8.8`

### "Timeout checking IP"

**Cause:** Network issues or API down  
**Fix:**
1. Check internet connectivity
2. Test API directly: `ping api.abuseipdb.com`
3. Increase timeout in enrichment.py (default 10s)

---

## Resources

- [AbuseIPDB API Documentation](https://docs.abuseipdb.com/)
- [VirusTotal API v3 Documentation](https://developers.virustotal.com/reference/overview)
- [httpx Async Client Guide](https://www.python-httpx.org/async/)

---

**You're all set!** KeyChaser will now automatically enrich bots with threat intelligence. 🔍🛡️
