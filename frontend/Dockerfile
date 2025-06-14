# 1. ベースイメージの指定
# 公式のPython 3.12イメージをベースにする
FROM python:3.12-slim

# 2. 作業ディレクトリの設定
# コンテナ内の/appディレクトリで作業を行う
WORKDIR /app

# 3. 必要なファイルをコピー
# まずは依存関係ファイルだけをコピーする
COPY requirements.txt .

# 4. 依存関係のインストール
# requirements.txtに書かれたライブラリをインストールする
RUN pip install --no-cache-dir -r requirements.txt

# 5. ソースコードのコピー
# frontendディレクトリの中身をコンテナ内の/appにコピーする
COPY . .

# 6. ポートを公開
# Streamlitが使用する8501ポートを外部に公開する
EXPOSE 8501

# 7. コンテナ起動時に実行するコマンド
# Streamlitサーバーを起動する
# --server.address 0.0.0.0 はコンテナ外部からのアクセスを許可するために必要
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
