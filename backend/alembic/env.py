# alembic/env.py (デバッグ強化版)
import asyncio
import os
import sys
import traceback  # エラー詳細表示用
from logging.config import fileConfig

from alembic import context
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel

# --- ↓↓↓ パス設定とデバッグ出力 ↓↓↓ ---
# env.py自身の絶対パス
env_py_path = os.path.abspath(__file__)
# alembicディレクトリの絶対パス
alembic_dir = os.path.dirname(env_py_path)
# プロジェクトルートの絶対パス (alembicディレクトリの親)
project_root = os.path.dirname(alembic_dir)

print("--- Alembic env.py Debug Info ---")
print(f"env.py Path: {env_py_path}")
print(f"Alembic Dir: {alembic_dir}")
print(f"Project Root: {project_root}")
print(f"Initial sys.path: {sys.path}")

# プロジェクトルートをsys.pathの先頭に追加 (存在しなければ)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"Added to sys.path: {project_root}")
print(f"Modified sys.path: {sys.path}")

# .env ファイルの読み込み
dotenv_path = os.path.join(project_root, ".env")
if os.path.exists(dotenv_path):
    loaded = load_dotenv(dotenv_path)
    print(f"Loaded .env from {dotenv_path}: {loaded}")
else:
    print(f"WARNING: .env file not found at {dotenv_path}")

# --- ファイル存在チェック ---
app_package_path = os.path.join(project_root, "app")
app_init_path = os.path.join(app_package_path, "__init__.py")
models_package_path = os.path.join(app_package_path, "models")
models_init_path = os.path.join(models_package_path, "__init__.py")
family_model_path = os.path.join(models_package_path, "family.py")

print(f"Checking path: {app_package_path} - Exists? {os.path.exists(app_package_path)}")
print(f"Checking path: {app_init_path} - Exists? {os.path.exists(app_init_path)}")
print(
    f"Checking path: {models_package_path} - Exists? {os.path.exists(models_package_path)}"
)
print(f"Checking path: {models_init_path} - Exists? {os.path.exists(models_init_path)}")
print(
    f"Checking path: {family_model_path} - Exists? {os.path.exists(family_model_path)}"
)

# --- モデルと設定のインポート試行 ---
target_metadata = None  # 初期化
settings = None  # 初期化

try:
    print("Attempting to import models...")
    import app.models.family  # noqa: F401
    import app.models.family_membership  # noqa: F401
    import app.models.label  # noqa: F401 # 追加
    import app.models.task  # noqa: F401 # 追加
    import app.models.task_label  # noqa: F401 # 追加
    import app.models.user  # noqa: F401

    # 他のモデルも後でここに追加
    print("Models potentially imported (due to noqa, actual use determines success)")
    # メタデータ設定はインポート成功後に行う
    target_metadata = SQLModel.metadata
    print("Target metadata set from SQLModel")

    print("Attempting to import settings...")
    from app.core.config import settings as app_settings

    settings = app_settings  # グローバル変数に代入
    print("Settings imported successfully!")

except ModuleNotFoundError as e:
    print("ERROR: ModuleNotFoundError occurred!")
    print(f"Error details: {e}")
    print("Please double-check:")
    print("1. If all necessary __init__.py files exist (app/, app/models/, etc.).")
    print("2. If the volume mount in docker-compose.yml (.:/app) is correct.")
    print("3. If sys.path shown above includes the correct project root ('/app').")
    traceback.print_exc()  # 詳細なトレースバックを出力
    sys.exit(1)  # エラーで終了
except Exception as e:
    print("ERROR: An unexpected error occurred during imports!")
    print(f"Error details: {e}")
    traceback.print_exc()
    sys.exit(1)

# --- ↑↑↑ デバッグ・インポート部分 ↑↑↑ ---

# --- Alembic ConfigオブジェクトとDB URL設定 (インポート成功後に実行) ---
config = context.config
if settings and settings.DATABASE_URL:
    config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    print(
        f"Database URL set in Alembic config: {settings.DATABASE_URL[:20]}..."
    )  # URLの一部だけ表示
else:
    print("ERROR: Settings or DATABASE_URL not available after imports!")
    sys.exit(1)

# --- ロギング設定 ---
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- メタデータ設定 (再度確認) ---
if target_metadata is None:
    print("ERROR: target_metadata is still None!")
    # Fallback or raise error - this shouldn't happen if imports worked
    # For safety, maybe assign directly again if using a Base class later
    # target_metadata = MyBase.metadata
    sys.exit(1)
print("Confirmed target_metadata is set.")


# --- run_migrations_offline 関数 (変更なし) ---
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


# --- run_migrations_online 関数 (変更なし) ---
def do_run_migrations(connection):
    """Helper function called by run_migrations_online."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode asynchronously."""
    connectable = create_async_engine(
        config.get_main_option("sqlalchemy.url"),
        future=True,
        # echo=True,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


# --- メイン実行部分 (変更なし) ---
if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())

print("--- Alembic env.py finished ---")  # 終了ログ
