import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, SQLModel

# --- Type Hintingのための循環参照回避 ---
# これらのモデルはまだ存在しませんが、リレーションシップで型ヒントを使うために必要です。
if TYPE_CHECKING:
    from .family_membership import FamilyMembership
    from .label import Label
    from .task import Task
# --- ここまで ---


class Family(SQLModel, table=True):
    # テーブルのカラムに対応するフィールドを定義
    id: Optional[int] = Field(default=None, primary_key=True)
    family_name: str = Field(
        index=True, max_length=100, nullable=False
    )  # 検索しそうなのでindex=True
    created_at: datetime.datetime = Field(
        default_factory=datetime.datetime.now, nullable=False
    )
    # onupdateはSQLAlchemyの機能を使うためsa_column_kwargsで指定
    updated_at: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        nullable=False,
        sa_column_kwargs={"onupdate": datetime.datetime.now},
    )

    # --- リレーションシップ定義 (この家族に属する他のモデル) ---
    # "memberships" という名前で FamilyMembership モデルのリストにアクセスできるようにする
    # back_populates で相手側のモデル(FamilyMembership)の関連フィールド名("family")を指定
    memberships: List["FamilyMembership"] = Relationship(back_populates="family")
    labels: List["Label"] = Relationship(back_populates="family")
    tasks: List["Task"] = Relationship(back_populates="family")

    # SQLModelにテーブル名を自動で推測させる (クラス名を小文字複数形に: family -> families)
    # もし明示的に指定したい場合は以下のように記述
    # __tablename__ = "families"
