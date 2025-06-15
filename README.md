# Lead Catcher - 新規法人情報 営業支援ツール

![アプリのスクリーンショット](https://placehold.co/800x400/DDE6ED/526D82?text=App+Screenshot)

**Lead Catcher**は、国のデータベース「[gBizINFO](https://info.gbiz.go.jp/)」から新規設立法人の情報を毎日自動で取得し、営業担当者が効率的に新規リード（見込み顧客）を発見・管理できるWebアプリケーションです。

---

## ✨ 主な機能

* **データ自動収集**: 毎日AM2:00 (JST)に、前日分の新規設立法人情報をgBizINFOから自動で取得し、データベースに蓄積します。
* **法人リスト表示**: 収集した法人情報を一覧（テーブル形式）で表示します。
* **地図マッピング機能**: 絞り込んだ法人の所在地を地図上にピンで可視化します。
* **インタラクティブな絞り込み**: 「都道府県（部分一致）」や「設立日の期間」で、表示する法人情報をリアルタイムに絞り込めます。
* **Dockerによる環境構築**: Docker Composeを利用しているため、誰の環境でも`docker compose up`コマンド一つでアプリケーション全体を簡単に起動できます。

---

## 🔧 技術スタック

このプロジェクトは、モダンな技術スタックで構築されています。

* **バックエンド**: Python, FastAPI
* **フロントエンド**: Python, Streamlit
* **データベース**: PostgreSQL + PostGIS (Docker)
* **コンテナ技術**: Docker, Docker Compose
* **バッチ処理の自動化**: GitHub Actions
* **主なPythonライブラリ**: Requests, Psycopg2, Pandas

---

## 🚀 セットアップと使い方

### 必要なもの

* [Docker Desktop](https://www.docker.com/products/docker-desktop/)

### 手順

1.  **リポジトリをクローン**
    ```bash
    git clone [https://github.com/あなたのユーザー名/lead-catcher.git](https://github.com/あなたのユーザー名/lead-catcher.git)
    cd lead-catcher
    ```

2.  **`.env`ファイルの作成**
    `batch`ディレクトリに`batch/.env.example`というサンプルファイルがあります。これをコピーして`batch/.env`を作成し、あなたのgBizINFOのAPIキーを設定してください。
    ```bash
    cp batch/.env.example batch/.env
    ```
    エディタで`batch/.env`を開き、`GBIZINFO_API_KEY`の値を設定します。
    ```dotenv
    # batch/.env
    GBIZINFO_API_KEY="ここにあなたのAPIキーを貼り付け"
    ...
    ```

3.  **アプリケーションの起動**
    プロジェクトのルートディレクトリで、以下のコマンドを実行します。
    ```bash
    docker compose up --build
    ```
    初回起動時は、各サービスのDockerイメージがビルドされるため数分かかります。

4.  **Webアプリケーションにアクセス**
    Webブラウザで `http://localhost:8501` を開きます。

5.  **（初回のみ）データベースにデータを投入**
    アプリケーションは起動しましたが、データベースはまだ空です。
    別のターミナルを開き、以下のコマンドでデータ収集バッチを手動で実行してください。
    ```bash
    docker compose run --rm batch
    ```
    バッチ処理が完了したら、ブラウザの画面を更新すると法人情報が表示されます。

---

## 🏛️ アーキテクチャ

このアプリケーションは、以下の4つの独立したコンテナが連携して動作しています。

```
graph TD
    subgraph "GitHub Actions (毎日AM2:00)"
        GHA[batchコンテナを起動]
    end

    subgraph "User's PC (Docker Compose)"
        subgraph "Services"
            Frontend[Frontend (Streamlit)]
            Backend[Backend (FastAPI)]
            Batch[Batch (Python Script)]
            DB[(Database: PostgreSQL)]
        end

        User([User]) -->|1. アクセス| Frontend
        Frontend -->|2. APIリクエスト| Backend
        Backend -->|3. データ問合せ| DB
        DB -->|4. データ応答| Backend
        Backend -->|5. JSON応答| Frontend
        Frontend -->|6. 画面表示| User

        Batch -->|データ取得| gBizINFO[gBizINFO API]
        Batch -->|データ保存| DB
    end
    
    GHA -->|トリガー| Batch
    linkStyle 8 stroke:#ff7878,stroke-width:2px,stroke-dasharray: 5 5;
```

---

## 📂 ディレクトリ構成

```
.
├── .github/workflows/          # GitHub Actionsのワークフロー定義
│   └── scheduler.yml
├── backend/                    # バックエンド (FastAPI)
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py
├── batch/                      # データ収集バッチ
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env.example
│   └── collect_data.py
├── frontend/                   # フロントエンド (Streamlit)
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app.py
├── docker-compose.yml          # 全体の組立説明書
├── ddl.sql                     # データベースのテーブル設計図
└── README.md                   # このファイル
```

---

## 🌱 今後の改善案

* **全件取得対応**: gBizINFO APIのページネーションに対応し、100件以上のデータも全件取得できるようにする。
* **フィルタリング強化**: 「業種」での絞り込み機能を追加する。
* **トレンド可視化**: 「業種別の設立件数」などをグラフで可視化する機能を追加する。
* **クラウドへのデプロイ**: AWS FargateやGCP Cloud Runなどにデプロイし、インターネット上に公開する。
