import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import DictCursor
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import date
import decimal # Decimal型を扱うためにインポート

# --- 準備 ---
dotenv_path = os.path.join(os.path.dirname(__file__), '../batch/.env')
load_dotenv(dotenv_path=dotenv_path)

DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')

app = FastAPI(
    title="Lead Catcher API",
    description="新規設立法人の情報を取得するためのAPIです。",
    version="1.0.0",
)

# --- CORS設定 ---
origins = [
    "http://localhost",
    "http://localhost:8501",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydanticモデル定義 ---
class Corporation(BaseModel):
    corporate_number: str
    name: str
    location: Optional[str] = None
    establishment_date: Optional[date] = None
    business_category: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # Pydantic V2との互換性のための修正
    model_config = ConfigDict(from_attributes=True)


# --- ヘルパー関数 ---
def get_db_connection():
    """データベースへの接続を取得する関数"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            cursor_factory=DictCursor
        )
        return conn
    except psycopg2.OperationalError as e:
        raise HTTPException(status_code=500, detail=f"データベース接続エラー: {e}")

# --- APIエンドポイント ---
@app.get("/")
def read_root():
    """APIのルート。動作確認用。"""
    return {"message": "Welcome to Lead Catcher API!"}

@app.get("/corporations", response_model=List[Corporation])
def get_corporations():
    """
    データベースに登録されている法人情報の一覧を取得します。
    最新の設立日から100件を返します。
    """
    conn = None # finallyブロックで参照できるよう、外で初期化
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    corporate_number, name, location, establishment_date, 
                    business_category, latitude, longitude 
                FROM corporations 
                ORDER BY establishment_date DESC NULLS LAST 
                LIMIT 100;
                """
            )
            db_results = cur.fetchall()
            
            # ▼▼▼ 重要な修正 ▼▼▼
            # DBからの結果をPydanticモデルに安全に変換する
            corporations_list = []
            for row in db_results:
                row_dict = dict(row)
                # Decimal型をfloatに明示的に変換
                if isinstance(row_dict.get('latitude'), decimal.Decimal):
                    row_dict['latitude'] = float(row_dict['latitude'])
                if isinstance(row_dict.get('longitude'), decimal.Decimal):
                    row_dict['longitude'] = float(row_dict['longitude'])
                corporations_list.append(row_dict)
            
            return corporations_list
            
    except psycopg2.Error as e:
        # DB操作に関するエラー
        raise HTTPException(status_code=500, detail=f"データベースクエリエラー: {e}")
    except Exception as e:
        # データ変換など、その他の予期せぬエラー
        raise HTTPException(status_code=500, detail=f"サーバー内部エラー: {e}")
    finally:
        if conn:
            conn.close()
