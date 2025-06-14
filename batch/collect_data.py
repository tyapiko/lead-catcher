import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta
import json
import time
import unicodedata
import re
import psycopg2
from psycopg2.extras import execute_batch

load_dotenv()

# --- API & Geocoder Settings ---
API_TOKEN = os.getenv('GBIZINFO_API_KEY')
GBIZINFO_URL = "https://info.gbiz.go.jp/hojin/v1/hojin/updateInfo"
GEOCODER_URL = "https://msearch.gsi.go.jp/address-search/AddressSearch"

# --- Database Settings ---
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')


def simplify_address_progressive(address: str):
    """
    段階的に住所を簡略化して複数パターンを返す
    """
    normalized = unicodedata.normalize('NFKC', address)
    patterns = []
    patterns.append(normalized)
    pattern1 = re.sub(r'(\d+丁目).*', r'\1', normalized)
    if pattern1 != normalized:
        patterns.append(pattern1)
    pattern2 = re.sub(r'\d+丁目.*', '', normalized)
    if pattern2 != pattern1:
        patterns.append(pattern2)
    last_idx = -1
    for keyword in ['市', '区', '町', '村']:
        idx = normalized.rfind(keyword)
        if idx > last_idx:
            last_idx = idx
    if last_idx != -1:
        pattern3 = normalized[:last_idx + 1]
        if pattern3 not in patterns:
            patterns.append(pattern3)
    return list(dict.fromkeys(patterns))

def geocode_address_improved(address: str):
    """
    改善されたジオコーディング関数
    """
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    address_patterns = simplify_address_progressive(address)
    for i, addr_pattern in enumerate(address_patterns):
        print(f"    試行 {i+1}: {addr_pattern}")
        params = {'q': addr_pattern}
        try:
            response = requests.get(GEOCODER_URL, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                first_result = data[0]
                if 'geometry' in first_result and 'coordinates' in first_result['geometry']:
                    coords = first_result['geometry']['coordinates']
                    if len(coords) >= 2:
                        coordinates = (coords[1], coords[0]) # (緯度, 経度)
                        print(f"    => 成功: 緯度 {coordinates[0]}, 経度 {coordinates[1]}")
                        return coordinates
        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            print(f"    => エラー: {e}")
        time.sleep(0.5)
    print(f"    => 失敗: すべてのパターンで見つかりませんでした。")
    return None, None

def fetch_new_corporations():
    if not API_TOKEN:
        print("エラー: gBizINFOのAPIキーが設定されていません。")
        return None
    headers = {"X-hojinInfo-api-token": API_TOKEN, "Accept": "application/json"}
    yesterday = datetime.now() - timedelta(days=1)
    date_str = yesterday.strftime('%Y%m%d')
    params = {"from": date_str, "to": date_str, "page": 1}
    print(f"gBizINFO APIから {date_str} の法人データを取得します...")
    try:
        response = requests.get(GBIZINFO_URL, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"APIリクエスト中にエラーが発生しました: {e}")
        return None

def save_corporations_to_db(corporations_data):
    """
    法人データをPostgreSQLデータベースに保存する。
    """
    if not corporations_data:
        print("データベースに保存するデータがありません。")
        return
    
    conn = None
    try:
        print("\nデータベースに接続しています...")
        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
        )
        print("データベース接続成功。")

        with conn.cursor() as cur:
            # ▼▼▼ 修正 ▼▼▼ ddl.sqlに合わせて`location`カラムを追加
            insert_query = """
                INSERT INTO corporations (
                    corporate_number, name, location, prefecture, city, street_address,
                    establishment_date, business_category, latitude, longitude
                ) VALUES (
                    %(corporate_number)s, %(name)s, %(location)s, %(prefecture)s, %(city)s, %(street_address)s,
                    %(establishment_date)s, %(business_category)s, %(latitude)s, %(longitude)s
                ) ON CONFLICT (corporate_number) DO UPDATE SET
                    name = EXCLUDED.name,
                    location = EXCLUDED.location,
                    prefecture = EXCLUDED.prefecture,
                    city = EXCLUDED.city,
                    street_address = EXCLUDED.street_address,
                    establishment_date = EXCLUDED.establishment_date,
                    business_category = EXCLUDED.business_category,
                    latitude = EXCLUDED.latitude,
                    longitude = EXCLUDED.longitude,
                    updated_at = CURRENT_TIMESTAMP;
            """
            
            execute_batch(cur, insert_query, corporations_data)

        conn.commit()
        print(f"✅ {len(corporations_data)}件のデータを処理し、データベースへの保存・更新を試みました。")

    except psycopg2.Error as e:
        print(f"データベースエラー: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
            print("データベース接続をクローズしました。")


if __name__ == '__main__':
    result = fetch_new_corporations()
    corporations = result.get('hojin-infos', []) if result else []

    if not corporations:
        print("🎉 データ取得成功。対象期間の法人は0件でした。")
    else:
        print(f"🎉 {len(corporations)} 件の法人情報を取得しました。ジオコーディングとデータ加工を開始します...")

        processed_corps = []
        success_count = 0
        for i, corp in enumerate(corporations):
            print(f"\n--- 法人 {i+1}/{len(corporations)}: {corp.get('name', '名称不明')} ---")
            
            # ▼▼▼ 修正 ▼▼▼ locationはそのまま取得できるので、先に変数に入れておく
            original_address = corp.get('location')

            lat, lon = None, None
            if original_address:
                print(f"  > 元の住所: {original_address}")
                lat, lon = geocode_address_improved(original_address)
                if lat and lon:
                    success_count += 1
                time.sleep(1)
            else:
                print("  > 住所情報なし")
            
            # ▼▼▼ 修正 ▼▼▼ DB保存用データに`location`キーを追加
            processed_data = {
                'corporate_number': corp.get('corporate_number'),
                'name': corp.get('name'),
                'location': original_address, # APIから取得した完全な住所を保存
                'prefecture': corp.get('prefecture_name'),
                'city': corp.get('city_name'),
                'street_address': corp.get('street_number'),
                'establishment_date': corp.get('establishment_date'),
                'business_category': corp.get('business_summary'),
                'latitude': lat,
                'longitude': lon,
            }
            if processed_data['corporate_number']:
                processed_corps.append(processed_data)

        print("\n--- ジオコーディング後の最初の1件のデータサンプル ---")
        if processed_corps:
            print(json.dumps(processed_corps[0], indent=2, ensure_ascii=False))
        print("-------------------------------------------------")
        print(f"ジオコーディング成功率: {success_count}/{len(corporations)}")

        save_corporations_to_db(processed_corps)

    print("\n✅ Step 1: データ収集・処理バッチ開発 は、これにて完了とします。")
