import datetime
from typing import Optional

from pydantic import (  # EmailやURL用の型をインポート
    BaseModel,
    ConfigDict,
    EmailStr,
    HttpUrl,
)
from sqlmodel import Field
from sqlmodel import SQLModel as SQLModelBase

# --- User Schemas ---


# ユーザー情報の基本的な部分（読み取りや更新で共通する可能性のあるフィールド）
# OIDCプロバイダーから常に提供されるとは限らないため Optional にしておく
class UserBase(SQLModelBase):
    email: Optional[EmailStr] = Field(
        default=None, index=True
    )  # EmailStrでメール形式をバリデーション
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    # OIDCでは 'picture' という名前の場合があるので validation_alias を使う
    avatar_url: Optional[HttpUrl] = Field(
        default=None,
    )  # HttpUrlでURL形式をバリデーション


# ユーザーが自身のプロフィール情報を更新する際にAPIが受け取るデータのスキーマ (例)
class UserUpdate(UserBase):
    # この例では UserBase と同じだが、更新させたい項目をここに定義する
    pass


# ユーザー要約情報スキーマ (APIレスポンスのネスト用)
class UserSummary(BaseModel):
    id: int
    name: Optional[str] = None  # DBに合わせてOptionalに
    avatar_url: Optional[HttpUrl] = None  # PydanticのHttpUrl型を使用
    model_config = ConfigDict(from_attributes=True)


# APIレスポンスとしてクライアントに返すユーザー情報のスキーマ
# ★機密情報(oidc_subjectなど)は含めないように、含めるフィールドを明示的に定義★
class UserRead(BaseModel):
    id: int
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    avatar_url: Optional[HttpUrl] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True)  # ★ ORMからの変換を許可


# --- (参考) 内部処理用スキーマ ---
# OIDC認証後にユーザーをDBに登録/更新する際に、内部的に使う可能性のあるスキーマ
# oidc_subject を含む
class UserInternalCreate(UserBase):
    oidc_subject: str = Field(index=True, unique=True)
