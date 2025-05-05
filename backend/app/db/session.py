from app.core.config import settings
from sqlalchemy.ext.asyncio import (
    create_async_engine,  # SQLAlchemy を直接使う場合も同様
)
from sqlalchemy.orm import sessionmaker
from sqlmodel.ext.asyncio.session import (
    AsyncSession,  # または from sqlalchemy.ext.asyncio import AsyncSession
)

# 非同期データベースエンジンを作成
# echo=True にすると実行されるSQLがログに出力される (開発時に便利)
engine = create_async_engine(settings.DATABASE_URL, echo=True, future=True)

# 非同期セッションを作成するためのファクトリ
# expire_on_commit=False にしないと、コミット後にオブジェクトにアクセスできなくなる場合がある
AsyncSessionFactory = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


# FastAPIの依存性注入(Depends)で使うための非同期セッション取得関数
async def get_db() -> AsyncSession:
    async with AsyncSessionFactory() as session:
        yield session
