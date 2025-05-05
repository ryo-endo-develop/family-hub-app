# --- 循環参照回避のため、TYPE_CHECKINGを使う ---
import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel as SQLModelBase
from pydantic import ConfigDict
from sqlmodel import Field  # Relationshipも追加 (リレーション用)

if TYPE_CHECKING:
    # Readスキーマでリレーション先の情報を含める場合に必要
    # from .user import UserRead # Userスキーマはまだないのでコメントアウト
    # from .task import TaskRead # Taskスキーマはまだないのでコメントアウト
    # from .label import LabelRead # Labelスキーマはまだないのでコメントアウト
    pass  # 現時点ではリレーションは含めない

# --- Family スキーマ定義 ---


# 共通のフィールドを持つベーススキーマ (主に作成・更新で利用)
class FamilyBase(SQLModelBase):
    family_name: str = Field(
        min_length=1, max_length=100, index=True
    )  # 簡単なバリデーション追加


# APIリクエストボディとして受け取る作成用スキーマ
class FamilyCreate(FamilyBase):
    pass  # 今はBaseと同じ


# APIリクエストボディとして受け取る更新用スキーマ (例)
# class FamilyUpdate(SQLModel):
#     family_name: Optional[str] = Field(default=None, min_length=1, max_length=100, index=True) # 更新は任意項目

# APIレスポンスとして返す読み取り用スキーマ
# ★ SQLModelの利点: DBモデルを継承してスキーマを簡単に作成できる ★


class FamilyRead(SQLModelBase):
    id: int
    family_name: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True)


# --- (オプション) リレーションを含む読み取り用スキーマ ---
# class FamilyReadWithMembers(FamilyRead):
#     memberships: List["FamilyMembershipRead"] # FamilyMembershipReadスキーマが必要

# class FamilyReadWithDetails(FamilyRead):
#     memberships: List["FamilyMembershipRead"]
#     tasks: List["TaskRead"]
#     labels: List["LabelRead"]
