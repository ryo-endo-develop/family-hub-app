import pytest
from app.models.family import Family  # テストデータ準備用
from app.models.family_membership import (  # テストデータ準備用
    FamilyMembership,
    MembershipRole,
)
from app.models.task import TaskType  # Enum
from app.models.user import User  # test_userフィクスチャの型

# --- 必要なモデル、スキーマ、Enumなどをインポート ---
from app.schemas.response import APIResponse
from app.schemas.task import TaskCreate, TaskRead  # 作成・参照スキーマ
from fastapi import status
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession  # DBセッション注入用

# --- Task API のテスト ---


@pytest.mark.asyncio
async def test_create_task_success(
    authenticated_client: AsyncClient,  # 認証済みクライアント (test_user でログイン状態)
    test_user: User,  # test_user オブジェクト (IDなどを参照)
    db_session: AsyncSession,  # DB操作用セッション
):
    """
    テストケース: POST /api/v1/families/{family_id}/tasks/
    正常系: 認証されたユーザーが所属する家族に基本的なタスクを作成できる
    """
    # --- Arrange (準備) ---
    # 1. テスト用の家族を作成し、test_user をメンバーとして追加
    family = Family(family_name=f"Family_for_Task_Test_{test_user.id}")
    db_session.add(family)
    await db_session.flush()  # family.id を確定させるため
    membership = FamilyMembership(
        user_id=test_user.id, family_id=family.id, role=MembershipRole.ADMIN
    )
    db_session.add(membership)
    await db_session.commit()  # このテスト用の前提データをDBに保存
    await db_session.refresh(family)
    family_id = family.id
    print(f"DEBUG [Test]: Created family ID: {family_id} for user ID: {test_user.id}")

    # 2. 作成するタスクのデータを定義 (TaskCreate スキーマを使用)
    task_payload = TaskCreate(
        title="最初のテストタスク",
        notes="これはテストタスクの詳細です。",
        task_type=TaskType.SINGLE,
        # 他のフィールドはデフォルト値を使うか、Noneのまま
        # assignee_id=None, parent_task_id=None, label_ids=None など
    )

    # --- Act (実行) ---
    # 3. APIエンドポイントにPOSTリクエストを送信
    api_url = f"/api/v1/families/{family_id}/tasks/"
    print(
        f"DEBUG [Test]: Posting to {api_url} with payload: {task_payload.model_dump()}"
    )
    response = await authenticated_client.post(api_url, json=task_payload.model_dump())

    # --- Assert (検証) ---
    # 4. ステータスコードの検証
    assert response.status_code == status.HTTP_201_CREATED, (
        f"Expected 201, got {response.status_code}. Response: {response.text}"
    )

    # 5. レスポンスボディの構造検証 (APIResponse と TaskRead)
    try:
        api_response = APIResponse[TaskRead](**response.json())
    except Exception as e:
        pytest.fail(
            f"Response JSON cannot be parsed into APIResponse[TaskRead]: {e}\nResponse text: {response.text}"
        )

    assert api_response.data is not None, "APIResponse 'data' field should not be None"

    # 6. 返却されたタスクデータの内容検証
    created_task = api_response.data
    assert created_task.title == task_payload.title
    assert created_task.notes == task_payload.notes
    assert created_task.task_type == task_payload.task_type
    assert created_task.is_done is False  # デフォルト値
    assert created_task.id is not None  # IDが採番されている
    assert created_task.family_id == family_id  # 正しい家族に紐づいている
    assert created_task.created_at is not None
    assert created_task.updated_at is not None
    assert created_task.assignee is None  # 今回は指定していないのでNoneのはず
    assert created_task.labels == []  # 今回は指定していないので空リストのはず
    assert created_task.parent_task_id is None  # サブタスクではない

    print(f"DEBUG [Test]: Task created successfully with ID: {created_task.id}")

    # 7. (任意) DBを直接確認するアサーション (スピード重視なら省略可)
    # db_task = await db_session.get(Task, created_task.id)
    # assert db_task is not None
    # assert db_task.title == task_payload.title
    # assert db_task.created_by_id == test_user.id # creator_id が設定されているかなど
