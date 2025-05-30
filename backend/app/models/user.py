import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, SQLModel

# --- Type Hintingのための循環参照回避 ---
if TYPE_CHECKING:
    from .family_membership import FamilyMembership
    from .label import Label
    from .task import Task
# --- ここまで ---


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    oidc_subject: str = Field(max_length=255, unique=True, index=True, nullable=False)
    email: Optional[str] = Field(default=None, max_length=255, unique=True, index=True)
    name: Optional[str] = Field(default=None, max_length=100)
    avatar_url: Optional[str] = Field(default=None, max_length=255)
    created_at: datetime.datetime = Field(
        default_factory=datetime.datetime.now, nullable=False
    )
    updated_at: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        nullable=False,
        sa_column_kwargs={"onupdate": datetime.datetime.now},
    )

    # --- リレーションシップ定義 (このユーザーに関連する他のモデル) ---
    memberships: List["FamilyMembership"] = Relationship(back_populates="user")
    # このユーザーが作成/更新/担当するラベルやタスクへの関連 (逆方向)
    created_labels: List["Label"] = Relationship(
        back_populates="creator",
        # このリレーションは Label テーブルの created_by_id カラムによって成立することを示す
        sa_relationship_kwargs={"foreign_keys": "Label.created_by_id"},
    )
    updated_labels: List["Label"] = Relationship(
        back_populates="updater",
        sa_relationship_kwargs={"foreign_keys": "Label.updated_by_id"},
    )
    assigned_tasks: List["Task"] = Relationship(
        back_populates="assignee",
        sa_relationship_kwargs={"foreign_keys": "Task.assignee_id"},
    )
    created_tasks: List["Task"] = Relationship(
        back_populates="creator",
        sa_relationship_kwargs={"foreign_keys": "Task.created_by_id"},
    )
    updated_tasks: List["Task"] = Relationship(
        back_populates="updater",
        sa_relationship_kwargs={"foreign_keys": "Task.updated_by_id"},
    )

    # __tablename__ = "users" # SQLModelが自動推測
