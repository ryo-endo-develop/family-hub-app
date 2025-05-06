import pytest
from app.schemas.family import FamilyCreate, FamilyRead

# 統一レスポンススキーマとFamilyスキーマをインポート
from app.schemas.response import APIResponse
from fastapi import status
from httpx import AsyncClient

# --- Family API のテスト ---

# pytest-asyncio を使う場合、テスト関数を async def にする
# pip install pytest-asyncio が必要になる場合がある
# pytest.mark.asyncio をつける


@pytest.mark.asyncio
async def test_create_family_success(client: AsyncClient):
    """家族作成API (POST /families/) の正常系テスト"""
    family_data = FamilyCreate(family_name="Test Family One")
    response = await client.post(
        "/api/v1/families/",
        json=family_data.model_dump(),  # Pydantic V2
    )
    assert response.status_code == status.HTTP_201_CREATED
    # 統一レスポンス形式で返ってくることを確認
    api_response = APIResponse[FamilyRead](**response.json())
    assert api_response.message is not None
    assert api_response.data is not None
    # dataの中身を確認 (FamilyRead型)
    assert api_response.data.family_name == family_data.family_name
    assert api_response.data.id is not None  # IDが採番されていること
    assert api_response.data.created_at is not None


@pytest.mark.asyncio
async def test_create_family_duplicate_name(client: AsyncClient):
    """家族作成API - 重複名でのエラーテスト"""
    # 1. 最初の家族を作成
    family_data = FamilyCreate(family_name="Test Family Duplicate")
    response1 = await client.post("/api/v1/families/", json=family_data.model_dump())
    assert response1.status_code == status.HTTP_201_CREATED

    # 2. 同じ名前で再度作成しようとする
    response2 = await client.post("/api/v1/families/", json=family_data.model_dump())
    # 409 Conflict エラーが返ることを期待
    assert response2.status_code == status.HTTP_409_CONFLICT
    error_data = response2.json()
    assert "detail" in error_data
    assert "already exists" in error_data["detail"]


@pytest.mark.asyncio
async def test_read_family_success(client: AsyncClient):
    """家族取得API (GET /families/{id}) の正常系テスト"""
    # 1. テスト用家族を作成
    family_data = FamilyCreate(family_name="Test Family Read")
    create_response = await client.post(
        "/api/v1/families/", json=family_data.model_dump()
    )
    created_family_data = APIResponse[FamilyRead](**create_response.json()).data
    assert created_family_data is not None
    family_id = created_family_data.id

    # 2. 作成した家族のIDで取得APIを叩く
    response = await client.get(f"/api/v1/families/{family_id}")

    # 3. 結果を検証
    assert response.status_code == status.HTTP_200_OK
    api_response = APIResponse[FamilyRead](**response.json())
    assert api_response.data is not None
    assert api_response.data.id == family_id
    assert api_response.data.family_name == family_data.family_name


@pytest.mark.asyncio
async def test_read_family_not_found(client: AsyncClient):
    """家族取得API - 存在しないIDでのエラーテスト"""
    non_existent_id = 99999
    response = await client.get(f"/api/v1/families/{non_existent_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    error_data = response.json()
    assert "detail" in error_data
    assert "not found" in error_data["detail"]
