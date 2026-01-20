"""
Bot management API endpoints.

Provides REST endpoints for querying infected bot information,
filtering by protocol, IP address, and time range.
"""

import json
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger
from app.models.bot import Bot, BotRead

logger = get_logger(__name__)

router = APIRouter()


@router.get("/bots", response_model=List[BotRead])
async def list_bots(
    protocol: Optional[str] = Query(None, description="Filter by protocol name"),
    ip_address: Optional[str] = Query(None, description="Filter by IP address"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db),
):
    """
    List infected bots with optional filtering.
    
    Returns a paginated list of bots ordered by last_seen (most recent first).
    """
    query = select(Bot).order_by(desc(Bot.last_seen))
    
    # Apply filters
    if protocol:
        query = query.where(Bot.protocol == protocol)
    if ip_address:
        query = query.where(Bot.ip_address == ip_address)
    
    # Apply pagination
    query = query.limit(limit).offset(offset)
    
    result = await db.execute(query)
    bots = result.scalars().all()
    
    logger.info(f"Retrieved {len(bots)} bots (protocol={protocol}, ip={ip_address})")
    
    return bots


@router.get("/bots/{bot_id}", response_model=BotRead)
async def get_bot(
    bot_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed information about a specific bot.
    """
    result = await db.execute(select(Bot).where(Bot.id == bot_id))
    bot = result.scalar_one_or_none()
    
    if not bot:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Bot {bot_id} not found")
    
    return bot


@router.get("/bots/count")
async def count_bots(
    protocol: Optional[str] = Query(None, description="Filter by protocol"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get total count of bots, optionally filtered by protocol.
    """
    from sqlalchemy import func
    
    query = select(func.count(Bot.id))
    
    if protocol:
        query = query.where(Bot.protocol == protocol)
    
    result = await db.execute(query)
    count = result.scalar()
    
    return {"count": count, "protocol": protocol}


@router.delete("/bots/{bot_id}")
async def delete_bot(
    bot_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a bot and all associated logs/credentials.
    
    WARNING: This cascades to delete all related data.
    """
    result = await db.execute(select(Bot).where(Bot.id == bot_id))
    bot = result.scalar_one_or_none()
    
    if not bot:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Bot {bot_id} not found")
    
    # Delete associated logs and credentials
    from app.models.credential import Credential
    from app.models.log import Log
    from sqlalchemy import delete as sql_delete
    
    await db.execute(sql_delete(Log).where(Log.bot_id == bot_id))
    await db.execute(sql_delete(Credential).where(Credential.bot_id == bot_id))
    await db.execute(sql_delete(Bot).where(Bot.id == bot_id))
    await db.commit()
    
    logger.warning(f"Deleted bot {bot_id} and all associated data")
    
    return {"status": "deleted", "bot_id": bot_id}


@router.get("/bots/{bot_id}/export")
async def export_bot_data(
    bot_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Export complete forensic data for a bot as JSON.
    
    Returns a downloadable JSON file containing bot metadata,
    all captured logs, and stolen credentials.
    
    Perfect for offline analysis, threat intelligence, or archival.
    """
    from fastapi import HTTPException
    from app.models.credential import Credential
    from app.models.log import Log
    
    # Fetch bot
    result = await db.execute(select(Bot).where(Bot.id == bot_id))
    bot = result.scalar_one_or_none()
    
    if not bot:
        raise HTTPException(status_code=404, detail=f"Bot {bot_id} not found")
    
    # Fetch all logs
    log_result = await db.execute(
        select(Log).where(Log.bot_id == bot_id).order_by(desc(Log.received_at))
    )
    logs = log_result.scalars().all()
    
    # Fetch all credentials
    cred_result = await db.execute(
        select(Credential).where(Credential.bot_id == bot_id).order_by(desc(Credential.received_at))
    )
    credentials = cred_result.scalars().all()
    
    # Build export data structure
    export_data = {
        "export_metadata": {
            "bot_id": bot_id,
            "export_timestamp": datetime.utcnow().isoformat(),
            "keychaser_version": "1.0.0",
            "export_type": "forensic_dump"
        },
        "bot_information": {
            "id": bot.id,
            "bot_id": bot.bot_id,
            "ip_address": bot.ip_address,
            "port": bot.port,
            "protocol": bot.protocol,
            "hostname": bot.hostname,
            "username": bot.username,
            "os_info": bot.os_info,
            "malware_version": bot.malware_version,
            "campaign_id": bot.campaign_id,
            "country": bot.country,
            "country_code": bot.country_code,
            "city": bot.city,
            "latitude": bot.latitude,
            "longitude": bot.longitude,
            "continent": bot.continent,
            "timezone": bot.timezone,
            "first_seen": bot.first_seen.isoformat() if bot.first_seen else None,
            "last_seen": bot.last_seen.isoformat() if bot.last_seen else None,
            "extra_data": bot.extra_data
        },
        "captured_logs": [
            {
                "id": log.id,
                "log_type": log.log_type,
                "window_title": log.window_title,
                "keystroke_data": log.keystroke_data,
                "clipboard_data": log.clipboard_data,
                "screenshot_path": log.screenshot_path,
                "system_info": log.system_info,
                "received_at": log.received_at.isoformat() if log.received_at else None,
                "extra_data": log.extra_data
            }
            for log in logs
        ],
        "stolen_credentials": [
            {
                "id": cred.id,
                "cred_type": cred.cred_type,
                "url": cred.url,
                "username": cred.username,
                "password": cred.password,
                "email": cred.email,
                "token": cred.token,
                "application": cred.application,
                "received_at": cred.received_at.isoformat() if cred.received_at else None,
                "extra_data": cred.extra_data
            }
            for cred in credentials
        ],
        "statistics": {
            "total_logs": len(logs),
            "total_credentials": len(credentials),
            "log_types": list(set(log.log_type for log in logs if log.log_type)),
            "credential_types": list(set(cred.cred_type for cred in credentials if cred.cred_type))
        }
    }
    
    # Generate JSON
    json_content = json.dumps(export_data, indent=2, ensure_ascii=False)
    
    # Create downloadable response
    filename = f"keychaser_bot_{bot_id}_{bot.bot_id or 'unknown'}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    
    logger.info(f"Exported forensic data for bot {bot_id}: {len(logs)} logs, {len(credentials)} credentials")
    
    return Response(
        content=json_content,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


# Import datetime for timestamps
from datetime import datetime
