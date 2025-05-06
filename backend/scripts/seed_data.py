import argparse  # コマンドライン引数処理用
import asyncio
import datetime  # 日付データ用
import logging
import os
import sys

# --- Path設定 (alembic/env.py や tests/conftest.py と同様) ---
# このスクリプト(seed_data.py)自身の絶対パスを取得
script_path = os.path.abspath(__file__)
# このスクリプトが存在するディレクトリ(scripts/)のパスを取得
scripts_dir = os.path.dirname(script_path)
# プロジェクトルートディレクトリのパスを取得 (scripts/ の親ディレクトリ)
project_root = os.path.dirname(scripts_dir)

# デバッグ用にパスを表示
print(f"DEBUG [Seed Script]: project_root = {project_root}")
print(f"DEBUG [Seed Script]: Initial sys.path = {sys.path}")

# プロジェクトルートがPythonのインポートパスに含まれていなければ追加
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"DEBUG [Seed Script]: Added {project_root} to sys.path")
print(f"DEBUG [Seed Script]: Modified sys.path = {sys.path}")
# --- ここまで Path設定 --

# --- 必要なものをインポート ---
from app.db.session import AsyncSessionFactory

# DB接続用のエンジンとセッションファクトリをインポート
# (conftest.pyとは別に、このスクリプト用に直接作成しても良い)
from app.db.session import engine as async_engine

# 必要なモデルとEnumをインポート
from app.models.family import Family
from app.models.family_membership import FamilyMembership, MembershipRole
from app.models.label import Label
from app.models.task import Task, TaskType
from app.models.task_label import TaskLabel
from app.models.user import User

# RoutineSettings スキーマもインポート (JSONデータ作成用)
from app.schemas.task import RoutineSettings
from sqlalchemy.ext.asyncio import AsyncEngine  # Engineの型ヒント用
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def reset_database(engine: AsyncEngine):
    """全てのテーブルを削除し、再作成する"""
    logger.info("Resetting database...")
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)
    logger.info("Database has been reset.")


async def seed_initial_data(session: AsyncSession):
    """初期データを投入する"""
    logger.info("Seeding initial data...")

    # --- データ作成 ---
    try:
        # 1. ユーザー作成 (テストで使うかもしれないユーザー)
        user1 = User(
            oidc_subject="seed|user1",
            email="seed.user1@example.com",
            name="Seed User 1",
        )
        user2 = User(
            oidc_subject="seed|user2",
            email="seed.user2@example.com",
            name="Seed User 2",
        )
        session.add_all([user1, user2])
        await session.flush()  # IDを確定

        # 2. 家族作成
        family1 = Family(family_name="テスト家族 Seed")
        session.add(family1)
        await session.flush()

        # 3. メンバーシップ作成 (User1をAdmin, User2をMemberとして家族1に追加)
        mem1 = FamilyMembership(
            user_id=user1.id, family_id=family1.id, role=MembershipRole.ADMIN
        )
        mem2 = FamilyMembership(
            user_id=user2.id, family_id=family1.id, role=MembershipRole.MEMBER
        )
        session.add_all([mem1, mem2])

        # 4. ラベル作成 (家族1用)
        label_kaji = Label(
            family_id=family1.id, name="家事", color="#FFDDC1", created_by_id=user1.id
        )
        label_kaimono = Label(
            family_id=family1.id, name="買い物", color="#A0E7E5", created_by_id=user1.id
        )
        label_shigoto = Label(
            family_id=family1.id, name="仕事", color="#D4A5A5", created_by_id=user1.id
        )
        session.add_all([label_kaji, label_kaimono, label_shigoto])
        await session.flush()

        # 5. タスク作成 (家族1用)
        # タスク1: 定常タスク、担当者あり、ラベル複数
        routine_data = RoutineSettings(
            repeat_every="weekly", weekdays=[0, 3]
        )  # 月曜、木曜
        task1 = Task(
            family_id=family1.id,
            title="週次のゴミ出し準備",
            notes="資源ごみと燃えるゴミをまとめる",
            task_type=TaskType.ROUTINE,
            routine_settings=routine_data.model_dump(),  # スキーマから辞書へ
            assignee_id=user2.id,  # User2に割り当て
            created_by_id=user1.id,
            updated_by_id=user1.id,
            priority=1,
        )
        session.add(task1)
        await session.flush()
        # タスク1にラベルを紐付け
        link1_1 = TaskLabel(task_id=task1.id, label_id=label_kaji.id)
        link1_2 = TaskLabel(
            task_id=task1.id, label_id=label_kaimono.id
        )  # ゴミ出し準備も買い物の一部？
        session.add_all([link1_1, link1_2])

        # タスク2: 単発タスク、担当者なし、ラベルあり、サブタスク
        task2 = Task(
            family_id=family1.id,
            title="牛乳を買う",
            task_type=TaskType.SINGLE,
            is_done=False,
            due_date=datetime.date.today() + datetime.timedelta(days=2),
            created_by_id=user1.id,
            updated_by_id=user1.id,
            parent_task_id=task1.id,  # task1のサブタスクに
        )
        session.add(task2)
        await session.flush()
        # タスク2にラベルを紐付け
        link2_1 = TaskLabel(task_id=task2.id, label_id=label_kaimono.id)
        session.add(link2_1)

        # タスク3: 完了済みタスク
        task3 = Task(
            family_id=family1.id,
            title="銀行振込",
            task_type=TaskType.SINGLE,
            is_done=True,
            created_by_id=user1.id,
            updated_by_id=user1.id,
        )
        session.add(task3)

        # 全ての変更をコミット
        await session.commit()
        logger.info("Initial data seeded successfully.")

    except Exception:
        logger.error("Error seeding data, rolling back.", exc_info=True)
        await session.rollback()
        raise


async def main(reset: bool = False):
    """メイン処理: リセット（オプション）とシード実行"""
    logger.info("Starting data seeding script...")
    # このスクリプト用にエンジンとセッションファクトリを取得
    # app.db.session からインポートしたものをそのまま使う
    global async_engine, AsyncSessionFactory

    if reset:
        await reset_database(async_engine)

    logger.info("Proceeding to seed data...")
    async with AsyncSessionFactory() as session:
        await seed_initial_data(session)

    await async_engine.dispose()  # スクリプト終了時にエンジンを破棄
    logger.info("Data seeding script finished.")


if __name__ == "__main__":
    # コマンドライン引数を解析
    parser = argparse.ArgumentParser(description="Seed the database with initial data.")
    parser.add_argument(
        "--reset",
        action="store_true",  # --reset が指定されたら True になる
        help="Reset the database (drop and create all tables) before seeding.",
    )
    args = parser.parse_args()

    # main コルーチンを実行
    asyncio.run(main(reset=args.reset))
