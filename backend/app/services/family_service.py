import logging

from fastapi import HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.crud import crud_family, crud_membership
from app.models.family import Family
from app.models.family_membership import MembershipRole
from app.models.user import User
from app.schemas.family import FamilyCreate

logger = logging.getLogger(__name__)


async def create_family_with_owner(
    db: AsyncSession, *, family_in: FamilyCreate, owner_user: User
) -> Family:
    """
    新しい家族を作成し、作成者をオーナー(admin)としてメンバーに追加する。
    トランザクション管理は get_db 依存関係に任せる。
    """
    # 1. 重複チェック (HTTPExceptionはそのままraiseしてOK、get_dbがrollbackしてくれる)
    existing_family = await crud_family.get_family_by_name(
        db, name=family_in.family_name
    )
    if existing_family:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Family with this name already exists.",
        )

    # 2. 家族を作成 (add + flush in CRUD)
    db_family = await crud_family.create_family(db=db, family_in=family_in)
    if not db_family or not db_family.id:
        logger.error(
            "Family creation CRUD function returned None or no ID after flush."
        )
        # 予期せぬエラーはそのままraiseすれば get_db がrollbackしてくれる
        raise ValueError("Family creation failed unexpectedly after flush.")

    # 3. オーナーをメンバーに追加 (add + flush in CRUD)
    await crud_membership.create_membership(
        db=db, user_id=owner_user.id, family_id=db_family.id, role=MembershipRole.ADMIN
    )

    logger.info(
        f"Family '{db_family.family_name}' (ID: {db_family.id}) and owner membership prepared in session."
    )

    return db_family  # セッションに追加・flushされた状態のオブジェクトを返す


async def get_family_for_user_or_404(
    db: AsyncSession, *, family_id: int, user: User
) -> Family:
    """
    指定されたIDの家族を取得する。ユーザーがメンバーでない場合は403エラー。
    家族が存在しない場合は404エラー。
    """
    # 1. 家族を取得
    db_family = await crud_family.get_family(db, family_id=family_id)
    if db_family is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Family not found",
        )

    # 2. ユーザーがメンバーかチェック (認可)
    is_member = await crud_membership.is_user_member(
        db, user_id=user.id, family_id=family_id
    )
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this family",
        )

    return db_family
