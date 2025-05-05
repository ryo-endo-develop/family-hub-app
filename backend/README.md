# FamilyHubApp (Backend)

## 概要

家族間のタスク管理や情報共有を効率化し、日々の生活をサポートすることを目的とした「FamilyHubApp」のバックエンド API です。
このリポジトリは、Python (FastAPI) と PostgreSQL を使用し、Docker コンテナ上で動作します。マルチテナント対応で、OIDC による認証を想定しています。

## 技術スタック

- **言語:** Python 3.11
- **フレームワーク:** FastAPI
- **データベース:** PostgreSQL 15 (Alpine)
- **ORM:** SQLModel
- **Linter/Formatter:** Ruff
- **環境:** Docker, Docker Compose
- **認証(予定):** OIDC (OpenID Connect)

## セットアップとローカル実行

### 前提条件

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) がインストールされ、起動していること。
- Git がインストールされていること。

### 手順

1.  **リポジトリをクローン:**

    ```bash
    git clone <このリポジトリのURL>
    cd FamilyHubApp # またはクローンしたディレクトリ名
    ```

2.  **環境変数ファイル `.env` の作成:**
    プロジェクトルートに `.env.example` というサンプルファイルを用意しています。これをコピーして `.env` ファイルを作成し、中身（特にデータベースのユーザー名、パスワード）を**ご自身の環境に合わせて安全な値に設定**してください。

    _(プロジェクトルートに `.env.example` を作成)_

    ```dotenv
    # .env.example - このファイルをコピーして .env を作成してください
    POSTGRES_USER=hubuser_changeme
    POSTGRES_PASSWORD=hubpassword_changeme
    POSTGRES_DB=familyhubapp_dev_db
    POSTGRES_SERVER=db
    POSTGRES_PORT=5432
    # SECRET_KEY=your_super_secret_key # 必要なら追加
    ```

    _(作成した `.env` の中身を編集)_

    ```dotenv
    # .env - ★ 必ず安全な値に変更し、Gitにはコミットしない ★
    POSTGRES_USER=hubuser # 例: 実際のユーザー名
    POSTGRES_PASSWORD=YourSecureP@ssw0rd! # ★ 例: 実際のパスワードに変更 ★
    POSTGRES_DB=familyhubapp_dev_db # 例: 実際のDB名
    POSTGRES_SERVER=db
    POSTGRES_PORT=5432
    ```

    **注意:** `.env` ファイルは `.gitignore` により Git の管理対象外となっています。絶対にコミットしないでください。

3.  **Docker コンテナのビルドと起動:**
    プロジェクトルートディレクトリで、以下のコマンドを実行します。

    ```bash
    docker compose up --build -d
    ```

    - `--build`: 初回や `Dockerfile`, `requirements.txt` 変更時にイメージを再ビルドします。
    - `-d`: コンテナをバックグラウンドで起動します。ログを確認したい場合は `-d` を付けずに実行してください。

4.  **起動確認:**
    エラーなく起動したら、ウェブブラウザで `http://localhost:8000` にアクセスします。`{"message":"Welcome to FamilyHubApp API! It's running!"}` と表示されればバックエンド API が正常に起動しています。

5.  **停止:**
    バックグラウンドで起動したコンテナを停止するには、プロジェクトルートで以下のコマンドを実行します。
    ```bash
    docker compose down
    ```

## データベースマイグレーション (Alembic)

データベーススキーマの変更履歴管理には [Alembic](https://alembic.sqlalchemy.org/) を使用します。関連するコマンドは、`docker compose run` を使って一時的なコンテナ内で実行し、生成物はローカルで管理します。

1.  **(初回のみ) Alembic 環境の初期化:**
    以下のコマンドを実行すると、**ローカルのプロジェクトルート**に `alembic` ディレクトリと `alembic.ini` ファイルが作成されます。

    ```bash
    docker compose run --rm backend alembic init alembic
    ```

    - `--rm`: コマンド実行後に一時コンテナを自動削除します。
    - **重要:** このコマンド実行後、生成された `alembic.ini` と `alembic/env.py` を、このプロジェクト（FastAPI, SQLModel, PostgreSQL, 非同期）に合わせて**適切に設定する必要があります。**（次のステップで実施します）

2.  **マイグレーションファイルの自動生成:**
    `app/models/` ディレクトリ内のモデル定義を変更した後、以下のコマンドで差分を検出し、マイグレーションスクリプト（例: `alembic/versions/xxxxx_add_tasks_table.py`）を自動生成します。

    ```bash
    docker compose run --rm backend alembic revision --autogenerate -m "変更内容の短い説明"
    ```

    - 例: `-m "Create families and users tables"`
    - 生成されたマイグレーションスクリプトの内容は必ず確認してください。
    - **★★★【重要】モデル追加・変更時の注意 ★★★**
    - **新しいモデルファイル (`app/models/`) を作成したり、既存モデルにリレーションシップを追加するなどの大きな変更を加えた場合は、必ず `alembic/env.py` ファイルの上部にあるモデルインポートセクションに、対応する `import` 文を追加してください。**
    - (例: `from app.models.new_model import NewModel`)
    - **これを忘れると、`--autogenerate` コマンドがモデルの変更を正しく検出できず、期待したマイグレーションスクリプトが生成されません！**

3.  **データベースへのマイグレーション適用:**
    生成・確認したマイグレーションスクリプトをデータベースに適用し、テーブル作成やスキーマ変更を行います。
    ```bash
    docker compose run --rm backend alembic upgrade head
    ```
    - `head` は利用可能な最新リビジョンまで適用するという意味です。

## Lint & Format (Ruff)

コードの品質維持とスタイル統一のため、[Ruff](https://docs.astral.sh/ruff/) を使用しています。

- **コードの問題点をチェック:**
  ```bash
  docker compose exec backend ruff check ./app
  ```
- **コードがフォーマットルールに従っているかチェック:**
  ```bash
  docker compose exec backend ruff format ./app --check
  ```
- **コードを自動フォーマット:**
  ```bash
  docker compose exec backend ruff format ./app
  ```
- **コードの問題点を自動修正 (可能な範囲で):**
  ```bash
  docker compose exec backend ruff check ./app --fix
  ```

### VSCode との連携 (推奨)

1.  VSCode 拡張機能「Ruff (`charliermarsh.ruff`)」をインストールします。
2.  推奨される設定は、プロジェクト内の `.vscode/settings.json` に記述されています。これにより、ファイル保存時に自動でフォーマットと Lint 修正が実行されます。

## (オプション) データベースへの接続

開発中に直接データベースの内容を確認したい場合は、以下の方法があります。

1.  **`psql` コマンドを使用:**
    ```bash
    docker compose exec db psql -U ${POSTGRES_USER} -d ${POSTGRES_DB}
    ```
    (ターミナルから直接 SQL を実行できます。`.env`ファイルの値が使われます。)
2.  **GUI ツールを使用:**
    `compose.yml` の `db` サービスの `ports` 設定（例: `"5433:5432"`）のコメントアウトを解除し、`docker compose up -d` で再起動します。その後、DBeaver, TablePlus, pgAdmin などの GUI ツールから `localhost:5433` (ホスト側ポート) に対して、`.env` ファイルに設定したユーザー名、パスワード、データベース名で接続します。
