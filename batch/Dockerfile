# ベースイメージとしてPythonを指定
FROM python:3.12-slim

# 作業ディレクトリを設定
WORKDIR /app

# 依存関係ファイルをコピーしてインストール
COPY ./batch/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# バッチディレクトリ全体をコピー
COPY ./batch/ ./batch

# 実行コマンド
CMD ["python", "./batch/collect_data.py"]
