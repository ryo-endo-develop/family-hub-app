from app.crud import crud_family
from app.db.session import get_db  # DBセッションを取得するための依存関数
from app.schemas.family import FamilyCreate, FamilyRead  # APIスキーマ
from app.schemas.response import APIResponse  # 統一レスポンススキーマ
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession  # セッションの型ヒント用

# from app.models import User # 認証用 (今はまだ使わない)
# from app.api.deps import get_current_active_user # 認証用 (今はまだない)

# APIRouterインスタンスを作成
router = APIRouter()


@router.post(
    "/",  # /api/v1/families/ へのPOSTリクエストに対応
    response_model=APIResponse[FamilyRead],  # レスポンスの型を指定 (統一形式)
    status_code=status.HTTP_201_CREATED,  # 成功時のステータスコード
    summary="Create new family",  # APIドキュメント用の要約
    response_description="Successfully created family",  # APIドキュメント用の説明
)
async def create_new_family(
    *,
    db: AsyncSession = Depends(get_db),  # DBセッションを注入
    family_in: FamilyCreate,  # リクエストボディをFamilyCreateスキーマで受け取りバリデーション
    # current_user: User = Depends(get_current_active_user) # TODO: OIDC認証実装後に追加
) -> APIResponse[FamilyRead]:  # レスポンスの型ヒント
    """
    新しい家族を作成します。

    - **family_name**: 作成する家族の名前 (必須)

    **TODO:**
    - 認証されたユーザーを自動的にこの家族の最初のメンバー（管理者）として
      `family_memberships` テーブルに追加するロジックが必要です。
    """
    # 同名の家族が既に存在しないかチェック (任意だが推奨)
    existing_family = await crud_family.get_family_by_name(
        db, name=family_in.family_name
    )
    if existing_family:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,  # 409 Conflict
            detail="Family with this name already exists.",
        )

    # CRUD関数を呼び出して家族を作成
    new_family = await crud_family.create_family(db=db, family_in=family_in)

    # ★★★ ここに重要なロジックが不足 ★★★
    # 認証されたユーザー (current_user) を FamilyMembership として追加する処理が必要
    # 例: membership_crud.create(db, user_id=current_user.id, family_id=new_family.id, role='admin')

    # 統一レスポンス形式で返す
    return APIResponse[
        FamilyRead
    ](
        data=new_family,  # SQLModelオブジェクトはFamilyReadに変換可能 (from_attributes=True設定済)
        message=f"Family '{new_family.family_name}' created successfully.",
    )


@router.get(
    "/{family_id}",  # /api/v1/families/{family_id} へのGETリクエストに対応
    response_model=APIResponse[FamilyRead],
    summary="Get family by ID",
    response_description="Details of the family",
)
async def read_family(
    *,
    db: AsyncSession = Depends(get_db),
    family_id: int,  # パスパラメータからIDを取得
    # current_user: User = Depends(get_current_active_user) # TODO: OIDC認証実装後に追加
) -> APIResponse[FamilyRead]:
    """
    指定されたIDの家族情報を取得します。

    **TODO:**
    - 認証されたユーザーがこの家族に所属しているかどうかの認可チェックが必要です。
    """
    db_family = await crud_family.get_family(db, family_id=family_id)
    if db_family is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,  # 404 Not Found
            detail="Family not found",
        )

    # ★★★ ここに重要なロジックが不足 ★★★
    # 認証されたユーザー (current_user) が db_family に所属しているかチェックする処理が必要
    # 例: if not membership_crud.is_member(db, user_id=current_user.id, family_id=family_id):
    #         raise HTTPException(status_code=403, detail="Not authorized")

    return APIResponse[FamilyRead](data=db_family)


# TODO: GET /families/ (一覧取得、ページネーション付き) の実装
# TODO: PUT /families/{family_id} (更新) の実装
# TODO: DELETE /families/{family_id} (削除) の実装
