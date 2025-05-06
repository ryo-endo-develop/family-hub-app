from typing import List, Sequence

from fastapi import APIRouter, Depends, Path, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import CurrentUser
from app.db.session import get_db
from app.models.label import Label
from app.schemas.label import LabelCreate, LabelRead, LabelUpdate
from app.schemas.response import APIResponse
from app.services import label_service

# Label用のルーターを作成
router = APIRouter()

# --- エンドポイント定義 ---


@router.post(
    "/",  # /families/{family_id}/labels/ への POST
    response_model=APIResponse[LabelRead],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new label for a family",
    response_description="Successfully created label",
)
async def create_new_label(
    *,
    # パスパラメータから family_id を受け取る
    family_id: int = Path(..., title="The ID of the family to add the label to"),
    label_in: LabelCreate,  # リクエストボディ
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser,  # 認証済みユーザー
) -> APIResponse[LabelRead]:
    """
    指定された家族に新しいラベルを作成します。
    ユーザーはその家族のメンバーである必要があります。
    """
    # Service層を呼び出し (認可チェック・重複チェックはService内で行われる)
    new_label = await label_service.create_label_for_family(
        db=db, label_in=label_in, family_id=family_id, user=current_user
    )
    return APIResponse[LabelRead](
        data=new_label, message=f"Label '{new_label.name}' created successfully."
    )


@router.get(
    "/",  # /families/{family_id}/labels/ への GET
    response_model=APIResponse[List[LabelRead]],  # ラベルのリストを返す
    summary="List labels for a family",
    response_description="List of labels belonging to the family",
)
async def read_labels(
    *,
    family_id: int = Path(..., title="The ID of the family to list labels for"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser,
    skip: int = Query(0, ge=0, title="Skip", description="スキップするアイテム数"),
    limit: int = Query(
        100, ge=1, le=500, title="Limit", description="取得する最大アイテム数 (最大500)"
    ),  # 例: 1件以上、500件以下に制限
) -> APIResponse[List[LabelRead]]:
    """
    指定された家族に属するラベルのリストを取得します。
    ユーザーはその家族のメンバーである必要があります。
    """
    # Service層を呼び出し (認可チェックはService内)
    labels: Sequence[Label] = await label_service.get_labels_for_family(
        db=db, family_id=family_id, user=current_user, skip=skip, limit=limit
    )
    # Sequence[Label] を List[LabelRead] に変換する必要があるか？
    # SQLModelを継承している場合、そのまま返せる場合が多い
    # Pydantic V2 + SQLModelでは data=list(labels) のようにリスト化が必要な場合も
    return APIResponse[List[LabelRead]](data=list(labels))  # 安全のため list() で変換


@router.get(
    "/{label_id}",  # /families/{family_id}/labels/{label_id} への GET
    response_model=APIResponse[LabelRead],
    summary="Get a specific label",
    response_description="Details of the specific label",
)
async def read_label(
    *,
    family_id: int = Path(..., title="The ID of the family"),
    label_id: int = Path(..., title="The ID of the label to retrieve"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser,
) -> APIResponse[LabelRead]:
    """
    指定された家族内の特定のラベルを取得します。
    ユーザーはその家族のメンバーである必要があります。
    """
    # Service層を呼び出し (認可・存在チェックはService内)
    db_label = await label_service.get_label_for_family_user_or_404(
        db=db, label_id=label_id, family_id=family_id, user=current_user
    )
    return APIResponse[LabelRead](data=db_label)


@router.put(
    "/{label_id}",  # /families/{family_id}/labels/{label_id} への PUT
    response_model=APIResponse[LabelRead],
    summary="Update a label",
    response_description="The updated label information",
)
async def update_existing_label(
    *,
    family_id: int = Path(..., title="The ID of the family"),
    label_id: int = Path(..., title="The ID of the label to update"),
    label_in: LabelUpdate,  # リクエストボディ
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser,
) -> APIResponse[LabelRead]:
    """
    指定されたラベルを更新します。
    ユーザーはその家族のメンバーである必要があります。
    """
    # Service層を呼び出し (認可・存在・重複チェックはService内)
    updated_label = await label_service.update_label_for_family_user(
        db=db,
        label_id=label_id,
        label_in=label_in,
        family_id=family_id,
        user=current_user,
    )
    return APIResponse[LabelRead](
        data=updated_label, message="Label updated successfully."
    )


@router.delete(
    "/{label_id}",  # /families/{family_id}/labels/{label_id} への DELETE
    response_model=APIResponse[None],  # データは返さない
    status_code=status.HTTP_200_OK,  # または 204 No Content
    summary="Delete a label",
    response_description="Label deleted successfully",
)
async def delete_existing_label(
    *,
    family_id: int = Path(..., title="The ID of the family"),
    label_id: int = Path(..., title="The ID of the label to delete"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser,
) -> APIResponse[None]:
    """
    指定されたラベルを削除します。
    ユーザーはその家族のメンバーである必要があります。
    """
    # Service層を呼び出し (認可・存在チェックはService内)
    await label_service.delete_label_for_family_user(
        db=db, label_id=label_id, family_id=family_id, user=current_user
    )
    # 成功時はデータなし、メッセージ付きのレスポンスを返す
    return APIResponse[None](success=True, message="Label deleted successfully.")
