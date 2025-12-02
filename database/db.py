import asyncpg
from typing import Optional

from utils.config import settings


_pool: Optional[asyncpg.Pool] = None


async def init_db_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(dsn=settings.postgres_dsn)
    return _pool


async def close_db_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


async def ensure_schema() -> None:
    pool = await init_db_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                google_token TEXT,
                opiu_url TEXT,
                sku_url TEXT,
                setings_url TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            );
            """
        )


async def upsert_user_google_data(
    user_id: int,
    refresh_token: str,
    opiu_url: str,
    sku_url: str,
    settings_url: str,
) -> None:
    pool = await init_db_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO users (user_id, google_token, opiu_url, sku_url, setings_url)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (user_id) DO UPDATE SET
                google_token = EXCLUDED.google_token,
                opiu_url = EXCLUDED.opiu_url,
                sku_url = EXCLUDED.sku_url,
                setings_url = EXCLUDED.setings_url;
            """,
            user_id,
            refresh_token,
            opiu_url,
            sku_url,
            settings_url,
        )


async def get_user_refresh_token(user_id: int) -> Optional[str]:
    pool = await init_db_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT google_token FROM users WHERE user_id = $1", user_id
        )
        return row["google_token"] if row else None


