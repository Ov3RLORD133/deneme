"""
Bot management API endpoints.

Provides REST endpoints for querying infected bot information,
filtering by protocol, IP address, and time range.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
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
