from typing import Generic, Optional, TypeVar

from pydantic import BaseModel

DataType = TypeVar("DataType")


class APIResponse(BaseModel, Generic[DataType]):
    """APIレスポンスの標準形式 (主に成功時 2xx で使用)"""

    message: Optional[str] = None  # 補足メッセージ (任意)
    data: Optional[DataType] = (
        None  # 実際のレスポンスデータ (型は可変、リストまたはオブジェクト)
    )


# エラー時 (4xx, 5xx) は、FastAPIのデフォルトである {"detail": "エラーメッセージ"} や、
# カスタムの HTTPException を返すことを想定します。
