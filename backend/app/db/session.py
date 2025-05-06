import logging
from typing import AsyncGenerator

from app.core.config import settings
from sqlalchemy.ext.asyncio import (
    create_async_engine,  # SQLAlchemy を直接使う場合も同様
)
from sqlalchemy.orm import sessionmaker
from sqlmodel.ext.asyncio.session import (
    AsyncSession,  # または from sqlalchemy.ext.asyncio import AsyncSession
)

logger = logging.getLogger(__name__)

# 非同期データベースエンジンを作成
# echo=True にすると実行されるSQLがログに出力される (開発時に便利)
engine = create_async_engine(settings.DATABASE_URL, echo=True, future=True)

# 非同期セッションを作成するためのファクトリ
# expire_on_commit=False にしないと、コミット後にオブジェクトにアクセスできなくなる場合がある
AsyncSessionFactory = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


# FastAPIの依存性注入(Depends)で使うための非同期セッション取得関数
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    DBセッションを依存関係として提供する非同期ジェネレータ。
    リクエスト処理完了時に自動でコミットまたはロールバックする。
    """
    print("DEBUG [Session]: Getting DB session")  # デバッグ用
    async with AsyncSessionFactory() as session:
        try:
            yield session  # ここでルーターやサービスにセッションが渡される
            # yieldから戻ってきた後、例外が発生していなければコミット
            await session.commit()
            print("DEBUG [Session]: Transaction committed.")  # デバッグ用
        except Exception as e:
            # yieldの後、またはyield中に例外が発生した場合
            logger.error(
                f"Transaction rolled back due to exception: {e}", exc_info=True
            )
            await session.rollback()  # ロールバック実行
            raise e  # エラーを再送出してFastAPIに処理させる
        # finally:
        # 'async with AsyncSessionFactory() as session:' を使っているので、
        # finally ブロックでの明示的な session.close() は通常不要
        # print("DEBUG [Session]: Session closed.")
