import streamlit as st
import pandas as pd
import requests
from datetime import date
import os # osモジュールをインポート

# --- ▼▼▼ 変更点 ▼▼▼ ---
# 環境変数からAPIのURLを取得。なければデフォルト値を使う。
API_URL = os.getenv("API_URL", "http://localhost:8000") + "/corporations"
# --- ▲▲▲ ここまで ▲▲▲ ---

# ページの基本設定
st.set_page_config(
    page_title="Lead Catcher",
    page_icon="✨",
    layout="wide",
)

# --- 関数定義 ---
@st.cache_data(ttl=600)
def fetch_data_from_api(prefecture: str | None, start_date: date | None, end_date: date | None):
    """
    バックエンドAPIから法人情報を取得し、Pandas DataFrameとして返す関数。
    """
    params = {}
    if prefecture:
        params['prefecture'] = prefecture
    if start_date:
        params['start_date'] = start_date.strftime('%Y-%m-%d')
    if end_date:
        params['end_date'] = end_date.strftime('%Y-%m-%d')
    
    try:
        response = requests.get(API_URL, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"APIへの接続に失敗しました。バックエンドが起動しているか確認してください。: {e}")
        return None
    except Exception as e:
        st.error(f"データの取得中に不明なエラーが発生しました: {e}")
        return None

# --- サイドバー (入力フォーム) ---
st.sidebar.header("絞り込み検索 🔎")
pref_input = st.sidebar.text_input("都道府県名で検索", placeholder="例: 東京都")
start_date_input = st.sidebar.date_input("設立日（開始）", value=None)
end_date_input = st.sidebar.date_input("設立日（終了）", value=None)

# --- メイン画面 (表示エリア) ---
st.title("✨ Lead Catcher: 新規法人情報")
corporations_data = fetch_data_from_api(pref_input, start_date_input, end_date_input)

if corporations_data is not None:
    if not corporations_data:
        st.info("指定された条件の法人情報はありませんでした。")
    else:
        df = pd.DataFrame(corporations_data)
        
        st.subheader("📍 法人所在地マップ")
        df_map = df.dropna(subset=['latitude', 'longitude'])
        
        if not df_map.empty:
            st.map(df_map)
        else:
            st.info("地図に表示できる位置情報を持つ法人がありません。")
        
        st.subheader("📄 法人情報一覧")
        display_columns = ["name", "location", "establishment_date", "business_category"]
        df_display = df[[col for col in display_columns if col in df.columns]]
        
        st.write(f"**{len(df_display)}** 件の法人情報が見つかりました。")
        st.dataframe(df_display, use_container_width=True, height=400)
else:
    st.warning("データを表示できませんでした。")
