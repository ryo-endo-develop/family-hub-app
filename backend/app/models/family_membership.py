import datetime
import enum  # Python標準のenum
from typing import TYPE_CHECKING, Optional

from sqlmodel import Column, Field, Relationship, SQLModel  # Enumを使うためにインポート
from sqlmodel import Enum as SQLModelEnum

# --- Type Hintingのための循環参照回避 ---
if TYPE_CHECKING:
    from .family import Family
    from .user import User
# --- ここまで ---


# 役割を定義するEnum (Python標準enumを使用)
class MembershipRole(str, enum.Enum):
    ADMIN = "admin"
    MEMBER = "member"


class FamilyMembership(SQLModel, table=True):
    # 中間テーブルにも代理キー(id)を持たせる (無くても複合主キーで定義可能)
    id: Optional[int] = Field(default=None, primary_key=True)

    # 外部キー
    user_id: int = Field(foreign_key="user.id", index=True, nullable=False)
    family_id: int = Field(foreign_key="family.id", index=True, nullable=False)

    # 役割 (Enumを使用)
    # SQLAlchemyのEnum型を使うためにsa_columnを使用
    role: MembershipRole = Field(
        sa_column=Column(SQLModelEnum(MembershipRole), nullable=False),
        default=MembershipRole.MEMBER,
    )
    joined_at: datetime.datetime = Field(
        default_factory=datetime.datetime.now, nullable=False
    )

    # --- リレーションシップ定義 (多対一の関係) ---
    # この所属情報がどのユーザー、どの家族に紐づくか
    user: "User" = Relationship(back_populates="memberships")
    family: "Family" = Relationship(back_populates="memberships")

    # もしidを使わずuser_idとfamily_idを複合主キーにする場合
    # __table_args__ = (PrimaryKeyConstraint("user_id", "family_id"),)
    # __tablename__ = "family_memberships" # SQLModelが自動推測
