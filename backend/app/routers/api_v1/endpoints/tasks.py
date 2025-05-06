import logging

from fastapi import APIRouter, Depends, Path, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import CurrentUser  # 認証済みユーザー取得用
from app.db.session import get_db
from app.schemas.label import LabelSummary
from app.schemas.response import APIResponse

# --- 必要なスキーマ、依存関係などをインポート ---
from app.schemas.task import RoutineSettings, TaskCreate, TaskRead
from app.schemas.user import UserSummary
from app.services import task_service

# --- Task用ルーターを作成 ---
router = APIRouter()

logger = logging.getLogger(__name__)
# --- エンドポイント定義 ---


@router.post(
    "/",  # /api/v1/families/{family_id}/tasks/ へのPOST
    response_model=APIResponse[TaskRead],
    status_code=status.HTTP_201_CREATED,
    summary="Create new task",
    response_description="The created task",
)
async def create_new_task(
    *,
    family_id: int = Path(..., title="The ID of the family this task belongs to"),
    task_in: TaskCreate,  # リクエストボディ
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser,
):
    """
    指定された家族内に新しいタスクを作成します。
    ユーザーはその家族のメンバーである必要があります。
    """
    logger.info(f"Router received request to create task in family {family_id}")

    # Service層を呼び出し、複数のオブジェクトを受け取る
    db_task, assignee_obj, label_objs = await task_service.create_task_for_family(
        db=db, task_in=task_in, family_id=family_id, user=current_user
    )

    # --- レスポンス用 TaskRead オブジェクトを手動で構築 ---
    logger.info(f"Constructing TaskRead response for task ID {db_task.id}")

    # 担当者情報をサマリーに変換
    assignee_summary = (
        UserSummary.model_validate(assignee_obj) if assignee_obj else None
    )

    # ラベル情報をサマリーのリストに変換
    label_summaries = [LabelSummary.model_validate(lbl) for lbl in label_objs]
    label_ids = [lbl.id for lbl in label_objs if lbl.id is not None]  # IDのリストも作成

    # routine_settings をスキーマオブジェクトに変換 (存在すれば)
    routine_settings_obj = None
    if db_task.routine_settings:
        try:
            routine_settings_obj = RoutineSettings.model_validate(
                db_task.routine_settings
            )
        except Exception as e:
            logger.warning(
                f"Failed to validate routine_settings for task {db_task.id}: {e}. Returning raw dict/None."
            )
            # エラーの場合はNoneにするか、あるいは元の辞書をそのまま返すか検討
            # ここではNoneにする
            routine_settings_obj = None

    # TaskReadオブジェクトを作成
    task_read_data = TaskRead(
        id=db_task.id,
        title=db_task.title,
        notes=db_task.notes,
        is_done=db_task.is_done,
        task_type=db_task.task_type,
        due_date=db_task.due_date,
        priority=db_task.priority,
        routine_settings=routine_settings_obj,
        created_at=db_task.created_at,
        updated_at=db_task.updated_at,
        assignee=assignee_summary,  # ★ 変換したサマリーを設定
        labels=label_summaries,  # ★ 変換したサマリーリストを設定
        label_ids=label_ids,  # ★ IDリストを設定
        family_id=db_task.family_id,
        parent_task_id=db_task.parent_task_id,
    )

    logger.info(f"Task {task_read_data.id} processed, returning response.")
    return APIResponse[TaskRead](
        data=task_read_data, message="Task created successfully."
    )
