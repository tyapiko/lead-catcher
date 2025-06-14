import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import DictCursor
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import date
import decimal

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
def get_corporations(
    prefecture: Optional[str] = Query(None, description="都道府県名でフィルタリング（例: 東京都）"),
    start_date: Optional[date] = Query(None, description="設立日の開始日でフィルタリング（YYYY-MM-DD）"),
    end_date: Optional[date] = Query(None, description="設立日の終了日でフィルタリング（YYYY-MM-DD）")
):
    """
    データベースに登録されている法人情報の一覧を取得します。
    都道府県や設立日でフィルタリングできます。
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # ベースとなるSQLクエリ
            base_query = """
                SELECT 
                    corporate_number, name, location, establishment_date, 
                    business_category, latitude, longitude 
                FROM corporations
            """
            
            # WHERE句の条件とパラメータを動的に構築
            where_clauses = []
            params = {}
            
            # ddl.sqlにはprefectureカラムがないため、locationでフィルタリング
            if prefecture:
                where_clauses.append("location LIKE %(prefecture)s")
                params['prefecture'] = f"%{prefecture}%" # 部分一致で検索
            
            if start_date:
                where_clauses.append("establishment_date >= %(start_date)s")
                params['start_date'] = start_date
            
            if end_date:
                where_clauses.append("establishment_date <= %(end_date)s")
                params['end_date'] = end_date
            
            # WHERE句を結合
            query = base_query
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
            
            # ORDER BY と LIMIT を追加
            query += " ORDER BY establishment_date DESC NULLS LAST LIMIT 100;"
            
            cur.execute(query, params)
            db_results = cur.fetchall()
            
            corporations_list = []
            for row in db_results:
                row_dict = dict(row)
                if isinstance(row_dict.get('latitude'), decimal.Decimal):
                    row_dict['latitude'] = float(row_dict['latitude'])
                if isinstance(row_dict.get('longitude'), decimal.Decimal):
                    row_dict['longitude'] = float(row_dict['longitude'])
                corporations_list.append(row_dict)
            
            return corporations_list
            
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"データベースクエリエラー: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"サーバー内部エラー: {e}")
    finally:
        if conn:
            conn.close()
