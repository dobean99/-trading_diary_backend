from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session

DBSession = AsyncSession
GetDBSession = get_db_session
