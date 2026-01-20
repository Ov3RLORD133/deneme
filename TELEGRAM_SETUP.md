# Telegram Notifications Setup Guide

## Overview

KeyChaser now sends real-time alerts to Telegram when critical events occur:
- 🦠 **New Infections** - When a new bot connects
- 🔑 **Credential Theft** - When passwords/tokens are stolen (optional)
- 🚨 **YARA Detections** - When malware signatures match (optional)

---

## Setup Instructions

### Step 1: Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` command
3. Choose a name: `KeyChaser Monitor`
4. Choose a username: `keychaser_monitor_bot` (must end in `_bot`)
5. **Copy the API token** - looks like: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`

### Step 2: Get Your Chat ID

**Option A: Using Your Bot (Easiest)**
1. Send any message to your bot (e.g., `/start`)
2. Visit this URL in browser (replace `<YOUR_TOKEN>`):
   ```
   https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
   ```
3. Look for `"chat":{"id":123456789}` in the JSON response
4. **Copy the chat ID** (numeric value)

**Option B: Using @userinfobot**
1. Search for **@userinfobot** in Telegram
2. Send `/start`
3. Bot will reply with your User ID - use this as chat ID

**Option C: For Group Chats**
1. Add your bot to a group
2. Send a message in the group
3. Visit the `getUpdates` URL above
4. Look for `"chat":{"id":-123456789}` (negative number for groups)

### Step 3: Configure KeyChaser

Edit your `.env` file:

```env
# Telegram Notifications
KEYCHASER_TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
KEYCHASER_TELEGRAM_CHAT_ID=123456789
```

**Important:**
- `BOT_TOKEN` - From @BotFather (includes colon `:`)
- `CHAT_ID` - Your user ID or group ID (can be negative)
- Leave both empty to disable notifications

### Step 4: Test the Setup

1. Restart KeyChaser backend:
   ```powershell
   python -m app.main
   ```

2. Send test malware traffic to trigger a notification:
   ```python
   import socket
   s = socket.socket()
   s.connect(('localhost', 4444))
   s.send(b'TEST-BOT-001|VICTIM-PC|testuser|Windows 10')
   s.close()
   ```

3. Check Telegram - you should receive:
   ```
   🦠 New Infection Detected

   Protocol: ExampleLogger
   IP: 127.0.0.1
   Hostname: VICTIM-PC
   Bot ID: TEST-BOT-001
   ```

---

## Notification Types

### 1. New Infection (Automatic)

Sent when a **new bot** connects for the first time:

```
🦠 New Infection Detected

Protocol: AgentTesla
IP: 192.168.1.100
Hostname: VICTIM-PC
Bot ID: AGENT-12345
YARA: ['win_agent_tesla', 'keylogger_payload']
```

**Trigger:** First connection from unique bot_id  
**Level:** WARNING (⚠️)

### 2. Credential Theft (Optional)

Can be enabled in `base.py` to alert on every credential:

```python
# In _store_data method, add after credential storage:
from app.core.notifier import send_credential_alert
await send_credential_alert(
    bot_id=bot.bot_id,
    ip_address=bot.ip_address,
    cred_type=cred_entry.get("cred_type"),
    url=cred_entry.get("url"),
    count=1
)
```

**Example Alert:**
```
🔑 Credentials Stolen (1)

Type: browser_password
Bot: AGENT-12345
IP: 192.168.1.100
URL: https://mail.google.com
```

### 3. YARA Detection (Optional)

Alert when YARA rules match (already integrated):

```
🚨 YARA Detection

IP: 192.168.1.100
Protocol: AgentTesla
Matched Rules:
• win_agent_tesla
• generic_credential_stealer
```

---

## Customization

### Change Notification Format

Edit `app/core/notifier.py` to customize messages:

```python
# Add custom fields
formatted_text = f"{emoji} <b>{title}</b>\n\n{message}\n\n<i>Timestamp: {datetime.now()}</i>"

# Add buttons (requires InlineKeyboardMarkup)
# See: https://core.telegram.org/bots/api#inlinekeyboardmarkup
```

### Add More Alert Types

```python
# In notifier.py
async def send_ddos_alert(ip: str, connection_count: int) -> bool:
    return await send_notification(
        title="🛡️ Rate Limit Exceeded",
        message=f"<b>IP:</b> {ip}\n<b>Connections:</b> {connection_count}",
        level="ERROR"
    )
```

### Disable Notifications Temporarily

```env
# Set tokens to empty in .env
KEYCHASER_TELEGRAM_BOT_TOKEN=
KEYCHASER_TELEGRAM_CHAT_ID=
```

Or comment them out - notifier will gracefully skip if unconfigured.

---

## Troubleshooting

### "Telegram notifications disabled (no credentials configured)"

**Cause:** Token or Chat ID is empty in `.env`  
**Fix:** Set both values as shown in Step 3

### "Telegram API returned status 401"

**Cause:** Invalid bot token  
**Fix:** 
1. Check for typos in token
2. Regenerate token: `/revoke` then `/newbot` with @BotFather
3. Update `.env` with new token

### "Telegram API returned status 400: Bad Request: chat not found"

**Cause:** Invalid Chat ID or bot hasn't received messages yet  
**Fix:**
1. Send `/start` to your bot first
2. Verify Chat ID using `getUpdates` URL
3. For groups: ensure bot is a member

### "Telegram notification timeout (API unreachable)"

**Cause:** Network issues or firewall blocking Telegram API  
**Fix:**
1. Test connectivity: `curl https://api.telegram.org/`
2. Check firewall rules
3. Try using a VPN if Telegram is blocked

### Notifications Not Appearing

**Checklist:**
- [ ] Token and Chat ID are correct in `.env`
- [ ] Bot token has **no extra spaces** before/after
- [ ] You sent `/start` to the bot at least once
- [ ] KeyChaser server restarted after `.env` changes
- [ ] Check server logs: `grep "Telegram" data/logs/*.log`

---

## Advanced Usage

### Multiple Alert Channels

Send different alerts to different chats:

```python
# In notifier.py, add:
CRITICAL_CHAT_ID = "987654321"  # Different chat for critical alerts

async def send_notification(title, message, level="INFO", override_chat=None):
    chat_id = override_chat or settings.telegram_chat_id
    # ... rest of logic
```

### Rich Formatting

Telegram supports HTML formatting:

```html
<b>bold</b>
<i>italic</i>
<u>underline</u>
<code>monospace</code>
<pre>code block</pre>
<a href="https://example.com">link</a>
```

**Example:**
```python
message = (
    f"<b>IP:</b> <code>{ip_address}</code>\n"
    f"<b>Protocol:</b> <u>{protocol}</u>\n"
    f"<a href='https://keychaser.local/bots/{bot_id}'>View Details</a>"
)
```

### Silent Notifications

Add `disable_notification=True` to payload for silent alerts:

```python
payload = {
    "chat_id": chat_id,
    "text": formatted_text,
    "parse_mode": "HTML",
    "disable_notification": True  # Silent notification
}
```

---

## Security Considerations

### Protecting Your Bot Token

**DO NOT commit `.env` to git!** (.gitignore already excludes it)

**Store securely:**
```bash
# Linux/Mac: Use environment variables
export KEYCHASER_TELEGRAM_BOT_TOKEN="..."
export KEYCHASER_TELEGRAM_CHAT_ID="..."

# Windows: Use system environment variables
[System.Environment]::SetEnvironmentVariable("KEYCHASER_TELEGRAM_BOT_TOKEN", "...", "User")
```

### Rate Limiting

Telegram limits: **30 messages/second** per bot

If you expect high traffic, implement batching:
```python
# Collect notifications
pending_alerts = []

# Send in batch every 5 seconds
async def batch_sender():
    while True:
        await asyncio.sleep(5)
        if pending_alerts:
            summary = "\n".join(pending_alerts[:10])
            await send_notification("Batch Alert", summary)
            pending_alerts.clear()
```

### Privacy

Sanitize sensitive data before sending:
```python
# Mask IP addresses
masked_ip = ip_address.split('.')[0] + '.XXX.XXX.XXX'

# Redact passwords (already done - we don't send passwords)
```

---

## Integration with Dashboard

Future enhancement: Add "Send Test Alert" button in dashboard:

```typescript
// In frontend
const testTelegram = async () => {
  await fetch('/api/test-telegram', { method: 'POST' });
};
```

```python
# In backend
@router.post("/test-telegram")
async def test_telegram():
    success = await send_notification(
        title="Test Alert",
        message="KeyChaser Telegram integration is working!",
        level="SUCCESS"
    )
    return {"success": success}
```

---

## Example .env (Complete)

```env
# Telegram Notifications
KEYCHASER_TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz-EXAMPLE
KEYCHASER_TELEGRAM_CHAT_ID=123456789

# Optional: Custom notification settings
KEYCHASER_NOTIFY_ON_CREDENTIALS=true
KEYCHASER_NOTIFY_ON_LOGS=false
KEYCHASER_NOTIFY_BATCH_SIZE=10
```

---

## Resources

- [Telegram Bot API Documentation](https://core.telegram.org/bots/api)
- [Bot Formatting Guide](https://core.telegram.org/bots/api#formatting-options)
- [httpx Documentation](https://www.python-httpx.org/)

---

**You're all set!** KeyChaser will now send real-time alerts to your Telegram. 📱🔔
