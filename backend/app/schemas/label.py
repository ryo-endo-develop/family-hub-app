import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict
from sqlmodel import Field
from sqlmodel import SQLModel as SQLModelBase

# --- Label Schemas ---


# Label作成・更新で共通する基本フィールド
class LabelBase(SQLModelBase):
    name: str = Field(max_length=50, description="ラベル名")
    color: Optional[str] = Field(
        default=None, max_length=7, description="カラーコード (例: #FFB3BA)"
    )


# Label作成API (POST /labels) のリクエストボディ用スキーマ
class LabelCreate(LabelBase):
    pass  # 今はBaseと同じ


# Label更新API (PUT /labels/{id}) のリクエストボディ用スキーマ (全項目任意)
class LabelUpdate(SQLModelBase):
    name: Optional[str] = Field(default=None, max_length=50)
    color: Optional[str] = Field(default=None, max_length=7)


# Label読み取りAPI (GET /labels, GET /labels/{id}) のレスポンス用スキーマ
# DBモデルを継承して、DBの全フィールドを含む形にする (必要なら後で調整)
# creatorやupdaterの情報はここでは含めず、必要なら別スキーマを作る


# ラベル要約情報スキーマ (APIレスポンスのネスト用)
class LabelSummary(BaseModel):
    id: int
    name: str
    color: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)  # ★ ORMからの変換を許可


class LabelRead(BaseModel):
    id: int
    # family_id はAPIレスポンスに含めないケースが多いので除外 (必要なら追加)
    name: str
    color: Optional[str] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True)  # ★ ORMからの変換を許可
