from fastapi import APIRouter

from .endpoints import families, labels

# API v1 のためのメインルーター
api_router = APIRouter()

# families ルーターを /families というプレフィックスで登録
api_router.include_router(families.router, prefix="/families", tags=["Families"])
api_router.include_router(
    labels.router, prefix="/families/{family_id}/labels", tags=["Labels"]
)
# --- 今後、他のリソースのルーターもここに追加していく ---
# from .endpoints import users
# api_router.include_router(users.router, prefix="/users", tags=["Users"])
# from .endpoints import tasks
# api_router.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
