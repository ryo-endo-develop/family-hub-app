import logging

from sqlmodel import delete
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.task_label import TaskLabel

logger = logging.getLogger(__name__)


async def add_label_to_task(
    db: AsyncSession, *, task_id: int, label_id: int
) -> TaskLabel:
    """TaskとLabelの関連を作成し、セッションに追加・フラッシュする"""
    logger.debug(f"Adding link between task {task_id} and label {label_id}")
    # すでに存在するかチェックはしない（DBの主キー制約に任せる）
    db_link = TaskLabel(task_id=task_id, label_id=label_id)
    db.add(db_link)

    try:
        await db.flush()
        # refreshは必須ではないことが多い (複合主キーのみのため)
        # await db.refresh(db_link)
    except Exception as e:
        # 主キー制約違反 (すでにリンクが存在する) など
        logger.error(
            f"Error flushing TaskLabel link for task {task_id}, label {label_id}: {e}",
            exc_info=True,
        )
        # ロールバックは呼び出し元 (get_db) が担当
        raise
    return db_link


async def delete_labels_for_task(db: AsyncSession, *, task_id: int) -> int:
    """特定のTaskに関連する全てのLabel関連を削除し、フラッシュする。削除件数を返す。"""
    logger.debug(f"Deleting all label links for task {task_id}")
    statement = delete(TaskLabel).where(TaskLabel.task_id == task_id)
    try:
        result = await db.execute(statement)
        await db.flush()  # 削除をDBに反映させる
        deleted_count = result.rowcount
        logger.debug(f"Deleted {deleted_count} label links for task {task_id}")
        return deleted_count
    except Exception as e:
        logger.error(
            f"Error deleting TaskLabel links for task {task_id}: {e}", exc_info=True
        )
        raise
