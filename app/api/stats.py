"""
Statistics and analytics API endpoints.

Provides aggregated statistics about captured traffic, active infections,
and credential theft for the dashboard.
"""

from datetime import datetime, timedelta
from typing import Dict, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger
from app.models.bot import Bot
from app.models.credential import Credential
from app.models.log import Log

logger = get_logger(__name__)

router = APIRouter()


@router.get("/stats/overview")
async def get_overview(db: AsyncSession = Depends(get_db)):
    """
    Get high-level statistics overview.
    
    Returns counts of bots, logs, credentials, and active infections.
    """
    # Total counts
    total_bots = await db.scalar(select(func.count(Bot.id)))
    total_logs = await db.scalar(select(func.count(Log.id)))
    total_credentials = await db.scalar(select(func.count(Credential.id)))
    
    # Active bots (seen in last hour)
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    active_bots = await db.scalar(
        select(func.count(Bot.id)).where(Bot.last_seen >= one_hour_ago)
    )
    
    # Protocol distribution
    protocol_result = await db.execute(
        select(Bot.protocol, func.count(Bot.id))
        .group_by(Bot.protocol)
    )
    protocols = {row[0]: row[1] for row in protocol_result}
    
    return {
        "total_bots": total_bots,
        "active_bots": active_bots,
        "total_logs": total_logs,
        "total_credentials": total_credentials,
        "protocols": protocols,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/stats/timeline")
async def get_timeline(
    hours: int = Query(24, ge=1, le=168, description="Hours to look back"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get infection timeline data for charting.
    
    Returns hourly aggregated counts of new bots and log entries.
    """
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    # New bots per hour
    bot_timeline = await db.execute(
        select(
            func.strftime("%Y-%m-%d %H:00:00", Bot.first_seen).label("hour"),
            func.count(Bot.id).label("count")
        )
        .where(Bot.first_seen >= cutoff_time)
        .group_by("hour")
        .order_by("hour")
    )
    
    # Logs per hour
    log_timeline = await db.execute(
        select(
            func.strftime("%Y-%m-%d %H:00:00", Log.received_at).label("hour"),
            func.count(Log.id).label("count")
        )
        .where(Log.received_at >= cutoff_time)
        .group_by("hour")
        .order_by("hour")
    )
    
    return {
        "bots": [{"hour": row[0], "count": row[1]} for row in bot_timeline],
        "logs": [{"hour": row[0], "count": row[1]} for row in log_timeline],
        "hours": hours,
    }


@router.get("/stats/top_ips")
async def get_top_ips(
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    Get top IP addresses by infection count.
    """
    result = await db.execute(
        select(Bot.ip_address, func.count(Bot.id).label("count"))
        .group_by(Bot.ip_address)
        .order_by(func.count(Bot.id).desc())
        .limit(limit)
    )
    
    return [{"ip": row[0], "count": row[1]} for row in result]


@router.get("/stats/top_credentials")
async def get_top_credentials(
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    Get most commonly stolen credential types.
    """
    result = await db.execute(
        select(Credential.cred_type, func.count(Credential.id).label("count"))
        .group_by(Credential.cred_type)
        .order_by(func.count(Credential.id).desc())
        .limit(limit)
    )
    
    return [{"type": row[0], "count": row[1]} for row in result]


@router.get("/stats/recent_activity")
async def get_recent_activity(
    minutes: int = Query(15, ge=1, le=1440),
    db: AsyncSession = Depends(get_db),
):
    """
    Get recent activity summary (last N minutes).
    
    Useful for real-time dashboard updates.
    """
    cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
    
    # Recent bots
    recent_bots = await db.scalar(
        select(func.count(Bot.id)).where(Bot.last_seen >= cutoff_time)
    )
    
    # Recent logs
    recent_logs = await db.scalar(
        select(func.count(Log.id)).where(Log.received_at >= cutoff_time)
    )
    
    # Recent credentials
    recent_creds = await db.scalar(
        select(func.count(Credential.id)).where(Credential.received_at >= cutoff_time)
    )
    
    return {
        "minutes": minutes,
        "bots": recent_bots,
        "logs": recent_logs,
        "credentials": recent_creds,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/stats/protocols")
async def get_protocol_stats(db: AsyncSession = Depends(get_db)):
    """
    Get detailed statistics per protocol.
    """
    result = await db.execute(
        select(
            Bot.protocol,
            func.count(Bot.id).label("bot_count"),
            func.max(Bot.last_seen).label("last_activity")
        )
        .group_by(Bot.protocol)
    )
    
    protocols = []
    for row in result:
        protocol_name = row[0]
        
        # Get log count for this protocol
        log_count = await db.scalar(
            select(func.count(Log.id))
            .join(Bot, Bot.id == Log.bot_id)
            .where(Bot.protocol == protocol_name)
        )
        
        # Get credential count
        cred_count = await db.scalar(
            select(func.count(Credential.id))
            .join(Bot, Bot.id == Credential.bot_id)
            .where(Bot.protocol == protocol_name)
        )
        
        protocols.append({
            "protocol": protocol_name,
            "bots": row[1],
            "logs": log_count,
            "credentials": cred_count,
            "last_activity": row[2].isoformat() if row[2] else None,
        })
    
    return protocols
