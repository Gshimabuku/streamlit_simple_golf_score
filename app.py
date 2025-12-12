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
                par = page["properties"]["par"]["number"] if "par" in page["properties"] and page["properties"]["par"]["number"] else 72
                
                # レート情報を取得
                gold = page["properties"]["gold"]["number"] if "gold" in page["properties"] and page["properties"]["gold"]["number"] else 4
                silver = page["properties"]["silver"]["number"] if "silver" in page["properties"] and page["properties"]["silver"]["number"] else 3
                bronze = page["properties"]["bronze"]["number"] if "bronze" in page["properties"] and page["properties"]["bronze"]["number"] else 2
                iron = page["properties"]["iron"]["number"] if "iron" in page["properties"] and page["properties"]["iron"]["number"] else 1
                diamond = page["properties"]["diamond"]["number"] if "diamond" in page["properties"] and page["properties"]["diamond"]["number"] else 5
                
                # メンバー情報を取得
                members = []
                member_names = {}
                for i in range(1, 5):
                    member_key = f"member{i}"
                    if page["properties"][member_key]["relation"]:
                        member_id = page["properties"][member_key]["relation"][0]["id"]
                        members.append(member_id)
                        # メンバー名も取得する（後でユーザー情報から名前を検索するため）
                        member_names[f"member{i}_id"] = member_id
                    else:
                        member_names[f"member{i}_id"] = None
                
                games.append({
                    "id": game_id,
                    "play_date": play_date,
                    "place": place,
                    "par": par,
                    "members": members,
                    "member_ids": member_names,  # 個別のメンバーID情報を追加
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
                birdie = page["properties"]["birdie"]["checkbox"] if "birdie" in page["properties"] and page["properties"]["birdie"] else False
                
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
                    "birdie": birdie,
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
        ["ラウンド記録", "ラウンド編集", "スコア入力", "スコア確認", "計算シート", "ユーザー管理"]
    )
    
    # サイドバーにラウンド・ホール選択を追加
    st.sidebar.divider()
    
    # ラウンド選択（全メニュー共通）
    games = notion.get_games()
    if games:
        st.sidebar.subheader("🏌️ ラウンド選択")
        game_options = {f"{game['id']} - {game['place']} ({game['play_date']})": game for game in games}
        
        # セッション状態でラウンドを管理
        if "selected_game" not in st.session_state:
            st.session_state.selected_game = None
        
        selected_game_key = st.sidebar.selectbox(
            "ラウンドを選択",
            ["選択なし"] + list(game_options.keys()),
            index=0 if st.session_state.selected_game is None else (
                list(game_options.keys()).index(st.session_state.selected_game_key) + 1 
                if "selected_game_key" in st.session_state and st.session_state.selected_game_key in game_options 
                else 0
            ),
            key="sidebar_game_select"
        )
        
        if selected_game_key != "選択なし":
            st.session_state.selected_game = game_options[selected_game_key]
            st.session_state.selected_game_key = selected_game_key
        else:
            st.session_state.selected_game = None
            st.session_state.selected_game_key = None
    
    # ホール選択（ラウンドが選択されている場合のみ表示）
    if "selected_game" in st.session_state and st.session_state.selected_game is not None:
        st.sidebar.subheader("🎯 ホール選択")
        
        # セッション状態でホール番号を管理
        if "selected_hole" not in st.session_state:
            st.session_state.selected_hole = 1
        
        # ホール選択（1-18のドロップダウン）
        hole_options = list(range(1, 19))
        selected_hole = st.sidebar.selectbox(
            "ホール番号",
            hole_options,
            index=st.session_state.selected_hole - 1,
            key="sidebar_hole_select"
        )
        
        if selected_hole != st.session_state.selected_hole:
            st.session_state.selected_hole = selected_hole
        
        # 選択中のラウンドとホールを表示
        st.sidebar.info(f"🏌️ {st.session_state.selected_game['place']}\n🎯 ホール {st.session_state.selected_hole}")
    
    st.sidebar.divider()
    
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
                total_par = st.number_input("合計パー", min_value=20, max_value=75, value=72, help="18ホール合計パー数")
            
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
                        "par": {"number": total_par},
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
        
        # 既存のユーザー一覧を取得
        users = notion.get_users()
        
        if not games:
            st.warning("編集可能なラウンドがありません。まずラウンドを記録してください。")
        else:
            # サイドバーでラウンドが選択されている場合はそれを使用
            if "selected_game" in st.session_state and st.session_state.selected_game is not None:
                selected_game = st.session_state.selected_game
                st.info(f"📌 サイドバーで選択中: {selected_game['place']} - {selected_game['play_date']}")
            else:
                # ゲーム選択（サイドバーで選択されていない場合のフォールバック）
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
                else:
                    st.warning("⬅️ サイドバーまたは上記でラウンドを選択してください。")
                    return
            
            # デバッグ情報（開発用）
            with st.expander("🔍 デバッグ情報（開発用）"):
                st.json(selected_game)
            
            with st.form("edit_round_form"):
                st.subheader("ラウンド情報編集")
                
                # 既存の値を初期値として設定
                col1, col2 = st.columns(2)
                
                with col1:
                    edit_date = st.date_input(
                        "プレー日",
                        value=datetime.strptime(selected_game['play_date'], "%Y-%m-%d").date()
                    )
                
                with col2:
                    edit_place = st.text_input(
                        "ゴルフ場名",
                        value=selected_game.get('place', '')
                    )
                
                edit_par = st.number_input(
                    "合計パー",
                    min_value=20,
                    max_value=75,
                    value=selected_game.get('par', 72),
                    help="18ホール合計パー数"
                )
                
                # メンバー選択（最大4人）
                st.subheader("メンバー選択")
                
                # メンバー選択用のオプション準備
                member_options = [{"name": "（選択なし）", "page_id": None}] + users
                
                # 現在設定されているメンバーを取得
                current_member_ids = []
                for i in range(1, 5):
                    member_id = selected_game["member_ids"].get(f'member{i}_id')
                    current_member_ids.append(member_id)
                
                # 4つのプルダウンでメンバー選択
                member_cols = st.columns(4)
                selected_member_ids = []
                
                for i in range(4):
                        with member_cols[i]:
                            # 現在設定されているメンバーのインデックスを取得
                            current_member_id = current_member_ids[i] if i < len(current_member_ids) else None
                            default_index = 0  # デフォルトは「選択なし」
                            
                            if current_member_id:
                                for idx, option in enumerate(member_options):
                                    if option["page_id"] == current_member_id:
                                        default_index = idx
                                        break
                            
                            selected_member = st.selectbox(
                                f"メンバー{i+1}",
                                member_options,
                                index=default_index,
                                format_func=lambda x: x["name"],
                                key=f"edit_member_{i+1}"
                            )
                            
                            selected_member_ids.append(selected_member["page_id"] if selected_member["page_id"] else None)
                
                # 選択されたメンバーをフィルタリング（Noneを除外）
                edit_selected_members = []
                for member_id in selected_member_ids:
                    if member_id:
                        for user in users:
                            if user["page_id"] == member_id:
                                edit_selected_members.append(user)
                                break
                
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
                    edit_iron_rate = st.number_input(
                        "鉄",
                        min_value=0,
                        max_value=100,
                        value=max(0, selected_game.get('iron', 0) or 0),
                        step=1,
                    )
                
                with col2:
                    edit_silver_rate = st.number_input(
                        "銀",
                        min_value=0,
                        max_value=100,
                        value=max(0, selected_game.get('silver', 0) or 0),
                        step=3,
                    )
                    edit_diamond_rate = st.number_input(
                        "ダイヤモンド",
                        min_value=0,
                        max_value=100,
                        value=max(0, selected_game.get('diamond', 0) or 0),
                        step=5
                    )
                
                with col3:
                    edit_bronze_rate = st.number_input(
                        "銅",
                        min_value=0,
                        max_value=100,
                        value=max(0, selected_game.get('bronze', 0) or 0),
                        step=2,
                    )
                
                if st.form_submit_button("ラウンドを更新"):
                    if not edit_selected_members:
                        st.error("少なくとも1人のメンバーを選択してください。")
                    elif not edit_place:
                        st.error("ゴルフ場名を入力してください。")
                    else:
                        # プレー日からIDを自動生成
                        edit_game_id = edit_date.strftime("%Y%m%d")
                        
                        # 更新用のプロパティを作成
                        properties = {
                            "play_date": {"date": {"start": edit_date.strftime("%Y-%m-%d")}},
                            "place": {"rich_text": [{"text": {"content": edit_place}}]},
                            "id": {"title": [{"text": {"content": edit_game_id}}]},
                            "par": {"number": edit_par},
                            "gold": {"number": edit_gold_rate},
                            "silver": {"number": edit_silver_rate},
                            "bronze": {"number": edit_bronze_rate},
                            "iron": {"number": edit_iron_rate},
                            "diamond": {"number": edit_diamond_rate}
                        }
                        
                        # メンバーのリレーションを更新（プルダウンの選択順序で設定）
                        for i in range(1, 5):
                            member_id = selected_member_ids[i-1] if i-1 < len(selected_member_ids) else None
                            if member_id:
                                properties[f"member{i}"] = {"relation": [{"id": member_id}]}
                            else:
                                properties[f"member{i}"] = {"relation": []}
                        
                        result = notion.update_page(selected_game["page_id"], properties)
                        if result:
                            st.success(f"ラウンド '{edit_game_id}' を更新しました！")
                            st.rerun()
    
    elif menu == "スコア入力":
        st.header("スコア入力")
        
        # ユーザー一覧を取得
        users = notion.get_users()
        
        if not games:
            st.warning("記録されたラウンドがありません。まずラウンドを記録してください。")
            return
        
        # サイドバーでラウンドが選択されている場合はそれを使用、そうでなければ選択を促す
        if "selected_game" in st.session_state and st.session_state.selected_game is not None:
            selected_game = st.session_state.selected_game
            st.info(f"📌 サイドバーで選択中: {selected_game['place']} - {selected_game['play_date']}")
        else:
            st.warning("⬅️ サイドバーでラウンドを選択してください。")
            return
        
        # 選択されたゲームのメンバーを取得
        user_dict = {user["page_id"]: user for user in users}
        game_members = [user_dict[member_id] for member_id in selected_game["members"] if member_id in user_dict]
        
        if not game_members:
            st.warning("このラウンドにメンバーが設定されていません。")
            return
        
        # サイドバーでホールが選択されている場合はそれを使用、そうでなければボタン形式で選択
        if "selected_hole" not in st.session_state:
            st.session_state.selected_hole = 1
        
        hole_number = st.session_state.selected_hole
        
        # ホール選択セクション（ボタン形式 - サイドバー選択と連動）
        st.subheader("🏌️ ホール選択")
        
        # 現在選択中のホールを表示
        st.info(f"📌 現在選択中: ホール {hole_number} (サイドバーから変更可能)")
        
        # クイックホール選択ボタン（オプション）
        with st.expander("🔄 クイックホール選択", expanded=False):
            # 1行目：1-9ホール
            hole_cols_1 = st.columns(9)
            for i in range(1, 10):
                with hole_cols_1[i-1]:
                    button_type = "primary" if st.session_state.selected_hole == i else "secondary"
                    if st.button(str(i), key=f"hole_{i}", type=button_type, use_container_width=True):
                        st.session_state.selected_hole = i
                        st.rerun()
            
            # 2行目：10-18ホール
            hole_cols_2 = st.columns(9)
            for i in range(10, 19):
                with hole_cols_2[i-10]:
                    button_type = "primary" if st.session_state.selected_hole == i else "secondary"
                    if st.button(str(i), key=f"hole_{i}", type=button_type, use_container_width=True):
                        st.session_state.selected_hole = i
                        st.rerun()
        
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
                    st.caption(f"ホール{hole_number}")
                    
                    # パー±での入力（既存データから取得またはデフォルト0）
                    par_relative = st.number_input(
                        f"スコア",
                        min_value=-3,
                        max_value=20,
                        value=existing_score["stroke"] if existing_score else 0,
                        key=f"stroke_{member['page_id']}_{hole_number}",  # ホール番号を含める
                        help="パーからの打数差を入力（-3～+20）"
                    )
                    
                    # スコア表示
                    if par_relative == -3:
                        st.caption("🦈 アルバトロス!")
                    elif par_relative == -2:
                        st.caption("🦅 イーグル!")
                    elif par_relative == -1:
                        st.caption("🐦 バーディー!")
                    elif par_relative == 0:
                        st.caption("⭕ パー")
                    elif par_relative == 1:
                        st.caption("➕ ボギー")
                    elif par_relative >= 2:
                        st.caption(f"➕➕ ダブルボギー以上 (+{par_relative})")
                    
                    putt = st.number_input(
                        "パット",
                        min_value=0,
                        max_value=5,
                        value=existing_score["putt"] if existing_score else 0,
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
                        max_value=20,
                        value=existing_score["snake"] if existing_score else 0,
                        key=f"snake_{member['page_id']}_{hole_number}"  # ホール番号を含める
                    )
                    
                    # 3の倍数ホール（3、6、9、12、15、18）でsnake_outチェックボックスを表示
                    snake_out = False
                    # if hole_number % 3 == 0:
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
                    'stroke': par_relative,  # パー±の値をそのまま保存
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
        
        # ユーザー一覧を取得
        users = notion.get_users()
        
        if not games:
            st.warning("記録されたラウンドがありません。")
            return
        
        # サイドバーでラウンドが選択されている場合はそれを使用、そうでなければ選択UIを表示
        if "selected_game" in st.session_state and st.session_state.selected_game is not None:
            selected_game = st.session_state.selected_game
            st.info(f"📌 サイドバーで選択中: {selected_game['place']} - {selected_game['play_date']}")
        else:
            # ゲーム選択（サイドバーで選択されていない場合のフォールバック）
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
                    "snake_out": score.get("snake_out", False),
                    "birdie": score.get("birdie", False)
                }
        
        # スコアシート形式のテーブルを作成
        st.subheader("📋 スコアシート")
        
        # テーブルデータを構築
        table_data = []
        
        # ヘッダー行
        header = ["名前"] + [str(i) for i in range(1, 10)] + ["IN"] + [str(i) for i in range(10, 19)] + ["OUT", "計"]
        table_data.append(header)
        
        # 合計パー数を取得
        total_par = selected_game.get('par', 72)
        
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
                    par_diff = score_data[member_name][hole]["stroke"]  # データベースにはパー±が保存されている
                    stroke_row.append(f"{par_diff:+d}" if par_diff != 0 else "E")
                    in_total += par_diff
                else:
                    stroke_row.append("-")
            
            # IN合計をパー±で表示
            if in_total != 0:
                stroke_row.append(f"{in_total:+d}")
            else:
                stroke_row.append("E" if any(hole in score_data[member_name] for hole in range(1, 10)) else "-")
            
            # 後半（10-18ホール）
            for hole in range(10, 19):
                if hole in score_data[member_name]:
                    par_diff = score_data[member_name][hole]["stroke"]  # データベースにはパー±が保存されている
                    stroke_row.append(f"{par_diff:+d}" if par_diff != 0 else "E")
                    out_total += par_diff
                else:
                    stroke_row.append("-")
            
            # OUT合計をパー±で表示
            if out_total != 0:
                stroke_row.append(f"{out_total:+d}")
            else:
                stroke_row.append("E" if any(hole in score_data[member_name] for hole in range(10, 19)) else "-")
            
            # 総合計を「実際スコア(パー±)」形式で表示
            total_diff = in_total + out_total
            if any(hole in score_data[member_name] for hole in range(1, 19)):
                total_actual_score = total_par + total_diff
                if total_diff != 0:
                    stroke_row.append(f"{total_actual_score}({total_diff:+d})")
                else:
                    stroke_row.append(f"{total_actual_score}(E)")
            else:
                stroke_row.append("-")
            
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
        
        # IN/OUT/計列の数値セルを太字にするスタイリング
        def style_bold_totals(df):
            def apply_bold_style(val):
                if str(val) != "-" and str(val).isdigit():
                    return "font-weight: bold"
                return ""
            
            styled_df = df.style
            for col in ["IN", "OUT", "計"]:
                if col in df.columns:
                    styled_df = styled_df.applymap(apply_bold_style, subset=[col])
            
            return styled_df
        
        # スタイル付きデータフレームを表示
        st.dataframe(style_bold_totals(df), use_container_width=True, hide_index=True)
        
        # ヘビスコア確認シートを追加
        st.subheader("🐍 ヘビスコア")
        
        # ヘビスコアのテーブルデータを構築
        snake_table_data = []
        
        # ヘッダー行（3ホールごと）
        snake_header = ["名前", "1-3", "4-6", "7-9", "10-12", "13-15", "16-18"]
        snake_table_data.append(snake_header)
        
        # 各メンバーのヘビスコア行
        for member in game_members:
            member_name = member["name"]
            snake_row = [member_name]
            
            # 3ホールごとの集計
            for start_hole in [1, 4, 7, 10, 13, 16]:
                period_snake = 0
                for hole in range(start_hole, start_hole + 3):
                    if hole in score_data[member_name]:
                        period_snake += score_data[member_name][hole]["snake"]
                
                snake_row.append(str(period_snake) if period_snake > 0 else "0")
            
            snake_table_data.append(snake_row)
        
        # 全メンバー合計行を追加
        total_row = ["合計"]
        for start_hole in [1, 4, 7, 10, 13, 16]:
            period_total = 0
            for member in game_members:
                member_name = member["name"]
                for hole in range(start_hole, start_hole + 3):
                    if hole in score_data[member_name]:
                        period_total += score_data[member_name][hole]["snake"]
            total_row.append(str(period_total))
        
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
        
        # オリンピックスコア確認シートを追加
        st.subheader("🏅 オリンピックスコア")
        
        # オリンピックスコアのテーブルデータを構築
        olympic_table_data = []
        
        # ヘッダー行
        olympic_header = ["名前", "金", "銀", "銅", "鉄", "ダイヤモンド", "合計点"]
        olympic_table_data.append(olympic_header)
        
        # オリンピック設定値を取得
        gold_rate = selected_game.get("gold", 4)
        silver_rate = selected_game.get("silver", 3)
        bronze_rate = selected_game.get("bronze", 2)
        iron_rate = selected_game.get("iron", 1)
        diamond_rate = selected_game.get("diamond", 5)
        
        # 各メンバーのオリンピックスコア行
        for member in game_members:
            member_name = member["name"]
            
            # 各オリンピックの個数をカウント
            gold_count = 0
            silver_count = 0
            bronze_count = 0
            iron_count = 0
            diamond_count = 0
            
            for hole in range(1, 19):
                if hole in score_data[member_name]:
                    olympic = score_data[member_name][hole]["olympic"]
                    if olympic == "金":
                        gold_count += 1
                    elif olympic == "銀":
                        silver_count += 1
                    elif olympic == "銅":
                        bronze_count += 1
                    elif olympic == "鉄":
                        iron_count += 1
                    elif olympic == "ダイヤモンド":
                        diamond_count += 1
            
            # 合計点を計算（個数×設定値）
            total_points = (gold_count * gold_rate + 
                           silver_count * silver_rate + 
                           bronze_count * bronze_rate + 
                           iron_count * iron_rate + 
                           diamond_count * diamond_rate)
            
            # 表示は未取得(0)の場合は '-' を表示
            gold_disp = str(gold_count) if gold_count > 0 else "-"
            silver_disp = str(silver_count) if silver_count > 0 else "-"
            bronze_disp = str(bronze_count) if bronze_count > 0 else "-"
            iron_disp = str(iron_count) if iron_count > 0 else "-"
            diamond_disp = str(diamond_count) if diamond_count > 0 else "-"
            total_disp = str(total_points) if total_points > 0 else "-"

            olympic_row = [
                member_name,
                gold_disp,
                silver_disp,
                bronze_disp,
                iron_disp,
                diamond_disp,
                total_disp
            ]
            olympic_table_data.append(olympic_row)
        
        # オリンピックスコアテーブルを表示
        olympic_df = pd.DataFrame(olympic_table_data[1:], columns=olympic_table_data[0])
        
        # 合計点列を太字にするスタイリング
        def style_olympic_totals(df):
            def apply_bold_style(val):
                if str(val).isdigit():
                    return "font-weight: bold"
                return ""
            
            styled_df = df.style
            if "合計点" in df.columns:
                styled_df = styled_df.applymap(apply_bold_style, subset=["合計点"])
            
            return styled_df
        
        st.dataframe(style_olympic_totals(olympic_df), use_container_width=True, hide_index=True)
        
        # オリンピック設定値を表示
        st.caption(f"設定値: 金={gold_rate}点, 銀={silver_rate}点, 銅={bronze_rate}点, 鉄={iron_rate}点, ダイヤモンド={diamond_rate}点")
        
        # スペシャルスコア確認シートを追加
        st.subheader("🏆 スペシャルスコア")
        
        # 各メンバーのスペシャルスコア取得数を計算
        member_special_scores = {}
        
        for member in game_members:
            member_name = member["name"]
            albatross_count = 0  # -3
            eagle_count = 0      # -2
            birdie_count = 0     # -1
            
            # 全18ホールのスペシャルスコアをカウント
            for hole in range(1, 19):
                if hole in score_data[member_name]:
                    par_diff = score_data[member_name][hole]["stroke"]
                    if par_diff == -3:
                        albatross_count += 1
                    elif par_diff == -2:
                        eagle_count += 1
                    elif par_diff == -1:
                        birdie_count += 1
            
            member_special_scores[member_name] = {
                "albatross": albatross_count,
                "eagle": eagle_count,
                "birdie": birdie_count
            }
        
        # 結果を表示
        special_score_cols = st.columns(len(game_members))
        for i, member in enumerate(game_members):
            member_name = member["name"]
            scores = member_special_scores[member_name]
            with special_score_cols[i]:
                st.markdown(f"**{member_name}**")
                if scores["albatross"] > 0:
                    st.metric("🦈 アルバトロス", scores["albatross"])
                if scores["eagle"] > 0:
                    st.metric("🦅 イーグル", scores["eagle"])
                if scores["birdie"] > 0:
                    st.metric("🐦 バーディー", scores["birdie"])
                if scores["albatross"] == 0 and scores["eagle"] == 0 and scores["birdie"] == 0:
                    st.caption("スペシャルスコアなし")
        
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
                            par_diff = hole_data['stroke']  # データベースにはパー±が保存されている
                            
                            st.write(f"**ホール {hole}**")
                            if par_diff > 0:
                                st.write(f"パー: +{par_diff}")
                            elif par_diff < 0:
                                st.write(f"パー: {par_diff}")
                            else:
                                st.write("パー: E")
                            st.write(f"パット: {hole_data['putt']}")
                            if hole_data['olympic']:
                                st.write(f"🏅 {hole_data['olympic']}")
                            else:
                                st.write("🏅 -")
                            if hole_data['snake'] > 0:
                                st.write(f"🐍 ヘビ: {hole_data['snake']}")
                            else:
                                st.write("🐍 -")
                        else:
                            st.write(f"**ホール {hole}**")
                            st.write("未記録")
    
    elif menu == "計算シート":
        st.header("💰 計算シート")
        
        # ユーザー一覧を取得
        users = notion.get_users()
        
        if not games:
            st.warning("記録されたラウンドがありません。")
            return
        
        # サイドバーでラウンドが選択されている場合はそれを使用、そうでなければ選択UIを表示
        if "selected_game" in st.session_state and st.session_state.selected_game is not None:
            selected_game = st.session_state.selected_game
            st.info(f"📌 サイドバーで選択中: {selected_game['place']} - {selected_game['play_date']}")
        else:
            # ゲーム選択（サイドバーで選択されていない場合のフォールバック）
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
        
        if len(game_members) < 2:
            st.warning("計算には最低2名のメンバーが必要です。")
            return
        
        # スコアデータを整理
        score_data = {}
        for member in game_members:
            score_data[member["name"]] = {
                "olympic_score": 0,
                "snake_score": 0,
                "special_score": 0,
                "page_id": member["page_id"]
            }
        
        # オリンピック設定値を取得
        gold_rate = selected_game.get("gold", 4)
        silver_rate = selected_game.get("silver", 3)
        bronze_rate = selected_game.get("bronze", 2)
        iron_rate = selected_game.get("iron", 1)
        diamond_rate = selected_game.get("diamond", 5)
        
        # 各イベントを記録（個別計算のため）
        events = []  # {"type": "olympic/special/snake", "player": "name", "points": int}
        
        # 各メンバーのスコアを計算
        for score in scores:
            user_name = next((user["name"] for user in users if user["page_id"] == score["user_relation"]), None)
            if user_name and user_name in score_data:
                # オリンピックスコア
                olympic = score.get("olympic", "")
                if olympic == "金":
                    score_data[user_name]["olympic_score"] += gold_rate
                    events.append({"type": "olympic", "player": user_name, "points": gold_rate})
                elif olympic == "銀":
                    score_data[user_name]["olympic_score"] += silver_rate
                    events.append({"type": "olympic", "player": user_name, "points": silver_rate})
                elif olympic == "銅":
                    score_data[user_name]["olympic_score"] += bronze_rate
                    events.append({"type": "olympic", "player": user_name, "points": bronze_rate})
                elif olympic == "鉄":
                    score_data[user_name]["olympic_score"] += iron_rate
                    events.append({"type": "olympic", "player": user_name, "points": iron_rate})
                elif olympic == "ダイヤモンド":
                    score_data[user_name]["olympic_score"] += diamond_rate
                    events.append({"type": "olympic", "player": user_name, "points": diamond_rate})
                
                # ヘビスコア
                snake = score.get("snake", 0)
                if snake > 0:
                    score_data[user_name]["snake_score"] += snake
                    events.append({"type": "snake", "player": user_name, "points": snake})
                
                # スペシャルスコア（バーディー以上）
                par_diff = score.get("stroke", 0)  # パー±
                if par_diff <= -1:  # バーディー以上
                    if par_diff == -1:  # バーディー
                        score_data[user_name]["special_score"] += 1
                        events.append({"type": "special", "player": user_name, "points": 1})
                    elif par_diff == -2:  # イーグル
                        score_data[user_name]["special_score"] += 3
                        events.append({"type": "special", "player": user_name, "points": 3})
                    elif par_diff <= -3:  # アルバトロス
                        score_data[user_name]["special_score"] += 5
                        events.append({"type": "special", "player": user_name, "points": 5})
        
        # 各メンバーの合計スコアを計算
        st.subheader("📊 スコア詳細")
        
        detail_cols = st.columns(len(game_members))
        
        for i, member in enumerate(game_members):
            member_name = member["name"]
            data = score_data[member_name]
            
            with detail_cols[i]:
                st.markdown(f"**{member_name}**")
                st.metric("🏅 オリンピック", f"+{data['olympic_score']}")
                st.metric("🏆 スペシャル", f"+{data['special_score']}")
                st.metric("🐍 ヘビ", f"-{data['snake_score']}")
        
        # 収支計算（イベントベース）
        st.subheader("💸 収支計算")
        
        # メンバー数
        num_members = len(game_members)
        other_members = num_members - 1
        
        # 各メンバーの最終収支を計算
        final_balances = {member["name"]: 0 for member in game_members}
        
        # 各イベントごとに収支を計算
        for event in events:
            event_player = event["player"]
            event_points = event["points"]
            event_type = event["type"]
            
            if event_type in ["olympic", "special"]:
                # プラスイベント：該当プレイヤーは他全員からポイントをもらう
                final_balances[event_player] += event_points * other_members
                for member_name in final_balances:
                    if member_name != event_player:
                        final_balances[member_name] -= event_points
            
            elif event_type == "snake":
                # マイナスイベント：該当プレイヤーは他全員にポイントを払う
                final_balances[event_player] -= event_points * other_members
                for member_name in final_balances:
                    if member_name != event_player:
                        final_balances[member_name] += event_points
        
        # 収支表示
        balance_cols = st.columns(len(game_members))
        for i, member in enumerate(game_members):
            member_name = member["name"]
            balance = final_balances[member_name]
            
            with balance_cols[i]:
                st.markdown(f"**{member_name}**")
                if balance > 0:
                    st.success(f"💰 +{balance:.1f}点")
                elif balance < 0:
                    st.error(f"💸 {balance:.1f}点")
                else:
                    st.info("⚖️ ±0点")
        
        # 各メンバー間の個別関係を計算
        member_relationships = {}
        
        # 各メンバーに対して他のメンバーとの関係を計算
        for member in game_members:
            member_name = member["name"]
            relationships = {}
            
            # 各イベントでこのメンバーが他のメンバーに与える/受ける影響を計算
            for event in events:
                event_player = event["player"]
                event_points = event["points"]
                event_type = event["type"]
                
                if event_type in ["olympic", "special"]:
                    # プラスイベント
                    if event_player == member_name:
                        # このメンバーがイベントを起こした場合、他全員から受け取る
                        for other_member in game_members:
                            if other_member["name"] != member_name:
                                other_name = other_member["name"]
                                if other_name not in relationships:
                                    relationships[other_name] = 0
                                relationships[other_name] += event_points
                    else:
                        # 他のメンバーがイベントを起こした場合、そのメンバーに払う
                        if event_player not in relationships:
                            relationships[event_player] = 0
                        relationships[event_player] -= event_points
                
                elif event_type == "snake":
                    # マイナスイベント
                    if event_player == member_name:
                        # このメンバーがイベントを起こした場合、他全員に払う
                        for other_member in game_members:
                            if other_member["name"] != member_name:
                                other_name = other_member["name"]
                                if other_name not in relationships:
                                    relationships[other_name] = 0
                                relationships[other_name] -= event_points
                    else:
                        # 他のメンバーがイベントを起こした場合、そのメンバーから受け取る
                        if event_player not in relationships:
                            relationships[event_player] = 0
                        relationships[event_player] += event_points
            
            member_relationships[member_name] = relationships
        
        # メンバー間関係を表示（タイトルなし）
        relationship_cols = st.columns(len(game_members))
        for i, member in enumerate(game_members):
            member_name = member["name"]
            relationships = member_relationships[member_name]
            
            with relationship_cols[i]:
                for other_name, points in relationships.items():
                    if points > 0:
                        st.write(f"{other_name}: +{points:.0f}点")
                    elif points < 0:
                        st.write(f"{other_name}: {points:.0f}点")
                    else:
                        st.write(f"{other_name}: ±0点")
        
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
