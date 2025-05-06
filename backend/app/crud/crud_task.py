import logging

from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.task import Task
from app.schemas.task import TaskCreate

logger = logging.getLogger(__name__)


async def create_task(
    db: AsyncSession, *, task_in: TaskCreate, family_id: int, creator_id: int
) -> Task:
    """Taskオブジェクトを作成し、セッションに追加する (骨組み)"""
    logger.info(
        f"Creating task '{task_in.title}' for family {family_id} by user {creator_id}"
    )

    # TaskCreateスキーマからTaskモデルに変換する際、label_idsは除く
    # (ラベルの関連付けはService層で別途行うため)
    # routine_settingsはスキーマ(RoutineSettings)からDictに変換が必要か？
    # -> DBモデル側はJSON(Dict)を期待しているので、スキーマからDictに変換する
    # routine_settings が None でない場合、 Pydanticモデルから辞書に変換
    task_data_dict = task_in.model_dump(exclude={"label_ids"})
    if task_data_dict.get("routine_settings") is not None:
        # Pydantic v2 では .model_dump() を使う
        task_data_dict["routine_settings"] = task_in.routine_settings.model_dump()

    # Taskモデルインスタンスを作成
    db_task = Task(
        **task_data_dict,
        family_id=family_id,
        created_by_id=creator_id,
        updated_by_id=creator_id,  # 作成時は更新者も作成者と同じ
    )

    # セッションに追加
    db.add(db_task)

    try:
        # DBにINSERT文を送信し、IDなどを確定させる
        await db.flush()
        # DBから最新の状態（自動採番ID、デフォルト値など）をオブジェクトに反映させる
        await db.refresh(db_task)
        logger.info(f"Task '{db_task.title}' (ID: {db_task.id}) flushed to session.")
    except Exception as e:
        # DBエラーが発生したらログに残し、エラーを再送出 (rollbackはget_dbが行う)
        logger.error(
            f"Error during flush/refresh for task '{task_in.title}': {e}", exc_info=True
        )
        raise
    return db_task


# --- 他のCRUD関数 (get_task, get_tasks_by_family, update_task, delete_task) の骨組みも後で追加 ---
