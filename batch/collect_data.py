import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta
import json

# .envファイルから環境変数を読み込む
load_dotenv()

# .envファイルからAPIキーを取得
API_TOKEN = os.getenv('GBIZINFO_API_KEY') # 変数名もtokenに合わせましたが、.envファイルは変更不要です

# 【正】判明した正しいURL
URL = "https://info.gbiz.go.jp/hojin/v1/hojin/updateInfo"


def fetch_new_corporations():
    """
    gBizINFO APIから前日分の法人情報を取得する関数
    """
    if not API_TOKEN:
        print("エラー: APIキーが設定されていません。.envファイルを確認してください。")
        return None

    # 【正】判明した正しいヘッダー名
    headers = {
        "X-hojinInfo-api-token": API_TOKEN,
    }

    # 【正】判明した正しい日付フォーマット YYYYMMDD
    yesterday = datetime.now() - timedelta(days=1)
    date_str = yesterday.strftime('%Y%m%d')
    
    # 【正】判明した正しいパラメータ (pageを追加)
    params = {
        "from": date_str,
        "to": date_str,
        "page": 1
    }

    print(f"最終修正版で、{date_str} の法人データを取得します...")

    try:
        response = requests.get(URL, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        return data

    except requests.exceptions.RequestException as e:
        print(f"APIリクエスト中にエラーが発生しました: {e}")
        if e.response is not None:
            try:
                error_details = e.response.json()
                print(f"エラーレスポンス: {json.dumps(error_details, indent=2, ensure_ascii=False)}")
            except json.JSONDecodeError:
                print(f"エラーレスポンス: {e.response.text}")
        return None

if __name__ == '__main__':
    result = fetch_new_corporations()

    if result and 'hojin-infos' in result:
        corporations = result['hojin-infos']
        
        # データが0件の場合のメッセージ
        if not corporations:
            print("🎉 データ取得に成功しましたが、対象期間の法人は0件でした。")
        else:
            count = len(corporations)
            total_count = result.get('totalCount', '不明')
            print(f"🎉 取得成功！ {total_count} 件中、最初のページの {count} 件を取得しました。")
            
            print("\n--- 最初の1件のデータサンプル ---")
            print(json.dumps(corporations[0], indent=2, ensure_ascii=False))
            print("------------------------------")
        
        print("\n✅ タスク 1-1: API接続 は、これにて完全に完了です！")

    elif result:
        print("データ取得に成功しましたが、'hojin-infos'キーが見つかりませんでした。")
        print("APIからのレスポンス:", result)
