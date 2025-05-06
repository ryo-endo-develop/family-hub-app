from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import CurrentUser  # ★ 型ヒント付きの認証依存関係を使用
from app.db.session import get_db
from app.schemas.family import FamilyCreate, FamilyRead
from app.schemas.response import APIResponse
from app.services import family_service

router = APIRouter()


@router.post(
    "/",
    response_model=APIResponse[FamilyRead],
    status_code=status.HTTP_201_CREATED,
    summary="Create new family",
    response_description="Successfully created family",
)
async def create_new_family(
    *,
    db: AsyncSession = Depends(get_db),
    family_in: FamilyCreate,
    current_user: CurrentUser,  # ★ 認証されたユーザーを取得
) -> APIResponse[FamilyRead]:
    """
    新しい家族を作成し、現在のユーザーをオーナーとして追加します。
    """
    new_family = await family_service.create_family_with_owner(
        db=db, family_in=family_in, owner_user=current_user
    )
    return APIResponse[FamilyRead](
        data=new_family,
        message=f"Family '{new_family.family_name}' created successfully.",
    )


@router.get(
    "/{family_id}",
    response_model=APIResponse[FamilyRead],
    summary="Get family by ID",
    response_description="Details of the family",
)
async def read_family(
    *,
    db: AsyncSession = Depends(get_db),
    family_id: int,
    current_user: CurrentUser,  # ★ 認証されたユーザーを取得
) -> APIResponse[FamilyRead]:
    """
    指定されたIDの家族情報を取得します (ユーザーがメンバーの場合のみ)。
    """
    db_family = await family_service.get_family_for_user_or_404(
        db=db, family_id=family_id, user=current_user
    )
    return APIResponse[FamilyRead](data=db_family)


# TODO: Implement GET /families/ (list) using service layer + pagination library
# TODO: Implement PUT /families/{family_id} using service layer
# TODO: Implement DELETE /families/{family_id} using service layer
