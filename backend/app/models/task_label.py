from typing import Optional

from sqlmodel import Field, SQLModel

# --- Type Hinting ---
# このモデル自体がリレーションシップの定義に使われるので、
# 他のモデルからの参照はあっても、ここから外部へのRelationshipは必須ではないことが多い
# if TYPE_CHECKING:
#     from .task import Task
#     from .label import Label


# 中間テーブルモデル: カラム定義のみでOKなことが多い
class TaskLabel(SQLModel, table=True):
    task_id: Optional[int] = Field(
        default=None, foreign_key="task.id", primary_key=True
    )
    label_id: Optional[int] = Field(
        default=None, foreign_key="label.id", primary_key=True
    )

    # __tablename__ = "task_labels" # SQLModelが自動推測
