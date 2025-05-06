import logging
from typing import Sequence

from fastapi import HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.crud import (
    crud_label,
)

# 必要なモデル、スキーマ、CRUD関数をインポート
from app.models.label import Label
from app.models.user import User

# from app.models.family import Family # check_user_family_membership内で必要
from app.schemas.label import LabelCreate, LabelUpdate

from .common import check_user_family_membership_or_raise

logger = logging.getLogger(__name__)


# --- Label Service 関数 ---


async def create_label_for_family(
    db: AsyncSession, *, label_in: LabelCreate, family_id: int, user: User
) -> Label:
    """指定された家族に新しいラベルを作成する (認可・重複チェック込み)"""
    # 1. 認可チェック (ユーザーが家族メンバーか？ 家族が存在するか？)
    await check_user_family_membership_or_raise(
        db, user_id=user.id, family_id=family_id
    )

    # 2. 同じ名前のラベルが家族内に存在しないかチェック
    existing_label = await crud_label.get_label_by_name_and_family(
        db, name=label_in.name, family_id=family_id
    )
    if existing_label:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,  # 重複は 409
            detail=f"Label name '{label_in.name}' already exists in this family.",
        )

    # 3. CRUD関数を呼び出してラベルを作成 (コミットは get_db に任せる)
    db_label = await crud_label.create_label(
        db, label_in=label_in, family_id=family_id, creator_id=user.id
    )
    logger.info(
        f"Label '{db_label.name}' (ID: {db_label.id}) created for family {family_id} by user {user.id}"
    )
    return db_label


async def get_labels_for_family(
    db: AsyncSession, *, family_id: int, user: User, skip: int = 0, limit: int = 100
) -> Sequence[Label]:
    """指定された家族のラベルリストを取得する (認可チェック込み)"""
    # 1. 認可チェック
    await check_user_family_membership_or_raise(
        db, user_id=user.id, family_id=family_id
    )

    # 2. CRUD関数を呼び出してラベルリストを取得
    labels = await crud_label.get_labels_by_family(
        db, family_id=family_id, skip=skip, limit=limit
    )
    return labels


async def get_label_for_family_user_or_404(
    db: AsyncSession, *, label_id: int, family_id: int, user: User
) -> Label:
    """指定されたIDのラベルを取得する (認可・存在チェック込み)"""
    # 1. 認可チェック (家族の存在とメンバーシップを確認)
    await check_user_family_membership_or_raise(
        db, user_id=user.id, family_id=family_id
    )

    # 2. CRUD関数を呼び出してラベルを取得
    db_label = await crud_label.get_label(db, label_id=label_id, family_id=family_id)
    if db_label is None:
        # CRUDで family_id も条件にしているので、ここで None になるのは
        # 「指定された家族にそのIDのラベルが存在しない」場合
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Label with ID {label_id} not found in family {family_id}",
        )
    # この時点で db_label.family_id == family_id は保証されているはず

    return db_label


async def update_label_for_family_user(
    db: AsyncSession,
    *,
    label_id: int,
    label_in: LabelUpdate,
    family_id: int,
    user: User,
) -> Label:
    """指定されたラベルを更新する (認可・存在・重複チェック込み)"""
    # 1. 認可チェック
    await check_user_family_membership_or_raise(
        db, user_id=user.id, family_id=family_id
    )

    # 2. ラベル取得
    db_label = await crud_label.get_label(db, label_id=label_id, family_id=family_id)
    if db_label is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Label not found"
        )

    # 2. 更新しようとしている名前が、家族内で他のラベルと重複しないかチェック
    if label_in.name is not None and label_in.name != db_label.name:
        existing_label_with_new_name = await crud_label.get_label_by_name_and_family(
            db, name=label_in.name, family_id=family_id
        )
        # 存在し、かつそれが自分自身でなければ重複エラー
        if existing_label_with_new_name and existing_label_with_new_name.id != label_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Label name '{label_in.name}' already exists in this family.",
            )

    # 3. CRUD関数を呼び出してラベルを更新 (コミットは get_db に任せる)
    updated_label = await crud_label.update_label(
        db, db_label=db_label, label_in=label_in, updater_id=user.id
    )
    logger.info(f"Label ID {label_id} updated by user {user.id}")
    return updated_label


async def delete_label_for_family_user(
    db: AsyncSession, *, label_id: int, family_id: int, user: User
) -> None:  # 削除成功時は何も返さない
    """指定されたラベルを削除する (認可・存在チェック込み)"""
    # 1. 認可チェックと削除対象ラベルの取得 (存在しなければ404)
    await check_user_family_membership_or_raise(
        db, user_id=user.id, family_id=family_id
    )

    db_label = await crud_label.get_label(db, label_id=label_id, family_id=family_id)
    if db_label is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Label not found"
        )

    # 2. CRUD関数を呼び出してラベルを削除 (コミットは get_db に任せる)
    await crud_label.delete_label(db, db_label=db_label)
    logger.info(f"Label ID {label_id} deleted by user {user.id}")
    # 削除成功時は None を返すか、あるいは成功メッセージを返すか（呼び出し元で判断）
    return None
