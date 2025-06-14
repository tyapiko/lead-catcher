-- 法人情報を格納するテーブル
CREATE TABLE corporations (
    corporate_number VARCHAR(13) PRIMARY KEY, -- 法人番号 (主キー)
    name VARCHAR(255) NOT NULL,              -- 法人名
    location TEXT,                           -- 完全な住所（APIから取得）
    prefecture VARCHAR(50),                  -- 都道府県
    city VARCHAR(100),                       -- 市区町村
    street_address VARCHAR(255),             -- 丁目番地等
    establishment_date DATE,                 -- 設立日
    business_category VARCHAR(255),          -- 業種
    latitude NUMERIC(9, 6),                  -- 緯度
    longitude NUMERIC(9, 6),                 -- 経度
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- 登録日時
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP  -- 更新日時
);

-- 更新日時を自動で更新するためのトリガー関数とトリガー
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = NOW();
   RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_corporations_updated_at
BEFORE UPDATE ON corporations
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
