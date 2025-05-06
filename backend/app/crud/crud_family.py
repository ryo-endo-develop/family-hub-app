from app.models.family import Family
from app.schemas.family import FamilyCreate
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession


async def get_family(db: AsyncSession, family_id: int) -> Family | None:
    """IDを指定して家族情報を取得する"""
    # session.get は主キーでの取得に最適 (SQLModel v0.0.16以降)
    # SQLAlchemy Coreに近く、より推奨される書き方:
    # statement = select(Family).where(Family.id == family_id)
    # result = await db.exec(statement)
    # return result.first()
    # session.getの方がシンプルで効率的
    family = await db.get(Family, family_id)
    return family


async def get_family_by_name(db: AsyncSession, name: str) -> Family | None:
    """家族名を指定して家族情報を取得する (重複チェック用)"""
    statement = select(Family).where(Family.family_name == name)
    result = await db.exec(statement)
    return result.first()


async def create_family(db: AsyncSession, *, family_in: FamilyCreate) -> Family:
    """新しい家族を作成する"""
    # FamilyCreateスキーマからFamilyモデルインスタンスを作成
    # Pydantic V2/SQLModel では .model_dump() を使う
    family_data = family_in.model_dump()
    db_family = Family(**family_data)

    # DBセッションに追加してコミット
    db.add(db_family)
    await db.commit()
    # DBによって自動採番されたIDなどをモデルインスタンスに反映させる
    await db.refresh(db_family)
    return db_family


async def get_families(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> list[Family]:
    """家族のリストを取得する (ページネーション対応の準備)"""
    statement = select(Family).offset(skip).limit(limit)
    result = await db.exec(statement)
    families = result.all()
    return list(families)  # 結果をリストとして返す
