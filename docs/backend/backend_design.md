# Backend Design Documentation (FamilyHubApp)

## ディレクトリ構成

このバックエンドアプリケーションは、関心事の分離を目的として以下のディレクトリ構成を採用しています。

```
├── app/                   # メインのアプリケーションコード
│   ├── init.py
│   ├── main.py          # FastAPI App Entrypoint
│   ├── core/            # コア設定・共通関数 (例: config.py)
│   ├── db/              # DB接続・セッション管理 (例: session.py)
│   ├── models/          # DBモデル定義 (SQLModel) (例: family.py, user.py, task.py)
│   ├── schemas/         # APIスキーマ定義 (Pydantic/SQLModel) (例: family.py, user.py, task.py)
│   ├── crud/            # CRUD操作関数 (例: crud_family.py, crud_user.py, crud_task.py)
│   └── routers/         # APIエンドポイント(ルーティング)定義
│       └── api_v1/      # APIバージョン管理 (例: v1)
│           └── endpoints/ # 各リソースのエンドポイント (例: families.py, users.py, tasks.py)
├── tests/                 # ★ テストコード用ディレクトリ ★
│   ├── init.py
│   ├── conftest.py        # pytestの共通設定・フィクスチャ
│   ├── crud/            # CRUD関数のテスト
│   │   └── test_crud_task.py
│   └── routers/         # APIエンドポイントのテスト
│       └── test_tasks.py
├── .env                 # 環境変数 (Git管理外)
├── .env.example         # 環境変数サンプル
├── .gitignore           # Git無視リスト
├── Dockerfile           # FastAPIアプリ用Dockerfile
├── docker-compose.yml   # Docker Compose設定
├── pyproject.toml       # プロジェクト設定 (Ruffなど)
└── requirements.txt     # Python依存ライブラリ
```

### 各ディレクトリの役割

- **`app/`**: アプリケーションの主要なソースコードが含まれます。
  - **`core/`**: 設定ファイルや共通のユーティリティ関数など。
  - **`db/`**: データベースセッションの管理など、データベース接続に関連するコード。
  - **`models/`**: データベースのテーブル構造に対応する SQLModel クラス。
  - **`schemas/`**: API リクエスト/レスポンスのデータ形式を定義する Pydantic/SQLModel クラス。
  - **`crud/`**: データベースに対する基本的な作成(Create)、読み取り(Read)、更新(Update)、削除(Delete)操作を行う関数群。ビジネスロジックは最小限に。
  - **`routers/`**: API のエンドポイントを定義し、リクエストを受け付け、適切な CRUD 関数やビジネスロジックを呼び出す部分。
- **`tests/`**: 自動テストのコードが含まれます。（後述）
- **(ルートディレクトリ)**: Docker 設定ファイル、依存関係ファイル、プロジェクト設定ファイルなど。
