from fastapi import FastAPI

# FastAPIアプリケーションインスタンスを作成
app = FastAPI(title="FamilyHubApp API")


# ルートエンドポイント (動作確認用)
@app.get("/")
async def read_root():
    """
    ルートパスにアクセスした際に簡単なメッセージを返すエンドポイント。
    APIが正常に起動しているかを確認するために使用します。
    """
    return {"message": "Welcome to FamilyHubApp API! It's running!"}
