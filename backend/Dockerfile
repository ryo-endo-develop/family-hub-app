# 1. ベースイメージを選択
FROM python:3.11-slim

# 2. 環境変数を設定
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

# 3. 作業ディレクトリを設定
WORKDIR /app

# 4. 依存関係をインストール (キャッシュを活用)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 5. アプリケーションコードをコピー
COPY ./app /app/app

# 6. アプリケーションが使用するポートを公開
EXPOSE 8000

# 7. アプリケーション起動コマンド (開発用にホットリロード有効)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]