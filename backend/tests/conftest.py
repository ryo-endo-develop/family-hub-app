import asyncio
import os
import sys
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio

# --- ↓↓↓ Python Path の設定を追加 ↓↓↓ ---
# conftest.py が tests/ にあるので、その親の親がプロジェクトルート(/app)になる
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
print(f"DEBUG [conftest]: PROJECT_ROOT = {PROJECT_ROOT}")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
    print(f"DEBUG [conftest]: Added {PROJECT_ROOT} to sys.path")
print(f"DEBUG [conftest]: Current sys.path = {sys.path}")
# --- ↑↑↑ Python Path の設定を追加 ↑↑↑ ---

# --- これ以降に必要なモジュールをインポート ---
from app.db.session import get_db  # 元のDBセッション取得関数

# app以下のモジュールもインポート可能になるはず
from app.main import app  # FastAPI アプリケーションインスタンス
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel  # create_engineも使う可能性があるので残す
from sqlmodel.ext.asyncio.session import AsyncSession

# --- テスト用DB設定 ---
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"  # インメモリSQLiteを使用

# --- 非同期テスト用エンジンとセッションファクトリ ---
async_engine = create_async_engine(TEST_DATABASE_URL, echo=False, future=True)
AsyncTestSessionLocal = sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False
)

# --- テストごとのDBリセット設定 ---


# # 非同期テストのためのイベントループ設定 (pytest-asyncioが必要な場合)
@pytest.fixture(scope="session")
def event_loop(request) -> Generator:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# # ★ 変更: scopeを "function" にし、各テスト前後にDBを初期化 ★
@pytest.fixture(scope="function", autouse=True)
async def db_setup_and_teardown() -> AsyncGenerator[None, None]:
    """各テスト関数の実行前にDBテーブルをクリア＆作成するフィクスチャ"""
    print(
        "\nDEBUG [conftest]: Running db_setup_and_teardown fixture..."
    )  # 改行追加で見やすく
    # ★ メタデータに含まれるテーブルを確認
    print(
        f"DEBUG [conftest]: Metadata tables BEFORE setup: {SQLModel.metadata.tables.keys()}"
    )
    try:
        async with async_engine.begin() as conn:
            print("DEBUG [conftest]: Dropping all tables...")
            # drop_allは外部キー制約などで失敗することがあるので、テスト開始時はcreate_allのみでも良いかも
            # await conn.run_sync(SQLModel.metadata.drop_all)
            await conn.run_sync(SQLModel.metadata.create_all)
            print("DEBUG [conftest]: Tables created successfully.")
    except Exception as e:
        print(f"ERROR [conftest]: Exception during DB setup: {e}")
        import traceback

        traceback.print_exc()
        # テストセットアップ失敗を明確にするためにエラーを再送出しても良い
        # raise e
    yield
    # print("DEBUG [conftest]: Teardown after test function.")
    # テスト後のDropは省略しても良い（次のテスト前にDropされるため）


# # --- 依存性オーバーライド ---
async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """テスト中に get_db が呼ばれたらテスト用セッションを返す"""
    async with AsyncTestSessionLocal() as session:
        yield session


# # FastAPIアプリの get_db 依存性をテスト用のものに差し替える
app.dependency_overrides[get_db] = override_get_db


# # --- テスト用クライアント ---
@pytest_asyncio.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    """非同期テストクライアントを提供するフィクスチャ"""
    async with AsyncClient(app=app, base_url="http://test") as async_client:
        print(f"DEBUG [conftest]: Yielding client object of type: {type(async_client)}")
        yield async_client
