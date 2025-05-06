from fastapi import FastAPI

from app.routers.api_v1.api import api_router

# FastAPIアプリケーションインスタンスを作成
app = FastAPI(title="FamilyHubApp API", version="0.1.0")
app.include_router(api_router, prefix="/api/v1")


# ルートエンドポイント (動作確認用)
@app.get("/")
async def read_root():
    """
    ルートパスにアクセスした際に簡単なメッセージを返すエンドポイント。
    APIが正常に起動しているかを確認するために使用します。
    """
    return {"message": "Welcome to FamilyHubApp API! It's running!"}
