"""
Threat Intelligence Enrichment Service.

Integrates external APIs (VirusTotal, AbuseIPDB) to automatically
analyze captured data and enrich bot/payload metadata.
"""

import asyncio
import hashlib
from typing import Dict, Optional

import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


async def check_ip_reputation(ip: str) -> Optional[Dict[str, any]]:
    """
    Check IP reputation using AbuseIPDB.
    
    Queries AbuseIPDB API to determine if an IP is associated with
    malicious activity, botnets, or scanning.
    
    Args:
        ip: IP address to check
        
    Returns:
        Dictionary with reputation data:
        {
            "abuseConfidenceScore": 85,
            "isp": "Example ISP",
            "countryCode": "US",
            "usageType": "Data Center/Web Hosting/Transit",
            "totalReports": 42,
            "isWhitelisted": false
        }
        Returns None if API is disabled or request fails.
        
    Example:
        result = await check_ip_reputation("192.168.1.100")
        if result and result["abuseConfidenceScore"] > 80:
            logger.warning(f"High abuse confidence: {ip}")
    """
    # Check if API is configured
    if not settings.abuseipdb_api_key:
        logger.debug("AbuseIPDB API disabled (no key configured)")
        return None
    
    try:
        url = "https://api.abuseipdb.com/api/v2/check"
        
        headers = {
            "Key": settings.abuseipdb_api_key,
            "Accept": "application/json"
        }
        
        params = {
            "ipAddress": ip,
            "maxAgeInDays": 90,  # Check last 90 days of reports
            "verbose": ""  # Include detailed report info
        }
        
        async with httpx.AsyncClient() as client:
            response = await asyncio.wait_for(
                client.get(url, headers=headers, params=params),
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "data" in data:
                    result = data["data"]
                    logger.info(
                        f"AbuseIPDB: {ip} - Confidence: {result.get('abuseConfidenceScore', 0)}%, "
                        f"Reports: {result.get('totalReports', 0)}"
                    )
                    return result
                else:
                    logger.warning(f"AbuseIPDB: Unexpected response format for {ip}")
                    return None
                    
            elif response.status_code == 429:
                logger.warning("AbuseIPDB: Rate limit exceeded")
                return None
            elif response.status_code == 401:
                logger.error("AbuseIPDB: Invalid API key")
                return None
            else:
                logger.warning(f"AbuseIPDB: API returned status {response.status_code}")
                return None
                
    except asyncio.TimeoutError:
        logger.warning(f"AbuseIPDB: Timeout checking {ip}")
        return None
    except httpx.HTTPError as e:
        logger.warning(f"AbuseIPDB: HTTP error for {ip}: {e}")
        return None
    except Exception as e:
        logger.error(f"AbuseIPDB: Unexpected error for {ip}: {e}")
        return None


async def check_file_hash(sha256_hash: str) -> Optional[Dict[str, any]]:
    """
    Check file hash reputation using VirusTotal.
    
    Queries VirusTotal API to determine if a file hash is known
    malware based on antivirus vendor detections.
    
    Args:
        sha256_hash: SHA256 hash of the file (64 hex characters)
        
    Returns:
        Dictionary with analysis results:
        {
            "malicious": 55,      # Number of AV vendors flagging as malicious
            "suspicious": 3,      # Number flagging as suspicious
            "undetected": 2,      # Number with no detection
            "total_vendors": 60,  # Total vendors that scanned
            "first_seen": "2024-01-15",
            "names": ["Trojan.Generic", "Win32.Malware"]
        }
        Returns None if API is disabled or request fails.
        
    Example:
        result = await check_file_hash("abc123...")
        if result and result["malicious"] > 5:
            logger.critical(f"Known malware detected! Score: {result['malicious']}/60")
    """
    # Check if API is configured
    if not settings.virustotal_api_key:
        logger.debug("VirusTotal API disabled (no key configured)")
        return None
    
    # Validate hash format
    if not sha256_hash or len(sha256_hash) != 64:
        logger.warning(f"Invalid SHA256 hash format: {sha256_hash}")
        return None
    
    try:
        url = f"https://www.virustotal.com/api/v3/files/{sha256_hash}"
        
        headers = {
            "x-apikey": settings.virustotal_api_key,
            "Accept": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await asyncio.wait_for(
                client.get(url, headers=headers),
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "data" in data and "attributes" in data["data"]:
                    attrs = data["data"]["attributes"]
                    stats = attrs.get("last_analysis_stats", {})
                    
                    # Extract detection names
                    results = attrs.get("last_analysis_results", {})
                    detection_names = list(set([
                        r.get("result", "")
                        for r in results.values()
                        if r.get("category") == "malicious" and r.get("result")
                    ]))[:10]  # Limit to 10 unique names
                    
                    result = {
                        "malicious": stats.get("malicious", 0),
                        "suspicious": stats.get("suspicious", 0),
                        "undetected": stats.get("undetected", 0),
                        "total_vendors": sum(stats.values()),
                        "first_seen": attrs.get("first_submission_date"),
                        "names": detection_names
                    }
                    
                    logger.info(
                        f"VirusTotal: {sha256_hash[:16]}... - "
                        f"Malicious: {result['malicious']}/{result['total_vendors']}"
                    )
                    return result
                else:
                    logger.warning(f"VirusTotal: Unexpected response format")
                    return None
                    
            elif response.status_code == 404:
                logger.info(f"VirusTotal: Hash not found (unknown file)")
                return None
            elif response.status_code == 429:
                logger.warning("VirusTotal: Rate limit exceeded")
                return None
            elif response.status_code == 401:
                logger.error("VirusTotal: Invalid API key")
                return None
            else:
                logger.warning(f"VirusTotal: API returned status {response.status_code}")
                return None
                
    except asyncio.TimeoutError:
        logger.warning(f"VirusTotal: Timeout checking hash")
        return None
    except httpx.HTTPError as e:
        logger.warning(f"VirusTotal: HTTP error: {e}")
        return None
    except Exception as e:
        logger.error(f"VirusTotal: Unexpected error: {e}")
        return None


def calculate_sha256(data: bytes) -> str:
    """
    Calculate SHA256 hash of binary data.
    
    Args:
        data: Binary data to hash
        
    Returns:
        64-character hexadecimal SHA256 hash
        
    Example:
        hash_value = calculate_sha256(payload_bytes)
        vt_result = await check_file_hash(hash_value)
    """
    return hashlib.sha256(data).hexdigest()


async def enrich_bot_with_ip_reputation(
    ip: str,
    bot_obj: any,
    session: any
) -> None:
    """
    Enrich bot object with IP reputation data.
    
    Checks AbuseIPDB and updates bot metadata if high abuse score detected.
    This is a fire-and-forget operation that doesn't block main processing.
    
    Args:
        ip: IP address to check
        bot_obj: Bot SQLAlchemy object to update
        session: Active database session
        
    Side Effects:
        Updates bot.extra_data with reputation info
        Tags bot as "Scanner/Malicious Actor" if abuse score > 80
    """
    try:
        reputation = await check_ip_reputation(ip)
        
        if reputation:
            abuse_score = reputation.get("abuseConfidenceScore", 0)
            
            # Update bot extra_data with reputation info
            if not bot_obj.extra_data:
                bot_obj.extra_data = {}
            
            bot_obj.extra_data["ip_reputation"] = {
                "abuse_score": abuse_score,
                "isp": reputation.get("isp"),
                "country": reputation.get("countryCode"),
                "usage_type": reputation.get("usageType"),
                "total_reports": reputation.get("totalReports"),
                "whitelisted": reputation.get("isWhitelisted", False)
            }
            
            # Tag as malicious if high confidence
            if abuse_score > 80:
                logger.warning(
                    f"High abuse IP detected: {ip} (Score: {abuse_score}%, "
                    f"Reports: {reputation.get('totalReports', 0)})"
                )
                
                # Add tag to campaign_id field (can be used for filtering)
                if bot_obj.campaign_id:
                    bot_obj.campaign_id = f"{bot_obj.campaign_id}|SCANNER"
                else:
                    bot_obj.campaign_id = "SCANNER"
                
                # Send Telegram alert if configured
                try:
                    from app.core.notifier import send_notification
                    await send_notification(
                        title="🚨 Malicious IP Detected",
                        message=(
                            f"<b>IP:</b> <code>{ip}</code>\n"
                            f"<b>Abuse Score:</b> {abuse_score}%\n"
                            f"<b>ISP:</b> {reputation.get('isp', 'N/A')}\n"
                            f"<b>Reports:</b> {reputation.get('totalReports', 0)}\n"
                            f"<b>Usage:</b> {reputation.get('usageType', 'N/A')}"
                        ),
                        level="CRITICAL"
                    )
                except Exception as e:
                    logger.debug(f"Telegram alert failed: {e}")
            
            await session.commit()
            logger.info(f"IP reputation enrichment completed for {ip}")
            
    except Exception as e:
        logger.error(f"IP enrichment failed for {ip}: {e}")


async def enrich_payload_with_hash_check(
    payload_data: bytes,
    log_obj: any,
    session: any
) -> None:
    """
    Enrich log/payload with VirusTotal hash analysis.
    
    Calculates SHA256 of payload and checks VirusTotal for known malware.
    Sends alert if malicious detection count is high.
    
    Args:
        payload_data: Binary payload data
        log_obj: Log SQLAlchemy object to update
        session: Active database session
        
    Side Effects:
        Updates log.extra_data with VT analysis
        Sends Telegram alert if malware detected
    """
    try:
        # Calculate hash
        sha256 = calculate_sha256(payload_data)
        logger.debug(f"Calculated SHA256: {sha256[:16]}...")
        
        # Check VirusTotal
        vt_result = await check_file_hash(sha256)
        
        if vt_result:
            malicious_count = vt_result.get("malicious", 0)
            total_vendors = vt_result.get("total_vendors", 0)
            
            # Update log extra_data
            if not log_obj.extra_data:
                log_obj.extra_data = {}
            
            log_obj.extra_data["virustotal"] = {
                "sha256": sha256,
                "malicious": malicious_count,
                "suspicious": vt_result.get("suspicious", 0),
                "total_vendors": total_vendors,
                "detection_names": vt_result.get("names", [])
            }
            
            # Alert if known malware
            if malicious_count > 0:
                logger.critical(
                    f"KNOWN MALWARE DETECTED! SHA256: {sha256[:16]}... "
                    f"Score: {malicious_count}/{total_vendors}"
                )
                
                # Send Telegram alert
                try:
                    from app.core.notifier import send_notification
                    detections = ", ".join(vt_result.get("names", [])[:3])
                    await send_notification(
                        title=f"🚨 Known Malware Detected (VT Score: {malicious_count}/{total_vendors})",
                        message=(
                            f"<b>SHA256:</b> <code>{sha256}</code>\n"
                            f"<b>Detections:</b> {malicious_count}/{total_vendors} vendors\n"
                            f"<b>Names:</b> {detections}\n"
                            f"<b>First Seen:</b> {vt_result.get('first_seen', 'Unknown')}"
                        ),
                        level="CRITICAL"
                    )
                except Exception as e:
                    logger.debug(f"Telegram alert failed: {e}")
            
            await session.commit()
            logger.info(f"VirusTotal enrichment completed: {malicious_count}/{total_vendors}")
            
    except Exception as e:
        logger.error(f"Payload enrichment failed: {e}")
