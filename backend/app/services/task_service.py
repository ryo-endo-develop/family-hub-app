import logging
from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.crud import crud_label, crud_membership, crud_task, crud_task_label, crud_user
from app.models.label import Label
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskCreate

from .common import check_user_family_membership_or_raise

logger = logging.getLogger(__name__)


async def create_task_for_family(
    db: AsyncSession, *, task_in: TaskCreate, family_id: int, user: User
) -> Tuple[Task, Optional[User], List[Label]]:
    """
    タスクを作成し、担当者やラベルを（指定があれば）紐付け、関連オブジェクトを返す。
    トランザクション管理は get_db に任せる。
    """
    # 1. 認可チェック
    await check_user_family_membership_or_raise(
        db, user_id=user.id, family_id=family_id
    )
    logger.info(f"User {user.id} authorized for family {family_id} to create task.")

    # 2. 基本的なタスクオブジェクトを作成 (add + flush)
    db_task = await crud_task.create_task(
        db=db, task_in=task_in, family_id=family_id, creator_id=user.id
    )
    logger.info(f"Task '{db_task.title}' (ID: {db_task.id}) base created in session.")

    assignee_obj: Optional[User] = None
    label_objs: List[Label] = []

    # 3. 担当者の処理 (もし指定されていれば)
    if task_in.assignee_id is not None:
        logger.info(
            f"Processing assignee ID: {task_in.assignee_id} for task {db_task.id}"
        )
        # 担当者ユーザーを取得
        assignee_obj = await crud_user.get_user(db, user_id=task_in.assignee_id)
        if not assignee_obj:
            await db.rollback()  # ★ エラー発生時はロールバック推奨
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,  # 404 または 422 が適切か
                detail=f"Assignee user with ID {task_in.assignee_id} not found.",
            )
        # 担当者も同じ家族のメンバーか確認 (セキュリティ上重要)
        is_assignee_member = await crud_membership.is_user_member(
            db, user_id=assignee_obj.id, family_id=family_id
        )
        if not is_assignee_member:
            await db.rollback()  # ★ エラー発生時はロールバック推奨
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,  # 意味的には422が近いか
                detail=f"Assignee user {assignee_obj.id} is not a member of family {family_id}.",
            )
        # Taskモデルのassignee_idはcrud_task.create_task内で設定済みのはずだが、
        # assignee_objを返すためにここで取得・検証する
        logger.info(f"Assignee user {assignee_obj.id} validated for task {db_task.id}")
    else:
        # assignee_id が None の場合、Task モデルの assignee_id も None であることを確認 (create_task内で処理されるはず)
        logger.info(f"No assignee specified for task {db_task.id}")

    # 4. ラベルの処理 (もし指定されていれば)
    if task_in.label_ids:
        label_ids = list(set(task_in.label_ids))  # 重複を除去
        logger.info(f"Processing label IDs: {label_ids} for task {db_task.id}")
        if label_ids:  # 空リストでない場合のみ処理
            # 指定されたIDのラベルが全て存在し、かつ同じ家族に属するか確認
            fetched_labels = await crud_label.get_labels_by_ids_and_family(
                db, label_ids=label_ids, family_id=family_id
            )
            if len(fetched_labels) != len(label_ids):
                await db.rollback()  # ★ エラー発生時はロールバック推奨
                found_ids = {lbl.id for lbl in fetched_labels}
                missing_ids = set(label_ids) - found_ids
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,  # 存在しないIDが含まれるので404
                    detail=f"Labels not found or do not belong to family {family_id}: {missing_ids}",
                )

            # TaskとLabelを紐付ける (add + flush in CRUD)
            for label in fetched_labels:
                await crud_task_label.add_label_to_task(
                    db=db, task_id=db_task.id, label_id=label.id
                )

            label_objs = list(fetched_labels)  # 返却用にリストを保持
            logger.info(
                f"Successfully linked {len(label_objs)} labels to task {db_task.id}"
            )
        else:
            logger.info(f"Empty label_ids list provided for task {db_task.id}")
    else:
        logger.info(f"No labels specified for task {db_task.id}")

    # 5. 関連オブジェクトも含めてタプルで返す
    #    コミットは get_db が担当する
    logger.info(f"Returning created task {db_task.id} with assignee and labels.")
    return db_task, assignee_obj, label_objs


# --- 他のサービス関数 (get_tasks_for_family など) の骨組みも後で追加 ---
