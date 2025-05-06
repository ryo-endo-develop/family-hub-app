from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.user import User


async def get_user(db: AsyncSession, user_id: int) -> User | None:
    """IDを指定してユーザー情報を取得する"""
    user = await db.get(User, user_id)
    return user


# (参考) 将来的にOIDC連携時などに必要になる可能性のある関数
async def get_user_by_oidc_subject(
    db: AsyncSession, *, oidc_subject: str
) -> User | None:
    """OIDC Subject を指定してユーザー情報を取得する"""
    statement = select(User).where(User.oidc_subject == oidc_subject)
    result = await db.exec(statement)
    return result.first()


async def create_user(db: AsyncSession, *, user_in: User) -> User:
    """新しいユーザーを作成する (主に内部処理用)"""
    # 本来は email や oidc_subject の重複チェックが必要
    db.add(user_in)
    await db.flush()
    await db.refresh(user_in)
    return user_in
