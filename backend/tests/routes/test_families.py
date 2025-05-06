import pytest
from app.models.family import Family
from app.models.family_membership import FamilyMembership, MembershipRole
from app.models.user import User
from app.schemas.family import FamilyCreate, FamilyRead

# 統一レスポンススキーマとFamilyスキーマをインポート
from app.schemas.response import APIResponse
from fastapi import status
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

# --- Family API のテスト ---


@pytest.mark.asyncio
async def test_create_family_success(authenticated_client: AsyncClient):
    """家族作成API (POST /families/) の正常系テスト (認証ユーザー使用)"""
    # authenticated_clientを使うことで、test_userが作成され、
    # get_current_active_userがそのユーザーを返す状態になっている。
    family_data = FamilyCreate(family_name="Test Family Created by Auth User")
    response = await authenticated_client.post(  # ★ authenticated_client を使用
        "/api/v1/families/", json=family_data.model_dump()
    )

    # アサーション
    assert response.status_code == status.HTTP_201_CREATED
    api_response = APIResponse[FamilyRead](**response.json())
    assert api_response.data is not None
    assert api_response.data.family_name == family_data.family_name
    assert api_response.data.id is not None
    # TODO: DBを直接確認して、FamilyMembershipも作成されているかアサーションを追加するとより良い


@pytest.mark.asyncio
async def test_create_family_duplicate_name(
    authenticated_client: AsyncClient, db_session: AsyncSession
):
    """家族作成API - 重複名でのエラーテスト"""
    # 1. 最初の家族を作成（API経由で）
    family_name = "Test Family Duplicate Name Check"
    family_data = FamilyCreate(family_name=family_name)
    response1 = await authenticated_client.post(
        "/api/v1/families/", json=family_data.model_dump()
    )
    assert response1.status_code == status.HTTP_201_CREATED

    # 2. 同じ名前で再度作成しようとする
    response2 = await authenticated_client.post(
        "/api/v1/families/", json=family_data.model_dump()
    )
    # 409 Conflict エラーが返ることを期待
    assert response2.status_code == status.HTTP_409_CONFLICT
    error_data = response2.json()
    assert "detail" in error_data
    assert "already exists" in error_data["detail"]


@pytest.mark.asyncio
async def test_read_family_success(
    authenticated_client: AsyncClient, test_user: User, db_session: AsyncSession
):
    """家族取得API (GET /families/{id}) の正常系テスト"""
    # 1. テストデータ準備: test_user が所属する家族を直接DBに作成
    family = Family(family_name="Family To Read")
    db_session.add(family)
    await db_session.flush()  # family.id を確定させる
    membership = FamilyMembership(
        user_id=test_user.id, family_id=family.id, role=MembershipRole.MEMBER
    )
    db_session.add(membership)
    await db_session.commit()  # このテスト用のデータをコミット
    await db_session.refresh(family)
    family_id = family.id

    # 2. 作成した家族のIDで取得APIを叩く
    response = await authenticated_client.get(f"/api/v1/families/{family_id}")

    # 3. 結果を検証
    assert response.status_code == status.HTTP_200_OK
    api_response = APIResponse[FamilyRead](**response.json())
    assert api_response.data is not None
    assert api_response.data.id == family_id
    assert api_response.data.family_name == family.family_name


@pytest.mark.asyncio
async def test_read_family_not_found(authenticated_client: AsyncClient):
    """家族取得API - 存在しないIDでのエラーテスト"""
    non_existent_id = 99999
    response = await authenticated_client.get(f"/api/v1/families/{non_existent_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    error_data = response.json()
    assert "detail" in error_data
    assert "not found" in error_data["detail"]


@pytest.mark.asyncio
async def test_read_family_not_member(
    authenticated_client: AsyncClient, db_session: AsyncSession
):
    """家族取得API - メンバーでない家族へのアクセスエラーテスト (403)"""
    # authenticated_client により、test_userでの認証状態がシミュレートされる

    # 1. 別の家族をDBに直接作成 (test_user はメンバーにしない)
    other_family = Family(family_name="Another User's Family")
    db_session.add(other_family)
    await db_session.commit()
    await db_session.refresh(other_family)
    other_family_id = other_family.id

    # 2. test_user としてその家族にアクセスしようとする
    response = await authenticated_client.get(f"/api/v1/families/{other_family_id}")

    # 3. 403 Forbidden が返ることを確認
    assert response.status_code == status.HTTP_403_FORBIDDEN
    error_data = response.json()
    assert "detail" in error_data
    assert "Not authorized" in error_data["detail"]
