# ゴルフスコア記録アプリ

NotionDBを使用したゴルフのスコア記録Streamlitアプリです。

## 機能

- **ラウンド記録**: 新しいゴルフラウンドの情報を記録
- **スコア入力**: 各ホールのスコア（ストローク、パット、ミス数、パットゲーム）を入力
- **スコア確認**: 記録されたスコアの確認と集計
- **ユーザー管理**: プレイヤーの登録と管理

## 必要な設定

### Notion データベース構成

#### 1. users（ユーザー情報）
- `id`: title/ユーザーのID（小文字英数字）
- `name`: rich_text/表示用の名前

#### 2. games（ラウンド情報）
- `id`: title/ラウンドのID（yyyymmddhhmm）
- `play_date`: date/プレイ日
- `place`: rich_text/プレイ場所（コース名）
- `member1`: リレーション users/メンバー1
- `member2`: リレーション users/メンバー2
- `member3`: リレーション users/メンバー3
- `member4`: リレーション users/メンバー4

#### 3. scores（スコア情報）
- `id`: title/スコアのID（{game-id}_{1～4 ※メンバー〇}_hole番号）
- `game`: リレーション games/ラウンド
- `user`: リレーション users/メンバー
- `hole`: number/Hole番号
- `stroke`: number/ストローク数
- `putt`: number/パット数
- `snake`: number/ミス数
- `olympic`: select/パットゲーム（金、銀、銅、鉄、ダイヤモンド）

### 環境設定

`.streamlit/secrets.toml` ファイルに以下の設定を追加してください：

```toml
api_key = "your_notion_api_key"
user_db_id = "your_user_database_id"
game_db_id = "your_game_database_id"
score_db_id = "your_score_database_id"
```

## インストールと実行

1. 依存パッケージのインストール：
```bash
pip install -r requirements.txt
```

2. アプリの実行：
```bash
streamlit run app.py
```

## 使用方法

1. **ユーザー管理**: まず「ユーザー管理」メニューからプレイヤーを登録
2. **ラウンド記録**: 「ラウンド記録」メニューで新しいラウンドを作成
3. **スコア入力**: 「スコア入力」メニューで各ホールのスコアを記録
4. **スコア確認**: 「スコア確認」メニューで記録されたスコアを確認

## 注意事項

- Notion APIキーとデータベースIDが正しく設定されている必要があります
- ユーザーIDは小文字の英数字のみ使用できます
- 最大4名まで同時にプレイ可能です