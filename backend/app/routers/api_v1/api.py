from fastapi import APIRouter

from .endpoints import families, labels, tasks

# API v1 のためのメインルーター
api_router = APIRouter()

api_router.include_router(families.router, prefix="/families", tags=["Families"])
api_router.include_router(
    labels.router, prefix="/families/{family_id}/labels", tags=["Labels"]
)
api_router.include_router(
    tasks.router,
    prefix="/families/{family_id}/tasks",
    tags=["Tasks"],
)

# --- 今後、他のリソースのルーターもここに追加していく ---
# from .endpoints import users
# api_router.include_router(users.router, prefix="/users", tags=["Users"])
# from .endpoints import tasks
# api_router.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])
