import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta
import json
import time
import unicodedata
import re

load_dotenv()

API_TOKEN = os.getenv('GBIZINFO_API_KEY')
GBIZINFO_URL = "https://info.gbiz.go.jp/hojin/v1/hojin/updateInfo"
GEOCODER_URL = "https://msearch.gsi.go.jp/address-search/AddressSearch"  # 正しいエンドポイント

def simplify_address_progressive(address: str):
    """
    段階的に住所を簡略化して複数パターンを返す
    """
    # 正規化
    normalized = unicodedata.normalize('NFKC', address)
    
    # 数字やハイフンなどを除去するパターン
    patterns = []
    
    # 1. 元の住所
    patterns.append(normalized)
    
    # 2. 番地以降を除去（丁目まで残す）
    pattern1 = re.sub(r'(\d+丁目).*', r'\1', normalized)
    if pattern1 != normalized:
        patterns.append(pattern1)
    
    # 3. 町名まで（丁目も除去）
    pattern2 = re.sub(r'\d+丁目.*', '', normalized)
    if pattern2 != pattern1:
        patterns.append(pattern2)
    
    # 4. 最後の市区町村まで
    last_idx = -1
    for keyword in ['市', '区', '町', '村']:
        idx = normalized.rfind(keyword)
        if idx > last_idx:
            last_idx = idx
    
    if last_idx != -1:
        pattern3 = normalized[:last_idx + 1]
        if pattern3 not in patterns:
            patterns.append(pattern3)
    
    return patterns

def geocode_address_improved(address: str):
    """
    改善されたジオコーディング関数
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    # 段階的に住所を簡略化して試行
    address_patterns = simplify_address_progressive(address)
    
    for i, addr_pattern in enumerate(address_patterns):
        print(f"    試行 {i+1}: {addr_pattern}")
        
        # 国土地理院のAPIパラメータ
        params = {
            'q': addr_pattern
        }
        
        try:
            response = requests.get(GEOCODER_URL, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            # レスポンスの内容を確認
            print(f"    レスポンス状態: {response.status_code}")
            data = response.json()
            
            # デバッグ用：レスポンス構造を表示
            if i == 0:  # 最初の試行のみ
                print(f"    レスポンス構造: {json.dumps(data, indent=2, ensure_ascii=False)[:200]}...")
            
            # 国土地理院APIのレスポンスは配列形式
            if isinstance(data, list) and len(data) > 0:
                first_result = data[0]
                if isinstance(first_result, dict):
                    # geometry配列から座標を取得
                    if 'geometry' in first_result and isinstance(first_result['geometry'], dict):
                        if 'coordinates' in first_result['geometry']:
                            coords = first_result['geometry']['coordinates']
                            if len(coords) >= 2:
                                coordinates = (coords[1], coords[0])  # lat, lon
                    # 直接座標が含まれている場合
                    elif 'lat' in first_result and 'lon' in first_result:
                        coordinates = (first_result['lat'], first_result['lon'])
                    elif 'latitude' in first_result and 'longitude' in first_result:
                        coordinates = (first_result['latitude'], first_result['longitude'])
            
            if coordinates:
                print(f"    => 成功: 緯度 {coordinates[0]}, 経度 {coordinates[1]}")
                return coordinates
                
        except requests.exceptions.RequestException as e:
            print(f"    => リクエストエラー: {e}")
        except json.JSONDecodeError as e:
            print(f"    => JSONデコードエラー: {e}")
        except Exception as e:
            print(f"    => その他のエラー: {e}")
        
        # 次の試行前に少し待機
        time.sleep(0.5)
    
    print(f"    => 失敗: すべてのパターンで見つかりませんでした。")
    return None, None

def fetch_new_corporations():
    if not API_TOKEN:
        return None
        
    headers = {
        "X-hojinInfo-api-token": API_TOKEN,
        "User-Agent": "Mozilla/5.0"
    }
    
    yesterday = datetime.now() - timedelta(days=1)
    date_str = yesterday.strftime('%Y%m%d')
    params = {
        "from": date_str,
        "to": date_str,
        "page": 1
    }
    
    print(f"gBizINFO APIから {date_str} の法人データを取得します...")
    
    try:
        response = requests.get(GBIZINFO_URL, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"APIリクエスト中にエラーが発生しました: {e}")
        return None

if __name__ == '__main__':
    result = fetch_new_corporations()
    corporations = result.get('hojin-infos', []) if result else []
    
    if not corporations:
        print("🎉 データ取得成功。対象期間の法人は0件でした。")
    else:
        print(f"🎉 {len(corporations)} 件の法人情報を取得しました。ジオコーディングを開始します...")
        
        success_count = 0
        for i, corp in enumerate(corporations):
            print(f"\n--- 法人 {i+1}/{len(corporations)} ---")
            original_address = corp.get('location')
            
            if original_address:
                print(f"  > 元の住所: {original_address}")
                
                lat, lon = geocode_address_improved(original_address)
                
                corp['latitude'] = lat
                corp['longitude'] = lon
                
                if lat and lon:
                    success_count += 1
                
                # APIに負荷をかけないよう待機
                time.sleep(1)
            else:
                print(f"  > 住所情報なし")
        
        print("\n--- ジオコーディング後の最初の1件のデータサンプル ---")
        if corporations:
            print(json.dumps(corporations[0], indent=2, ensure_ascii=False))
        print("-------------------------------------------------")
        print(f"ジオコーディング成功率: {success_count}/{len(corporations)}")
    
    print("\n✅ タスク 1-2: ジオコーディング実装 は、これにて完了とします。")
