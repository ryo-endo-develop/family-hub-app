import logging

from fastapi import HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.crud import crud_family, crud_membership

logger = logging.getLogger(__name__)


async def check_user_family_membership_or_raise(
    db: AsyncSession, *, user_id: int, family_id: int
):
    """
    家族が存在し、かつ指定されたユーザーがその家族のメンバーであるかを確認する。
    存在しない、またはメンバーでない場合は HTTPException を発生させる。
    """
    # 1. 家族の存在確認
    #    crud_family を直接使う (循環参照を避けるため FamilyService は使わない)
    family = await crud_family.get_family(db, family_id=family_id)
    if not family:
        logger.warning(f"Auth check failed: Family {family_id} not found.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Family not found.",  # エラー詳細は少し曖昧に
        )
    # 2. メンバーシップ確認
    is_member = await crud_membership.is_user_member(
        db, user_id=user_id, family_id=family_id
    )
    if not is_member:
        logger.warning(
            f"Auth check failed: User {user_id} not member of family {family_id}."
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized for this family.",  # エラー詳細は少し曖昧に
        )
    logger.debug(f"Auth check passed: User {user_id} is member of family {family_id}")
    # この関数はチェックが目的なので、Familyオブジェクトは返さない
