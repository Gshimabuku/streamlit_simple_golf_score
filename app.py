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
                
                # レート情報を取得
                gold = page["properties"]["gold"]["number"] if "gold" in page["properties"] and page["properties"]["gold"]["number"] else 4
                silver = page["properties"]["silver"]["number"] if "silver" in page["properties"] and page["properties"]["silver"]["number"] else 3
                bronze = page["properties"]["bronze"]["number"] if "bronze" in page["properties"] and page["properties"]["bronze"]["number"] else 2
                iron = page["properties"]["iron"]["number"] if "iron" in page["properties"] and page["properties"]["iron"]["number"] else 1
                diamond = page["properties"]["diamond"]["number"] if "diamond" in page["properties"] and page["properties"]["diamond"]["number"] else 5
                
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
                    "gold": gold,
                    "silver": silver,
                    "bronze": bronze,
                    "iron": iron,
                    "diamond": diamond,
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
                snake_out = page["properties"]["snake_out"]["checkbox"] if "snake_out" in page["properties"] and page["properties"]["snake_out"] else False
                
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
                    "snake_out": snake_out,
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
        ["ラウンド記録", "ラウンド編集", "スコア入力", "スコア確認", "ユーザー管理"]
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
            
            # オリンピックレート設定
            st.write("🏅 オリンピックレート設定")
            rate_col1, rate_col2, rate_col3 = st.columns(3)
            
            with rate_col1:
                gold_rate = st.number_input("金", min_value=0, max_value=100, value=4, help="金の点数")
                iron_rate = st.number_input("鉄", min_value=0, max_value=100, value=1, help="鉄の点数")
            
            with rate_col2:
                silver_rate = st.number_input("銀", min_value=0, max_value=100, value=3, help="銀の点数")
                diamond_rate = st.number_input("ダイヤモンド", min_value=0, max_value=100, value=5, help="ダイヤモンドの点数")
            
            with rate_col3:
                bronze_rate = st.number_input("銅", min_value=0, max_value=100, value=2, help="銅の点数")
            
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
                        "place": {"rich_text": [{"text": {"content": place}}]},
                        "gold": {"number": gold_rate},
                        "silver": {"number": silver_rate},
                        "bronze": {"number": bronze_rate},
                        "iron": {"number": iron_rate},
                        "diamond": {"number": diamond_rate}
                    }
                    
                    # メンバーのリレーションを追加
                    for i, member in enumerate(selected_members, 1):
                        properties[f"member{i}"] = {"relation": [{"id": member["page_id"]}]}
                    
                    result = notion.create_page(GAME_DB_ID, properties)
                    if result:
                        st.success(f"ラウンド '{game_id}' を記録しました！")
                        st.rerun()
    
    elif menu == "ラウンド編集":
        st.header("ラウンド編集")
        
        # 既存のゲーム一覧を取得
        games = notion.get_games()
        users = notion.get_users()
        
        if not games:
            st.warning("編集可能なラウンドがありません。まずラウンドを記録してください。")
        else:
            # ゲーム選択
            game_options = []
            for game in games:
                date_str = game['play_date']
                place = game['place']
                members = []
                for i in range(1, 5):
                    member_name = game.get(f'member{i}_name')
                    if member_name:
                        members.append(member_name)
                
                game_info = f"{date_str} - {place} ({', '.join(members)})"
                game_options.append({"label": game_info, "value": game})
            
            selected_game_option = st.selectbox(
                "編集するラウンドを選択してください",
                game_options,
                format_func=lambda x: x["label"]
            )
            
            if selected_game_option:
                selected_game = selected_game_option["value"]
                
                with st.form("edit_round_form"):
                    st.subheader("ラウンド情報編集")
                    
                    # 既存の値を初期値として設定
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        edit_date = st.date_input(
                            "プレー日",
                            value=datetime.strptime(selected_game['play_date'], "%Y-%m-%d").date()
                        )
                        
                        edit_place = st.text_input(
                            "ゴルフ場名",
                            value=selected_game.get('place', '')
                        )
                    
                    with col2:
                        edit_game_id = st.text_input(
                            "ラウンドID",
                            value=selected_game.get('game_id', '')
                        )
                    
                    # メンバー選択（最大4人）
                    st.subheader("メンバー選択")
                    
                    # 現在のメンバーを取得
                    current_members = []
                    for i in range(1, 5):
                        member_name = selected_game.get(f'member{i}_name')
                        if member_name:
                            # ユーザーリストから該当するユーザーを検索
                            for user in users:
                                if user["name"] == member_name:
                                    current_members.append(user)
                                    break
                    
                    edit_selected_members = st.multiselect(
                        "メンバーを選択してください（最大4人）",
                        users,
                        default=current_members,
                        format_func=lambda x: x["name"],
                        max_selections=4
                    )
                    # オリンピック設定
                    st.subheader("オリンピック設定")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        edit_gold_rate = st.number_input(
                            "金",
                            min_value=0,
                            max_value=100,
                            value=max(0, selected_game.get('gold', 0) or 0),
                            step=4,
                        )
                        
                        edit_silver_rate = st.number_input(
                            "銀",
                            min_value=0,
                            max_value=100,
                            value=max(0, selected_game.get('silver', 0) or 0),
                            step=3,
                        )
                    
                    with col2:
                        edit_bronze_rate = st.number_input(
                            "銅",
                            min_value=0,
                            max_value=100,
                            value=max(0, selected_game.get('bronze', 0) or 0),
                            step=2,
                        )
                        
                        edit_iron_rate = st.number_input(
                            "鉄",
                            min_value=0,
                            max_value=100,
                            value=max(0, selected_game.get('iron', 0) or 0),
                            step=1,
                        )
                    
                    with col3:
                        edit_diamond_rate = st.number_input(
                            "ダイヤモンド",
                            min_value=0,
                            max_value=100,
                            value=max(0, selected_game.get('diamond', 0) or 0),
                            step=5
                        )
                    
                    if st.form_submit_button("ラウンドを更新"):
                        if not edit_selected_members:
                            st.error("少なくとも1人のメンバーを選択してください。")
                        elif not edit_place:
                            st.error("ゴルフ場名を入力してください。")
                        elif not edit_game_id:
                            st.error("ラウンドIDを入力してください。")
                        else:
                            # 更新用のプロパティを作成
                            properties = {
                                "play_date": {"date": {"start": edit_date.strftime("%Y-%m-%d")}},
                                "place": {"rich_text": [{"text": {"content": edit_place}}]},
                                "game_id": {"title": [{"text": {"content": edit_game_id}}]},
                                "gold": {"number": edit_gold_rate},
                                "silver": {"number": edit_silver_rate},
                                "bronze": {"number": edit_bronze_rate},
                                "iron": {"number": edit_iron_rate},
                                "diamond": {"number": edit_diamond_rate}
                            }
                            
                            # メンバーのリレーションを更新（既存をクリアして新規設定）
                            for i in range(1, 5):
                                if i <= len(edit_selected_members):
                                    properties[f"member{i}"] = {"relation": [{"id": edit_selected_members[i-1]["page_id"]}]}
                                else:
                                    properties[f"member{i}"] = {"relation": []}
                            
                            result = notion.update_page(selected_game["page_id"], properties)
                            if result:
                                st.success(f"ラウンド '{edit_game_id}' を更新しました！")
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
            
            # ヘッダーと保存ボタンを同じ行に配置
            header_col, button_col = st.columns([3, 1])
            with header_col:
                st.subheader(f"ホール {hole_number} - 全メンバーのスコア入力")
            with button_col:
                submitted = st.form_submit_button("保存", use_container_width=True, type="primary")
            
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
                        "ストローク",
                        min_value=1,
                        max_value=15,
                        value=existing_score["stroke"] if existing_score else 4,
                        key=f"stroke_{member['page_id']}_{hole_number}"  # ホール番号を含める
                    )
                    
                    putt = st.number_input(
                        "パット",
                        min_value=0,
                        max_value=5,
                        value=existing_score["putt"] if existing_score else 2,
                        key=f"putt_{member['page_id']}_{hole_number}"  # ホール番号を含める
                    )
                    
                    olympic = st.selectbox(
                        "オリンピック",
                        olympic_options,
                        index=olympic_options.index(existing_score["olympic"]) if existing_score and existing_score["olympic"] in olympic_options else 0,
                        key=f"olympic_{member['page_id']}_{hole_number}"  # ホール番号を含める
                    )
                    
                    snake = st.number_input(
                        "ヘビ",
                        min_value=0,
                        max_value=10,
                        value=existing_score["snake"] if existing_score else 0,
                        key=f"snake_{member['page_id']}_{hole_number}"  # ホール番号を含める
                    )
                    
                    # 3の倍数ホール（3、6、9、12、15、18）でsnake_outチェックボックスを表示
                    snake_out = False
                    if hole_number % 3 == 0:
                        snake_out = st.checkbox(
                            "🐍アウト",
                            value=existing_score["snake_out"] if existing_score else False,
                            key=f"snake_out_{member['page_id']}_{hole_number}",
                            help="このホールでヘビアウトになった場合にチェック"
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
                    'snake_out': snake_out,
                    'existing_score': existing_score
                }
            
            if submitted:
                # 3の倍数ホールでのsnake_outバリデーション
                if hole_number % 3 == 0:
                    snake_out_count = sum(1 for score_data in member_scores.values() if score_data['snake_out'])
                    if snake_out_count > 1:
                        st.error("🐍アウトは1人だけ選択できます。")
                        st.stop()
                
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
                    
                    # 3の倍数ホールの場合のみsnake_outを追加
                    if hole_number % 3 == 0:
                        properties["snake_out"] = {"checkbox": score_data['snake_out']}
                    
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
                    "olympic": score["olympic"],
                    "snake_out": score.get("snake_out", False)
                }
        
        # スコアシート形式のテーブルを作成
        st.subheader("📋 スコアシート")
        
        # テーブルデータを構築
        table_data = []
        
        # ヘッダー行
        header = ["名前"] + [str(i) for i in range(1, 10)] + ["IN"] + [str(i) for i in range(10, 19)] + ["OUT", "計"]
        table_data.append(header)
        
        # 各メンバーのスコア行
        for member in game_members:
            member_name = member["name"]
            
            # ストローク行
            stroke_row = [member_name]
            in_total = 0
            out_total = 0
            
            # 前半（1-9ホール）
            for hole in range(1, 10):
                if hole in score_data[member_name]:
                    stroke = score_data[member_name][hole]["stroke"]
                    stroke_row.append(str(stroke))
                    in_total += stroke
                else:
                    stroke_row.append("-")
            
            stroke_row.append(str(in_total) if in_total > 0 else "-")
            
            # 後半（10-18ホール）
            for hole in range(10, 19):
                if hole in score_data[member_name]:
                    stroke = score_data[member_name][hole]["stroke"]
                    stroke_row.append(str(stroke))
                    out_total += stroke
                else:
                    stroke_row.append("-")
            
            stroke_row.append(str(out_total) if out_total > 0 else "-")
            stroke_row.append(str(in_total + out_total) if (in_total > 0 and out_total > 0) else "-")
            
            table_data.append(stroke_row)
            
            # パット行
            putt_row = [""]  # 名前欄は空白
            in_putt_total = 0
            out_putt_total = 0
            
            # 前半（1-9ホール）
            for hole in range(1, 10):
                if hole in score_data[member_name]:
                    putt = score_data[member_name][hole]["putt"]
                    putt_row.append(str(putt))
                    in_putt_total += putt
                else:
                    putt_row.append("-")
            
            putt_row.append(str(in_putt_total) if in_putt_total > 0 else "-")
            
            # 後半（10-18ホール）
            for hole in range(10, 19):
                if hole in score_data[member_name]:
                    putt = score_data[member_name][hole]["putt"]
                    putt_row.append(str(putt))
                    out_putt_total += putt
                else:
                    putt_row.append("-")
            
            putt_row.append(str(out_putt_total) if out_putt_total > 0 else "-")
            putt_row.append(str(in_putt_total + out_putt_total) if (in_putt_total > 0 and out_putt_total > 0) else "-")
            
            table_data.append(putt_row)
        
        # Streamlitでテーブルを表示
        import pandas as pd
        df = pd.DataFrame(table_data[1:], columns=table_data[0])
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # ヘビスコア確認シートを追加
        st.subheader("🐍 ヘビスコア")
        
        # ヘビスコアのテーブルデータを構築
        snake_table_data = []
        
        # ヘッダー行（3ホールごと）
        snake_header = ["名前", "1-3", "4-6", "7-9", "10-12", "13-15", "16-18", "計"]
        snake_table_data.append(snake_header)
        
        # 各メンバーのヘビスコア行
        for member in game_members:
            member_name = member["name"]
            snake_row = [member_name]
            total_snake = 0
            
            # 3ホールごとの集計
            for start_hole in [1, 4, 7, 10, 13, 16]:
                period_snake = 0
                for hole in range(start_hole, start_hole + 3):
                    if hole in score_data[member_name]:
                        period_snake += score_data[member_name][hole]["snake"]
                
                snake_row.append(str(period_snake) if period_snake > 0 else "0")
                total_snake += period_snake
            
            snake_row.append(str(total_snake))
            snake_table_data.append(snake_row)
        
        # 全メンバー合計行を追加
        total_row = ["合計"]
        grand_total = 0
        for start_hole in [1, 4, 7, 10, 13, 16]:
            period_total = 0
            for member in game_members:
                member_name = member["name"]
                for hole in range(start_hole, start_hole + 3):
                    if hole in score_data[member_name]:
                        period_total += score_data[member_name][hole]["snake"]
            total_row.append(str(period_total))
            grand_total += period_total
        
        total_row.append(str(grand_total))
        snake_table_data.append(total_row)
        
        # アウトメンバー行を追加
        out_row = ["アウト"]
        for target_hole in [3, 6, 9, 12, 15, 18]:
            out_members = []
            for member in game_members:
                member_name = member["name"]
                if target_hole in score_data[member_name] and score_data[member_name][target_hole].get("snake_out", False):
                    out_members.append(member_name)
            
            if out_members:
                out_row.append(", ".join(out_members))
            else:
                out_row.append("-")
        
        out_row.append("-")  # 計の欄
        snake_table_data.append(out_row)
        
        # ヘビスコアテーブルを表示
        snake_df = pd.DataFrame(snake_table_data[1:], columns=snake_table_data[0])
        st.dataframe(snake_df, use_container_width=True, hide_index=True)
        
        # 各メンバーのOUT合計を計算
        member_out_totals = {}
        
        for member in game_members:
            member_name = member["name"]
            total_out_score = 0
            
            # 3の倍数ホール（3、6、9、12、15、18）をチェック
            for target_hole in [3, 6, 9, 12, 15, 18]:
                if target_hole in score_data[member_name] and score_data[member_name][target_hole].get("snake_out", False):
                    # そのホールまでの3ホール区間の全メンバー合計ヘビ数を計算
                    start_hole = target_hole - 2  # 3→1, 6→4, 9→7, 12→10, 15→13, 18→16
                    period_total = 0
                    
                    for check_member in game_members:
                        check_member_name = check_member["name"]
                        for hole in range(start_hole, target_hole + 1):
                            if hole in score_data[check_member_name]:
                                period_total += score_data[check_member_name][hole]["snake"]
                    
                    total_out_score += period_total
            
            member_out_totals[member_name] = total_out_score
        
        # 結果を表示
        out_total_cols = st.columns(len(game_members))
        for i, member in enumerate(game_members):
            member_name = member["name"]
            with out_total_cols[i]:
                st.metric(
                    member_name,
                    f"{member_out_totals[member_name]}",
                    help="OUTになった時の3ホール区間合計ヘビ数の累計"
                )
        
        # 詳細情報（オリンピック、ヘビ）の表示
        st.subheader("🏅 詳細情報")
        
        for member in game_members:
            member_name = member["name"]
            with st.expander(f"{member_name} の詳細"):
                detail_cols = st.columns(6)
                
                for hole in range(1, 19):
                    col_index = (hole - 1) % 6
                    with detail_cols[col_index]:
                        if hole in score_data[member_name]:
                            hole_data = score_data[member_name][hole]
                            st.write(f"**ホール {hole}**")
                            st.write(f"ストローク: {hole_data['stroke']}")
                            st.write(f"パット: {hole_data['putt']}")
                            if hole_data['olympic']:
                                st.write(f"🏅 {hole_data['olympic']}")
                            if hole_data['snake'] > 0:
                                st.write(f"🐍 ヘビ: {hole_data['snake']}")
                            # 3の倍数ホールでsnake_outを表示
                            if hole % 3 == 0 and hole_data.get('snake_out', False):
                                st.write("🐍 **アウト!**")
                        else:
                            st.write(f"**ホール {hole}**")
                            st.write("未記録")
    
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
