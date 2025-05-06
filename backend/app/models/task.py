import datetime
import enum
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import JSON, TEXT, Column, Field, Relationship, SQLModel
from sqlmodel import Enum as SQLModelEnum

from .task_label import TaskLabel

# --- Type Hinting ---
if TYPE_CHECKING:
    from .family import Family
    from .label import Label
    from .user import User


# --- Enums ---
class TaskType(str, enum.Enum):
    SINGLE = "single"
    ROUTINE = "routine"


class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    family_id: int = Field(foreign_key="family.id", index=True, nullable=False)
    title: str = Field(max_length=255, nullable=False)
    is_done: bool = Field(default=False, nullable=False)
    # Enum型: SQLAlchemy/SQLModelのEnumを使う
    task_type: TaskType = Field(
        sa_column=Column(SQLModelEnum(TaskType), nullable=False)
    )
    due_date: Optional[datetime.date] = Field(default=None)
    next_occurrence_date: Optional[datetime.date] = Field(
        default=None, index=True
    )  # 検索用にインデックス追加
    # JSON型: SQLAlchemyのJSONを使う
    routine_settings: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    assignee_id: Optional[int] = Field(
        default=None, foreign_key="user.id", nullable=True, index=True
    )  # 検索用にインデックス追加
    # TEXT型: SQLAlchemyのTEXTを使う
    notes: Optional[str] = Field(default=None, sa_column=Column(TEXT))
    priority: Optional[int] = Field(default=None)  # 例: 1:高, 2:中, 3:低
    # 自己参照のための外部キー
    parent_task_id: Optional[int] = Field(
        default=None, foreign_key="task.id", nullable=True
    )
    created_by_id: Optional[int] = Field(
        default=None, foreign_key="user.id", nullable=True
    )
    updated_by_id: Optional[int] = Field(
        default=None, foreign_key="user.id", nullable=True
    )
    created_at: datetime.datetime = Field(
        default_factory=datetime.datetime.now, nullable=False
    )
    updated_at: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        nullable=False,
        sa_column_kwargs={"onupdate": datetime.datetime.now},
    )

    # --- Relationships ---
    family: "Family" = Relationship(back_populates="tasks")
    assignee: Optional["User"] = Relationship(
        back_populates="assigned_tasks",
        sa_relationship_kwargs={"foreign_keys": "Task.assignee_id"},
    )
    creator: Optional["User"] = Relationship(
        back_populates="created_tasks",
        sa_relationship_kwargs={"foreign_keys": "Task.created_by_id"},
    )
    updater: Optional["User"] = Relationship(
        back_populates="updated_tasks",
        sa_relationship_kwargs={"foreign_keys": "Task.updated_by_id"},
    )
    # 自己参照: remote_sideは文字列、foreign_keysはクラス属性リスト
    parent_task: Optional["Task"] = Relationship(
        back_populates="subtasks",
        sa_relationship_kwargs={
            "remote_side": "Task.id",
            "foreign_keys": "Task.parent_task_id",
        },
    )
    # 自己参照リレーションシップ (サブタスクリスト)
    subtasks: List["Task"] = Relationship(back_populates="parent_task")
    # Many-to-Many リレーションシップ (ラベル)
    labels: List["Label"] = Relationship(back_populates="tasks", link_model=TaskLabel)

    # __tablename__ = "tasks" # SQLModelが自動推測
