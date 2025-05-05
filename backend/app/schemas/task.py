import datetime
from typing import TYPE_CHECKING, List, Literal, Optional

from pydantic import BaseModel, ConfigDict
from sqlmodel import Field
from sqlmodel import SQLModel as SQLModelBase

# Taskモデルで定義したEnumをインポート
from app.models.task import TaskType

from .label import LabelSummary
from .user import UserSummary

# --- Type Hinting ---
# TaskReadスキーマ内でリレーション先のスキーマを使う場合に必要
if TYPE_CHECKING:
    pass
    # TaskRead自身を再帰的に参照する場合 (サブタスクなど) は文字列で指定

# --- Task Schemas ---


class RoutineSettings(BaseModel):
    repeat_every: Literal["daily", "weekly", "monthly", "yearly"]  # 年次も追加
    # 曜日は 0=月曜, 6=日曜 のように定義を明確にすると良い (例)
    weekdays: Optional[List[int]] = Field(
        default=None, description="週次繰り返し用 (例: [0, 6] for Mon, Sun)"
    )
    day_of_month: Optional[int] = Field(
        default=None, description="月次繰り返し用 (1-31)"
    )
    # 必要に応じて interval (間隔) や end_date (終了日) なども追加


# Task作成・更新で共通する基本フィールド
class TaskBase(SQLModelBase):
    title: str = Field(min_length=1, max_length=255, description="タスクのタイトル")
    notes: Optional[str] = Field(default=None, description="タスクの詳細なメモ")
    priority: Optional[int] = Field(
        default=None, description="優先度 (例: 1:高, 2:中, 3:低)"
    )
    due_date: Optional[datetime.date] = Field(default=None, description="期日")
    task_type: TaskType = Field(
        default=TaskType.SINGLE, description="タスク種別 (単発/定常)"
    )
    # JSONフィールドは辞書(Dict)として定義 (Pydanticが処理)
    routine_settings: Optional[RoutineSettings] = Field(default=None)
    is_done: bool = Field(default=False, description="完了フラグ")


# Task作成API (POST /tasks) のリクエストボディ用スキーマ
# family_id や created_by_id はAPI側で自動設定するため、ここには含めない
class TaskCreate(TaskBase):
    assignee_id: Optional[int] = Field(
        default=None, description="担当者のユーザーID (任意)"
    )
    parent_task_id: Optional[int] = Field(
        default=None, description="親タスクのID (サブタスク用, 任意)"
    )
    # タスク作成時に紐付けるラベルのIDリスト (任意)
    label_ids: Optional[List[int]] = Field(default=None)


# Task更新API (PUT /tasks/{id}) のリクエストボディ用スキーマ (全項目任意)
class TaskUpdate(SQLModelBase):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    notes: Optional[str] = None
    priority: Optional[int] = None
    due_date: Optional[datetime.date] = None
    task_type: Optional[TaskType] = None
    routine_settings: Optional[RoutineSettings] = Field(default=None)
    is_done: Optional[bool] = None
    assignee_id: Optional[int] = None  # 担当者の変更
    parent_task_id: Optional[int] = None  # 親タスクの変更
    # 更新時にラベルをまとめて変更する場合 (既存の関連は上書きされる想定など)
    label_ids: Optional[List[int]] = None


# Task読み取りAPI (GET /tasks, GET /tasks/{id}) のレスポンス用スキーマ
class TaskRead(BaseModel):
    id: int
    title: str
    notes: Optional[str] = None  # notesも返すように追加
    is_done: bool
    task_type: TaskType
    due_date: Optional[datetime.date] = None
    priority: Optional[int] = None  # priorityも返すように追加
    # レスポンスでは構造化された方を返す
    routine_settings: Optional[RoutineSettings] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    # --- ネストされた関連情報 ---
    assignee: Optional[UserSummary] = None  # 担当者サマリ
    labels: List[LabelSummary] = []  # ラベルサマリのリスト (デフォルト空)
    label_ids: List[int] = []
    # --- 関連ID (フロントでの操作等に便利な場合がある) ---
    family_id: int
    parent_task_id: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)  # ★ ORMからの変換を許可
    # created_by_id や updated_by_id は必要に応じて追加


# --- (オプション) リレーションを含む読み取り用スキーマの例 ---
# 必要になったら、以下のように関連情報を含むスキーマを別途定義する

# from .user import UserRead # UserReadスキーマが必要
# from .label import LabelRead # LabelReadスキーマが必要

# class TaskReadWithDetails(TaskRead):
#     assignee: Optional[UserRead] = None # 担当者情報をネスト
#     labels: List[LabelRead] = []      # ラベル情報のリストをネスト
#     # subtasks: List["TaskRead"] = [] # サブタスクもネスト（無限ループ注意）
