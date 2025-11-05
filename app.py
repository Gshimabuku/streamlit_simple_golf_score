import streamlit as st
import requests
import json
from datetime import datetime, date
import os

# Notion API設定
NOTION_API_URL = "https://api.notion.com/v1"
API_KEY = st.secrets["notion"]["api_key"]
USER_DB_ID = st.secrets["notion"]["user_db_id"]
GAME_DB_ID = st.secrets["notion"]["game_db_id"]
SCORE_DB_ID = st.secrets["notion"]["score_db_id"]

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

class NotionClient:
    def __init__(self):
        self.headers = HEADERS
    
    def query_database(self, db_id, filter_dict=None):
        """データベースをクエリする"""
        url = f"{NOTION_API_URL}/databases/{db_id}/query"
        payload = {}
        if filter_dict:
            payload["filter"] = filter_dict
        
        response = requests.post(url, headers=self.headers, data=json.dumps(payload))
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error querying database: {response.status_code} - {response.text}")
            return None
    
    def create_page(self, db_id, properties):
        """新しいページを作成する"""
        url = f"{NOTION_API_URL}/pages"
        payload = {
            "parent": {"database_id": db_id},
            "properties": properties
        }
        
        response = requests.post(url, headers=self.headers, data=json.dumps(payload))
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error creating page: {response.status_code} - {response.text}")
            return None
    
    def update_page(self, page_id, properties):
        """ページを更新する"""
        url = f"{NOTION_API_URL}/pages/{page_id}"
        payload = {"properties": properties}
        
        response = requests.patch(url, headers=self.headers, data=json.dumps(payload))
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error updating page: {response.status_code} - {response.text}")
            return None
    
    def get_users(self):
        """ユーザー一覧を取得"""
        result = self.query_database(USER_DB_ID)
        users = []
        if result and "results" in result:
            for page in result["results"]:
                user_id = page["properties"]["id"]["title"][0]["text"]["content"] if page["properties"]["id"]["title"] else ""
                user_name = page["properties"]["name"]["rich_text"][0]["text"]["content"] if page["properties"]["name"]["rich_text"] else ""
                users.append({"id": user_id, "name": user_name, "page_id": page["id"]})
        return users
    
    def get_games(self):
        """ラウンド一覧を取得"""
        result = self.query_database(GAME_DB_ID)
        games = []
        if result and "results" in result:
            for page in result["results"]:
                game_id = page["properties"]["id"]["title"][0]["text"]["content"] if page["properties"]["id"]["title"] else ""
                play_date = page["properties"]["play_date"]["date"]["start"] if page["properties"]["play_date"]["date"] else ""
                place = page["properties"]["place"]["rich_text"][0]["text"]["content"] if page["properties"]["place"]["rich_text"] else ""
                
                # メンバー情報を取得
                members = []
                for i in range(1, 5):
                    member_key = f"member{i}"
                    if page["properties"][member_key]["relation"]:
                        member_id = page["properties"][member_key]["relation"][0]["id"]
                        members.append(member_id)
                
                games.append({
                    "id": game_id,
                    "play_date": play_date,
                    "place": place,
                    "members": members,
                    "page_id": page["id"]
                })
        return games
    
    def get_scores(self, game_id=None):
        """スコア一覧を取得"""
        filter_dict = None
        if game_id:
            filter_dict = {
                "property": "id",
                "title": {
                    "starts_with": game_id
                }
            }
        
        result = self.query_database(SCORE_DB_ID, filter_dict)
        scores = []
        if result and "results" in result:
            for page in result["results"]:
                score_id = page["properties"]["id"]["title"][0]["text"]["content"] if page["properties"]["id"]["title"] else ""
                hole = page["properties"]["hole"]["number"] if page["properties"]["hole"]["number"] else 0
                stroke = page["properties"]["stroke"]["number"] if page["properties"]["stroke"]["number"] else 0
                putt = page["properties"]["putt"]["number"] if page["properties"]["putt"]["number"] else 0
                snake = page["properties"]["snake"]["number"] if page["properties"]["snake"]["number"] else 0
                olympic = page["properties"]["olympic"]["select"]["name"] if page["properties"]["olympic"]["select"] else ""
                
                # ゲームとユーザーのリレーション
                game_relation = page["properties"]["game"]["relation"][0]["id"] if page["properties"]["game"]["relation"] else ""
                user_relation = page["properties"]["user"]["relation"][0]["id"] if page["properties"]["user"]["relation"] else ""
                
                scores.append({
                    "id": score_id,
                    "hole": hole,
                    "stroke": stroke,
                    "putt": putt,
                    "snake": snake,
                    "olympic": olympic,
                    "game_relation": game_relation,
                    "user_relation": user_relation,
                    "page_id": page["id"]
                })
        return scores

def main():
    st.set_page_config(page_title="ゴルフスコア記録アプリ", layout="wide")
    st.title("🏌️ ゴルフスコア記録アプリ")
    
    notion = NotionClient()
    
    # サイドバーでメニュー選択
    menu = st.sidebar.selectbox(
        "メニューを選択",
        ["ラウンド記録", "スコア入力", "スコア確認", "ユーザー管理"]
    )
    
    if menu == "ラウンド記録":
        st.header("新しいラウンドを記録")
        
        # ユーザー一覧を取得
        users = notion.get_users()
        user_options = {user["name"]: user for user in users}
        
        # ラウンド情報入力フォーム
        with st.form("round_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                play_date = st.date_input("プレイ日", value=date.today())
                place = st.text_input("プレイ場所（コース名）", placeholder="例：〇〇ゴルフクラブ")
            
            with col2:
                st.write("メンバー選択（最大4名）")
                selected_members = []
                for i in range(4):
                    member = st.selectbox(
                        f"メンバー{i+1}",
                        ["選択なし"] + list(user_options.keys()),
                        key=f"member_{i}"
                    )
                    if member != "選択なし":
                        selected_members.append(user_options[member])
            
            submitted = st.form_submit_button("ラウンドを記録")
            
            if submitted:
                if not place:
                    st.error("プレイ場所を入力してください。")
                elif len(selected_members) == 0:
                    st.error("最低1名のメンバーを選択してください。")
                else:
                    # ラウンドIDを生成（yyyymmddhhmm）
                    game_id = datetime.now().strftime("%Y%m%d%H%M")
                    
                    # Notionページのプロパティを構築
                    properties = {
                        "id": {"title": [{"text": {"content": game_id}}]},
                        "play_date": {"date": {"start": play_date.isoformat()}},
                        "place": {"rich_text": [{"text": {"content": place}}]}
                    }
                    
                    # メンバーのリレーションを追加
                    for i, member in enumerate(selected_members, 1):
                        properties[f"member{i}"] = {"relation": [{"id": member["page_id"]}]}
                    
                    result = notion.create_page(GAME_DB_ID, properties)
                    if result:
                        st.success(f"ラウンド '{game_id}' を記録しました！")
                        st.rerun()
    
    elif menu == "スコア入力":
        st.header("スコア入力")
        
        # ゲーム一覧を取得
        games = notion.get_games()
        users = notion.get_users()
        
        if not games:
            st.warning("記録されたラウンドがありません。まずラウンドを記録してください。")
            return
        
        # ゲーム選択
        game_options = {f"{game['id']} - {game['place']} ({game['play_date']})": game for game in games}
        selected_game_key = st.selectbox("ラウンドを選択", list(game_options.keys()), key="game_select")
        selected_game = game_options[selected_game_key]
        
        # 選択されたゲームのメンバーを取得
        user_dict = {user["page_id"]: user for user in users}
        game_members = [user_dict[member_id] for member_id in selected_game["members"] if member_id in user_dict]
        
        if not game_members:
            st.warning("このラウンドにメンバーが設定されていません。")
            return
        
        # ホール選択（フォーム外で配置）
        hole_number = st.selectbox("ホール番号", list(range(1, 19)), key="hole_select")
        
        st.subheader(f"ホール {hole_number} - 全メンバーのスコア入力")
        
        # 既存のスコアを確認（ホール変更時に動的に更新）
        existing_scores = notion.get_scores(selected_game["id"])
        
        # 既存データがあるかどうかを表示
        hole_scores_exist = any(score["hole"] == hole_number for score in existing_scores)
        if hole_scores_exist:
            st.info(f"ℹ️ ホール{hole_number}には既存のスコアデータがあります。既存データが入力欄に表示されています。")
        else:
            st.info(f"ℹ️ ホール{hole_number}は新規入力です。")
        
        # 全メンバーのスコア入力フォーム
        with st.form(f"hole_score_form_{hole_number}"):  # ホール番号をキーに含める
            member_scores = {}
            olympic_options = ["", "金", "銀", "銅", "鉄", "ダイヤモンド"]
            
            # メンバーを横に並べて表示
            member_cols = st.columns(len(game_members))
            
            # 各メンバーの入力欄を作成
            for i, member in enumerate(game_members):
                member_index = i + 1
                score_id = f"{selected_game['id']}_{member_index}_{hole_number}"
                existing_score = next((score for score in existing_scores if score["id"] == score_id), None)
                
                # 各メンバーのカラム内で縦に配置
                with member_cols[i]:
                    # 既存データがある場合の表示
                    data_status = "📊" if existing_score else "🆕"
                    st.markdown(f"### {member['name']} {data_status}")
                    
                    stroke = st.number_input(
                        "ストローク数",
                        min_value=1,
                        max_value=15,
                        value=existing_score["stroke"] if existing_score else 4,
                        key=f"stroke_{member['page_id']}_{hole_number}"  # ホール番号を含める
                    )
                    
                    putt = st.number_input(
                        "パット数",
                        min_value=0,
                        max_value=5,
                        value=existing_score["putt"] if existing_score else 2,
                        key=f"putt_{member['page_id']}_{hole_number}"  # ホール番号を含める
                    )
                    
                    snake = st.number_input(
                        "ミス数",
                        min_value=0,
                        max_value=10,
                        value=existing_score["snake"] if existing_score else 0,
                        key=f"snake_{member['page_id']}_{hole_number}"  # ホール番号を含める
                    )
                    
                    olympic = st.selectbox(
                        "パットゲーム",
                        olympic_options,
                        index=olympic_options.index(existing_score["olympic"]) if existing_score and existing_score["olympic"] in olympic_options else 0,
                        key=f"olympic_{member['page_id']}_{hole_number}"  # ホール番号を含める
                    )
                    
                    # 既存データの詳細情報を表示
                    if existing_score:
                        st.caption("📊 既存データが読み込まれています")
                    else:
                        st.caption("🆕 新規入力")
                
                member_scores[member['page_id']] = {
                    'member': member,
                    'member_index': member_index,
                    'score_id': score_id,
                    'stroke': stroke,
                    'putt': putt,
                    'snake': snake,
                    'olympic': olympic,
                    'existing_score': existing_score
                }
            
            st.markdown("---")  # 区切り線
            submitted = st.form_submit_button("全メンバーのスコアを保存", use_container_width=True)
            
            if submitted:
                success_count = 0
                error_count = 0
                
                # 各メンバーのスコアを保存
                for member_page_id, score_data in member_scores.items():
                    # スコアデータのプロパティを構築
                    properties = {
                        "id": {"title": [{"text": {"content": score_data['score_id']}}]},
                        "game": {"relation": [{"id": selected_game["page_id"]}]},
                        "user": {"relation": [{"id": score_data['member']['page_id']}]},
                        "hole": {"number": hole_number},
                        "stroke": {"number": score_data['stroke']},
                        "putt": {"number": score_data['putt']},
                        "snake": {"number": score_data['snake']}
                    }
                    
                    if score_data['olympic']:
                        properties["olympic"] = {"select": {"name": score_data['olympic']}}
                    
                    if score_data['existing_score']:
                        # 既存スコアを更新
                        result = notion.update_page(score_data['existing_score']['page_id'], properties)
                        if result:
                            success_count += 1
                        else:
                            error_count += 1
                    else:
                        # 新規スコアを作成
                        result = notion.create_page(SCORE_DB_ID, properties)
                        if result:
                            success_count += 1
                        else:
                            error_count += 1
                
                if error_count == 0:
                    st.success(f"ホール{hole_number}の全メンバー（{success_count}名）のスコアを保存しました！")
                    st.rerun()
                else:
                    st.warning(f"ホール{hole_number}のスコア保存完了: 成功{success_count}件、エラー{error_count}件")
    
    elif menu == "スコア確認":
        st.header("スコア確認")
        
        # ゲーム一覧を取得
        games = notion.get_games()
        users = notion.get_users()
        
        if not games:
            st.warning("記録されたラウンドがありません。")
            return
        
        # ゲーム選択
        game_options = {f"{game['id']} - {game['place']} ({game['play_date']})": game for game in games}
        selected_game_key = st.selectbox("ラウンドを選択", list(game_options.keys()))
        selected_game = game_options[selected_game_key]
        
        # スコアを取得
        scores = notion.get_scores(selected_game["id"])
        
        if not scores:
            st.warning("このラウンドのスコアが記録されていません。")
            return
        
        # ユーザー辞書を作成
        user_dict = {user["page_id"]: user for user in users}
        game_members = [user_dict[member_id] for member_id in selected_game["members"] if member_id in user_dict]
        
        # スコアカードを表示
        st.subheader(f"📊 {selected_game['place']} - {selected_game['play_date']}")
        
        # ホール別スコア表を作成
        score_data = {}
        for member in game_members:
            score_data[member["name"]] = {}
        
        for score in scores:
            user_name = next((user["name"] for user in users if user["page_id"] == score["user_relation"]), "Unknown")
            if user_name in score_data:
                score_data[user_name][score["hole"]] = {
                    "stroke": score["stroke"],
                    "putt": score["putt"],
                    "snake": score["snake"],
                    "olympic": score["olympic"]
                }
        
        # スコア表を表示
        for hole in range(1, 19):
            if any(hole in player_scores for player_scores in score_data.values()):
                st.write(f"**ホール {hole}**")
                cols = st.columns(len(game_members))
                for i, member in enumerate(game_members):
                    with cols[i]:
                        if hole in score_data[member["name"]]:
                            hole_data = score_data[member["name"]][hole]
                            st.metric(
                                member["name"],
                                f"ストローク: {hole_data['stroke']}",
                                f"パット: {hole_data['putt']}, ミス: {hole_data['snake']}"
                            )
                            if hole_data["olympic"]:
                                st.write(f"🏅 {hole_data['olympic']}")
                        else:
                            st.metric(member["name"], "未記録", "")
                st.divider()
        
        # 合計スコア計算
        st.subheader("📋 合計スコア")
        cols = st.columns(len(game_members))
        for i, member in enumerate(game_members):
            with cols[i]:
                total_stroke = sum(hole_data["stroke"] for hole_data in score_data[member["name"]].values())
                total_putt = sum(hole_data["putt"] for hole_data in score_data[member["name"]].values())
                total_snake = sum(hole_data["snake"] for hole_data in score_data[member["name"]].values())
                holes_played = len(score_data[member["name"]])
                
                st.metric(
                    member["name"],
                    f"総ストローク: {total_stroke}",
                    f"ホール数: {holes_played}/18"
                )
                st.write(f"総パット: {total_putt}")
                st.write(f"総ミス: {total_snake}")
    
    elif menu == "ユーザー管理":
        st.header("ユーザー管理")
        
        # 既存ユーザー一覧
        users = notion.get_users()
        if users:
            st.subheader("登録済みユーザー")
            for user in users:
                st.write(f"- {user['name']} (ID: {user['id']})")
        
        st.subheader("新しいユーザーを追加")
        
        with st.form("user_form"):
            user_id = st.text_input(
                "ユーザーID",
                placeholder="例：yamada123（小文字英数字）",
                help="小文字の英数字のみ使用してください"
            )
            user_name = st.text_input(
                "表示名",
                placeholder="例：山田太郎"
            )
            
            submitted = st.form_submit_button("ユーザーを追加")
            
            if submitted:
                if not user_id or not user_name:
                    st.error("ユーザーIDと表示名の両方を入力してください。")
                elif not user_id.islower() or not user_id.isalnum():
                    st.error("ユーザーIDは小文字の英数字のみ使用してください。")
                else:
                    # 重複チェック
                    existing_ids = [user["id"] for user in users]
                    if user_id in existing_ids:
                        st.error("このユーザーIDは既に使用されています。")
                    else:
                        # ユーザーを作成
                        properties = {
                            "id": {"title": [{"text": {"content": user_id}}]},
                            "name": {"rich_text": [{"text": {"content": user_name}}]}
                        }
                        
                        result = notion.create_page(USER_DB_ID, properties)
                        if result:
                            st.success(f"ユーザー '{user_name}' を追加しました！")
                            st.rerun()

if __name__ == "__main__":
    main()
