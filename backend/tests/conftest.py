import asyncio
import datetime
import os
import sys
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from app.api.deps import get_current_active_user
from app.db.session import get_db  # 元のDBセッション取得関数
from app.main import app
from app.models.user import User
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

# --- Path設定 (最初に実行) ---
# conftest.py が tests/ にあるので、その親の親がプロジェクトルート(/app)になる
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
print(f"DEBUG [conftest]: PROJECT_ROOT = {PROJECT_ROOT}")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
    print(f"DEBUG [conftest]: Added {PROJECT_ROOT} to sys.path")
print(f"DEBUG [conftest]: Current sys.path = {sys.path}")


# --- テスト用DB設定 ---
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"  # インメモリSQLiteを使用
async_engine = create_async_engine(TEST_DATABASE_URL, echo=False, future=True)
AsyncTestSessionLocal = sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False
)


# --- Fixture: 非同期テスト用イベントループ (sessionスコープ) ---
@pytest.fixture(scope="session")
def event_loop(request) -> Generator:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# --- Fixture: 各テスト前にDBテーブルを初期化 (functionスコープ, 自動実行) ---
@pytest_asyncio.fixture(scope="function", autouse=True)
async def db_setup_fixture() -> AsyncGenerator[None, None]:
    """(Auto-used) Drops and creates tables before each test function."""
    print("\nDEBUG [conftest]: Running db_setup_fixture (drop/create)...")
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)
    print("DEBUG [conftest]: Tables created by db_setup_fixture.")
    yield


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provides a clean database session for each test function."""
    # db_setup_fixture が autouse=True なので、このフィクスチャが呼ばれる前に実行されている
    print("DEBUG [conftest]: Creating db_session for test...")
    async with AsyncTestSessionLocal() as session:
        try:
            yield session
            # ここではコミット/ロールバックしない。テストや他のフィクスチャが必要に応じて行う。
        except Exception:
            await session.rollback()  # テスト中に例外が発生したらロールバック
            raise
    print("DEBUG [conftest]: db_session closed.")


# --- 依存性オーバーライド ---
@pytest_asyncio.fixture(scope="function", autouse=True)  # 自動で適用
def override_get_db_in_app(db_session: AsyncSession):  # テスト用セッションに依存
    """Overrides the 'get_db' dependency in the FastAPI app instance."""
    print("DEBUG [conftest]: Overriding get_db dependency...")

    # get_db が呼ばれたら、このテスト関数用に用意された db_session を返す
    # (自動コミット/ロールバックは get_db ではなく、ここで提供される db_session を使う処理に依存)
    # → アプリケーション側は get_db がトランザクション管理すると期待しているので、
    #   オーバーライドする関数もその挙動を模倣する必要がある。
    #   なので、前の override_get_db の実装が適切。db_session は直接使わない。
    async def override_get_db_for_req() -> AsyncGenerator[AsyncSession, None]:
        async with (
            AsyncTestSessionLocal() as session
        ):  # 新しいセッションをリクエストごとに作る
            try:
                yield session
                await session.commit()
                # print("DEBUG [override_get_db]: Transaction committed.")
            except Exception:
                # print("DEBUG [override_get_db]: Rolling back transaction.")
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db_for_req
    yield  # テスト実行
    # テスト終了後にオーバーライドを解除
    print("DEBUG [conftest]: Clearing dependency override.")
    del app.dependency_overrides[get_db]


# --- テスト用クライアント ---
@pytest_asyncio.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    """非同期テストクライアントを提供するフィクスチャ"""
    async with AsyncClient(app=app, base_url="http://test") as async_client:
        print(f"DEBUG [conftest]: Yielding client object of type: {type(async_client)}")
        yield async_client


# --- Fixture: テスト用ユーザー作成 (functionスコープ) ---
@pytest_asyncio.fixture(scope="function")  # テスト関数ごとにユーザーを作成
async def test_user(db_session: AsyncSession) -> User:  # DBセッションフィクスチャに依存
    """テスト関数内で使用するテストユーザーを作成し、DBに保存して返すフィクスチャ"""
    # 毎回違うユーザーにするためにユニークな情報を使う（任意）
    now_ts = datetime.datetime.now().timestamp()
    user_data = User(
        oidc_subject=f"test_oidc|{now_ts}",
        email=f"test_{now_ts}@example.com",
        name="Test User Fixture",
    )
    db_session.add(user_data)
    # ★重要: test_userフィクスチャ内でコミットする
    # これにより、このユーザーがDBに確実に存在し、他のフィクスチャやテスト関数から利用可能になる
    await db_session.commit()
    await db_session.refresh(user_data)
    print(f"DEBUG [conftest]: Created test_user with ID: {user_data.id}")
    return user_data


@pytest_asyncio.fixture(scope="function")  # テスト関数ごとに設定・解除
async def authenticated_client(
    client: AsyncClient,  # 元の（認証されていない）クライアントフィクスチャに依存
    test_user: User,  # 作成されたテストユーザーフィクスチャに依存
) -> AsyncClient:
    """
    指定された test_user がログインしている状態をシミュレートする
    FastAPI TestClient を提供するフィクスチャ。
    """

    # get_current_active_userが常にtest_userを返すように上書きする関数を定義
    def override_get_current_user_for_test() -> User:
        return test_user

    # FastAPIアプリの依存関係上書き機能を使って差し替える
    app.dependency_overrides[get_current_active_user] = (
        override_get_current_user_for_test
    )

    # 上書きが適用された状態で、元のクライアントをテスト関数に渡す
    yield client

    # --- テスト関数終了後の後片付け ---
    # 必ず依存関係の上書きを元に戻す（他のテストに影響を与えないため）
    del app.dependency_overrides[get_current_active_user]
