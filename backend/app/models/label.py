import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, SQLModel

from .task_label import TaskLabel

# --- Type Hinting ---
if TYPE_CHECKING:
    from .family import Family
    from .task import Task  # M2M用にTaskも参照
    from .user import User


class Label(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    family_id: int = Field(foreign_key="family.id", index=True, nullable=False)
    name: str = Field(max_length=50, nullable=False)
    color: Optional[str] = Field(default=None, max_length=7)  # 例: '#FFB3BA'
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
    # このラベルが属するFamily (Many-to-One)
    family: "Family" = Relationship(back_populates="labels")
    # このラベルを作成したUser (Many-to-One)
    creator: Optional["User"] = Relationship(back_populates="created_labels")
    # このラベルを最後に更新したUser (Many-to-One)
    updater: Optional["User"] = Relationship(back_populates="updated_labels")
    # このラベルが付けられたTaskのリスト (Many-to-Many)
    tasks: List["Task"] = Relationship(back_populates="labels", link_model=TaskLabel)

    # __tablename__ = "labels" # SQLModelが自動推測
    # __table_args__ = (UniqueConstraint("family_id", "name", name="uq_family_label_name"),) # 一意制約 (Alembicが自動生成するはず)
