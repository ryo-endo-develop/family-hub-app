from typing import Sequence

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.label import Label
from app.schemas.label import LabelCreate, LabelUpdate


async def get_label(db: AsyncSession, *, label_id: int, family_id: int) -> Label | None:
    """指定されたIDと家族IDでラベルを取得する"""
    statement = select(Label).where(Label.id == label_id, Label.family_id == family_id)
    result = await db.exec(statement)
    return result.first()


async def get_label_by_name_and_family(
    db: AsyncSession, *, name: str, family_id: int
) -> Label | None:
    """指定された名前と家族IDでラベルを取得する (重複チェック用)"""
    statement = select(Label).where(Label.name == name, Label.family_id == family_id)
    result = await db.exec(statement)
    return result.first()


async def get_labels_by_family(
    db: AsyncSession, *, family_id: int, skip: int = 0, limit: int = 100
) -> Sequence[Label]:
    """指定された家族IDのラベルリストを取得する (ページネーション対応準備)"""
    statement = (
        select(Label).where(Label.family_id == family_id).offset(skip).limit(limit)
    )
    result = await db.exec(statement)
    labels = result.all()
    return labels


async def create_label(
    db: AsyncSession, *, label_in: LabelCreate, family_id: int, creator_id: int
) -> Label:
    """新しいラベルを作成する (セッションに追加)"""
    label_data = label_in.model_dump()
    db_label = Label(
        **label_data,
        family_id=family_id,
        created_by_id=creator_id,
        updated_by_id=creator_id,  # 作成時は更新者も作成者と同じ
    )
    db.add(db_label)
    await db.flush()
    await db.refresh(db_label)
    return db_label


async def update_label(
    db: AsyncSession, *, db_label: Label, label_in: LabelUpdate, updater_id: int
) -> Label:
    """既存のラベルを更新する (セッション内で更新)"""
    # スキーマから送られてきたデータ(Noneでないものだけ)でモデルを更新
    update_data = label_in.model_dump(exclude_unset=True)
    # 更新者IDも設定
    update_data["updated_by_id"] = updater_id

    # SQLModel v0.0.16+
    db_label.sqlmodel_update(update_data)
    # # または Pydantic V2 スタイル (SQLModelも内部でPydantic使用)
    # for key, value in update_data.items():
    #     setattr(db_label, key, value)

    db.add(db_label)  # セッションに変更を認識させる
    await db.flush()
    await db.refresh(db_label)
    return db_label


async def delete_label(db: AsyncSession, *, db_label: Label) -> None:
    """ラベルを削除する (セッションから削除)"""
    await db.delete(db_label)
    await db.flush()
    # コミットは呼び出し元 (Service層 or リクエストスコープ) で行う
