from typing import Annotated

# Userモデルをインポート (ダミーユーザー作成と型ヒント用)
from app.models.user import User
from fastapi import Depends


# --- 仮の認証用 依存関係 ---
async def get_current_active_user() -> User:
    """
    現在のログインユーザーを取得する仮の依存関係。
    将来的には実際のOIDCトークン検証ロジックに置き換える。
    現時点では、テスト用に固定のダミーユーザーを返すか、
    あるいは未認証エラーを発生させる。
    """
    print("警告: 仮の認証関数 get_current_active_user が使用されています。")
    # ここでは、開発・テストしやすいようにID=1のダミーユーザーを返すことにします
    # 必要に応じて raise HTTPException(status_code=401) に変更してください
    return User(
        id=1,
        oidc_subject="dummy_oidc|123",
        name="ダミーユーザー",
        email="dummy@example.com",
    )


# FastAPIの Depends で使いやすくするために Annotated を使う (任意)
CurrentUser = Annotated[User, Depends(get_current_active_user)]
