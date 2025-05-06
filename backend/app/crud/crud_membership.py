from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.family_membership import FamilyMembership, MembershipRole


async def create_membership(
    db: AsyncSession,
    *,
    user_id: int,
    family_id: int,
    role: MembershipRole = MembershipRole.MEMBER,
) -> FamilyMembership:
    """ユーザーを家族に追加する (セッションに追加するだけ)"""
    # TODO: すでに追加済みかチェックするロジックを追加検討
    print(f"DEBUG: Adding user {user_id} to family {family_id} with role {role.value}")
    db_membership = FamilyMembership(user_id=user_id, family_id=family_id, role=role)
    db.add(db_membership)
    await db.flush()  # DBに反映させてIDなどを取得 (コミットはしない)
    await db.refresh(db_membership)
    print(f"DEBUG: Membership created in session: ID {db_membership.id}")
    return db_membership


async def is_user_member(db: AsyncSession, *, user_id: int, family_id: int) -> bool:
    """指定されたユーザーが指定された家族のメンバーかどうかをチェックする"""
    statement = select(FamilyMembership).where(
        FamilyMembership.user_id == user_id, FamilyMembership.family_id == family_id
    )
    result = await db.exec(statement)
    membership = result.first()
    return membership is not None
