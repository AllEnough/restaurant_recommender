import hashlib
import html
from datetime import date

import folium
import streamlit as st
from streamlit_folium import st_folium

from recommender import get_mood_strategy, load_data, recommend_restaurants
from recipe_recommender import collect_ingredient_options, load_recipes, parse_ingredients, recommend_recipes

st.set_page_config(page_title="今天吃什麼", layout="wide")

def inject_design_system():
    st.markdown(
        """
        <style>
        :root {
            --bg: #f8fafc;
            --surface: #ffffff;
            --surface-soft: #f1f5f9;
            --text: #0f172a;
            --muted: #64748b;
            --line: #e2e8f0;
            --primary: #ef4444;
            --primary-dark: #dc2626;
            --accent: #0f766e;
            --accent-soft: #ccfbf1;
            --amber-soft: #fef3c7;
            --shadow: 0 18px 45px rgba(15, 23, 42, 0.08);
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(239, 68, 68, 0.10), transparent 28rem),
                linear-gradient(180deg, #fff7ed 0%, var(--bg) 18rem);
            color: var(--text);
        }

        section[data-testid="stSidebar"] {
            background: rgba(255, 255, 255, 0.82);
            border-right: 1px solid rgba(226, 232, 240, 0.9);
            box-shadow: 10px 0 35px rgba(15, 23, 42, 0.05);
        }

        section[data-testid="stSidebar"] > div {
            padding-top: 1.6rem;
        }

        section[data-testid="stSidebar"] *,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span {
            color: #0f172a;
        }

        .block-container {
            padding-top: 2.2rem;
            padding-bottom: 4rem;
            max-width: 1180px;
        }

        h1, h2, h3 {
            color: var(--text);
            letter-spacing: 0;
        }

        div[data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.92);
            border: 1px solid rgba(226, 232, 240, 0.9);
            border-radius: 18px;
            padding: 1rem 1.1rem;
            box-shadow: var(--shadow);
        }

        div[data-testid="stMetric"] label,
        div[data-testid="stMetricLabel"] {
            color: var(--muted);
            font-size: 0.88rem;
        }

        div[data-testid="stMetricValue"] {
            color: var(--text);
            font-weight: 800;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            border: 1px solid rgba(226, 232, 240, 0.95);
            border-radius: 20px;
            background: rgba(255, 255, 255, 0.94);
            box-shadow: var(--shadow);
        }

        div[data-testid="stAlert"] {
            border-radius: 16px;
            border: 1px solid rgba(226, 232, 240, 0.95);
            box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05);
        }

        .stButton > button {
            border-radius: 999px;
            border: 1px solid rgba(239, 68, 68, 0.24);
            background: #ffffff !important;
            color: var(--primary-dark) !important;
            font-weight: 700;
            padding: 0.45rem 1rem;
            transition: all 0.15s ease;
        }

        .stButton > button:hover {
            border-color: var(--primary);
            background: #fff1f2 !important;
            color: var(--primary-dark) !important;
            transform: translateY(-1px);
            box-shadow: 0 10px 22px rgba(239, 68, 68, 0.14);
        }

        button[data-testid="stBaseButton-secondary"] {
            border-radius: 999px !important;
            border: 1px solid rgba(239, 68, 68, 0.24) !important;
            background: #ffffff !important;
            color: var(--primary-dark) !important;
            font-weight: 800 !important;
        }

        button[data-testid="stBaseButton-secondary"]:hover {
            background: #fff1f2 !important;
            color: var(--primary-dark) !important;
            border-color: var(--primary) !important;
            box-shadow: 0 10px 22px rgba(239, 68, 68, 0.14) !important;
        }

        .stButton > button:disabled {
            background: #f1f5f9 !important;
            color: #94a3b8 !important;
            border-color: #e2e8f0;
            box-shadow: none;
        }

        button[data-testid="stBaseButton-secondary"]:disabled {
            background: #f1f5f9 !important;
            color: #94a3b8 !important;
            border-color: #e2e8f0 !important;
            box-shadow: none !important;
        }

        div[data-testid="stRadio"] {
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid rgba(226, 232, 240, 0.95);
            border-radius: 18px;
            padding: 0.85rem 1rem;
            box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05);
        }

        div[data-testid="stRadio"] label,
        div[data-testid="stRadio"] p,
        div[data-testid="stRadio"] span {
            color: #0f172a !important;
        }

        div[data-testid="stSlider"] [role="slider"] {
            background-color: var(--primary);
            border-color: var(--primary);
        }

        div[data-baseweb="select"] > div {
            background: #ffffff !important;
            border-radius: 14px !important;
            border-color: #e2e8f0 !important;
            color: #0f172a !important;
        }

        div[data-baseweb="select"] span,
        div[data-baseweb="select"] div {
            color: #0f172a !important;
        }

        textarea,
        input {
            background: #ffffff !important;
            border-radius: 14px !important;
            border-color: #e2e8f0 !important;
            color: #0f172a !important;
        }

        textarea::placeholder,
        input::placeholder {
            color: #94a3b8 !important;
        }

        details {
            border-radius: 16px !important;
        }

        hr {
            margin: 1.8rem 0;
            border-color: rgba(226, 232, 240, 0.85);
        }

        .app-hero {
            position: relative;
            overflow: hidden;
            border-radius: 28px;
            padding: 2rem;
            margin-bottom: 1.3rem;
            background:
                linear-gradient(135deg, rgba(15, 23, 42, 0.94), rgba(127, 29, 29, 0.86)),
                url("https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=1600&q=80");
            background-size: cover;
            background-position: center;
            color: #ffffff;
            box-shadow: 0 24px 70px rgba(15, 23, 42, 0.22);
        }

        .app-hero__eyebrow {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            padding: 0.32rem 0.72rem;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.16);
            border: 1px solid rgba(255, 255, 255, 0.22);
            font-size: 0.82rem;
            font-weight: 700;
        }

        .app-hero h1 {
            color: #ffffff;
            margin: 1rem 0 0.45rem;
            font-size: clamp(2rem, 5vw, 4rem);
            line-height: 1.05;
            font-weight: 900;
        }

        .app-hero p {
            max-width: 48rem;
            margin: 0;
            color: rgba(255, 255, 255, 0.86);
            font-size: 1.04rem;
            line-height: 1.75;
        }

        .section-kicker {
            display: inline-flex;
            align-items: center;
            padding: 0.35rem 0.72rem;
            border-radius: 999px;
            background: var(--accent-soft);
            color: #115e59;
            font-size: 0.82rem;
            font-weight: 800;
            margin: 0.4rem 0 0.6rem;
        }

        .soft-note {
            border: 1px solid rgba(226, 232, 240, 0.95);
            border-radius: 18px;
            background: rgba(255, 255, 255, 0.88);
            padding: 1rem 1.1rem;
            color: var(--muted);
            margin-bottom: 1rem;
        }

        .tag-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.42rem;
            margin: 0.2rem 0 0.8rem;
        }

        .tag-pill {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 0.26rem 0.62rem;
            background: #f1f5f9;
            color: #334155;
            font-size: 0.82rem;
            font-weight: 700;
            border: 1px solid #e2e8f0;
        }

        .rank-chip {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-width: 2.2rem;
            height: 2.2rem;
            border-radius: 999px;
            background: #fee2e2;
            color: #991b1b;
            font-weight: 900;
            margin-right: 0.55rem;
        }

        .reason-box {
            border-radius: 14px;
            padding: 0.8rem 0.95rem;
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            color: #475569;
            line-height: 1.65;
        }

        @media (max-width: 768px) {
            .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
            }
            .app-hero {
                border-radius: 20px;
                padding: 1.35rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_page_header():
    st.markdown(
        """
        <section class="app-hero">
            <div class="app-hero__eyebrow">餐廳與食譜推薦系統</div>
            <h1>今天吃什麼</h1>
            <p>依照外食條件、心情、冰箱食材與保存狀態，快速整理出更適合今天的餐廳或食譜推薦。</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_section_kicker(text):
    st.markdown(f'<div class="section-kicker">{html.escape(text)}</div>', unsafe_allow_html=True)


inject_design_system()
render_page_header()

mode = st.radio(
    "今天想怎麼吃？",
    ["我要外食", "我要自己煮"],
    horizontal=True,
    label_visibility="visible",
)

if "favorite_restaurants" not in st.session_state:
    st.session_state.favorite_restaurants = []
if "favorite_recipes" not in st.session_state:
    st.session_state.favorite_recipes = []
if "restaurant_decision" not in st.session_state:
    st.session_state.restaurant_decision = None
if "recipe_decision" not in st.session_state:
    st.session_state.recipe_decision = None


def add_favorite(kind, name):
    key = "favorite_restaurants" if kind == "restaurant" else "favorite_recipes"
    if name not in st.session_state[key]:
        st.session_state[key].append(name)


def render_favorites():
    with st.sidebar.expander("我的收藏", expanded=False):
        if st.session_state.favorite_restaurants:
            st.write("外食收藏")
            for item in st.session_state.favorite_restaurants:
                st.write(f"- {item}")
        if st.session_state.favorite_recipes:
            st.write("內食收藏")
            for item in st.session_state.favorite_recipes:
                st.write(f"- {item}")
        if not st.session_state.favorite_restaurants and not st.session_state.favorite_recipes:
            st.caption("目前還沒有收藏。")
        if st.session_state.favorite_restaurants or st.session_state.favorite_recipes:
            if st.button("清空收藏"):
                st.session_state.favorite_restaurants = []
                st.session_state.favorite_recipes = []
                st.rerun()


render_favorites()


def get_daily_index(seed_text, total):
    if total <= 0:
        return 0
    seed = f"{date.today().isoformat()}-{seed_text}"
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % total


def build_restaurant_fortune(result, mood):
    if result.empty:
        return None
    selected = result.iloc[get_daily_index(mood + "外食", len(result))]
    messages = {
        "省錢": "今天適合走精準省錢路線，把錢花在真正值得的一餐。",
        "疲累": "今天先降低決策成本，近一點、快一點，就是好選擇。",
        "開心": "今天可以選一間評價穩的店，把吃飯變成小小慶祝。",
        "心情不好": "今天先照顧自己，選一個吃完會舒服一點的選項。",
        "選擇困難": "今天交給系統決定，少想一點也不錯。",
    }
    return (
        f"今日外食籤：{messages.get(mood, '今天適合選一個條件最平衡的餐廳。')}"
        f"幸運餐點是 {selected['category']}，可以考慮 {selected['name']}。"
    )


def get_default_shelf_life(ingredient):
    short_life_keywords = ["白飯", "青菜", "生菜", "豆腐", "牛奶", "雞肉", "豬肉", "雞胸肉", "絞肉"]
    medium_life_keywords = ["番茄", "蔥", "香蕉", "蘋果", "菇", "高麗菜"]
    long_life_keywords = ["雞蛋", "泡麵", "義大利麵", "醬油", "鹽", "咖哩塊", "燕麥"]
    if any(keyword in ingredient for keyword in short_life_keywords):
        return 3
    if any(keyword in ingredient for keyword in medium_life_keywords):
        return 7
    if any(keyword in ingredient for keyword in long_life_keywords):
        return 14
    return 7


def get_default_price(ingredient):
    high_price_keywords = ["雞肉", "豬肉", "雞胸肉", "鮪魚", "絞肉"]
    low_price_keywords = ["蔥", "鹽", "醬油", "白飯", "雞蛋"]
    if any(keyword in ingredient for keyword in high_price_keywords):
        return 120
    if any(keyword in ingredient for keyword in low_price_keywords):
        return 35
    return 60


def get_default_perishability(ingredient):
    high_keywords = ["白飯", "青菜", "生菜", "豆腐", "牛奶", "雞肉", "豬肉", "雞胸肉", "絞肉"]
    low_keywords = ["泡麵", "義大利麵", "醬油", "鹽", "咖哩塊", "燕麥"]
    if any(keyword in ingredient for keyword in high_keywords):
        return "高"
    if any(keyword in ingredient for keyword in low_keywords):
        return "低"
    return "中"


def calculate_ingredient_priority(days_stored, shelf_life, price, perishability):
    shelf_life = max(int(shelf_life), 1)
    days_stored = max(int(days_stored), 0)
    price = max(float(price), 0)
    remaining_days = max(shelf_life - days_stored, 0)
    used_ratio = min(days_stored / shelf_life, 1)

    expiry_score = used_ratio * 45
    if remaining_days == 0:
        expiry_score += 30
    elif remaining_days == 1:
        expiry_score += 22
    elif remaining_days == 2:
        expiry_score += 14

    price_score = min(price / 150, 1) * 20
    perishability_score = {"低": 5, "中": 10, "高": 15}.get(perishability, 10)
    priority_score = round(min(expiry_score + price_score + perishability_score, 100), 1)

    penalty = price * {"低": 0.8, "中": 1.0, "高": 1.25}.get(perishability, 1.0)
    scheduling_ratio = round(penalty / (remaining_days + 1), 2)

    if priority_score >= 75:
        level = "高"
    elif priority_score >= 45:
        level = "中"
    else:
        level = "低"

    return priority_score, scheduling_ratio, remaining_days, level


def render_ingredient_priority_inputs(ingredients):
    profiles = {}
    if not ingredients:
        return profiles

    with st.sidebar.expander("食材保存資訊", expanded=False):
        st.caption("用保存天數、期限、價格與易腐程度計算食材使用優先級。")
        for ingredient in ingredients:
            st.markdown(f"**{ingredient}**")
            days_stored = st.number_input(
                "已放天數",
                min_value=0,
                max_value=30,
                value=min(1, get_default_shelf_life(ingredient)),
                step=1,
                key=f"stored_days_{ingredient}",
            )
            shelf_life = st.number_input(
                "保存期限（天）",
                min_value=1,
                max_value=60,
                value=get_default_shelf_life(ingredient),
                step=1,
                key=f"shelf_life_{ingredient}",
            )
            price = st.number_input(
                "估計價格（元）",
                min_value=0,
                max_value=500,
                value=get_default_price(ingredient),
                step=5,
                key=f"ingredient_price_{ingredient}",
            )
            perishability = st.selectbox(
                "易腐程度",
                ["低", "中", "高"],
                index=["低", "中", "高"].index(get_default_perishability(ingredient)),
                key=f"perishability_{ingredient}",
            )
            priority_score, scheduling_ratio, remaining_days, level = calculate_ingredient_priority(
                days_stored, shelf_life, price, perishability
            )
            profiles[ingredient] = {
                "days_stored": days_stored,
                "shelf_life": shelf_life,
                "price": price,
                "perishability": perishability,
                "priority_score": priority_score,
                "scheduling_ratio": scheduling_ratio,
                "remaining_days": remaining_days,
                "level": level,
            }
            st.divider()
    return profiles


def apply_ingredient_priority_to_recipes(result, priority_profiles):
    if result.empty or not priority_profiles:
        result = result.copy()
        result["priority_bonus"] = 0
        result["final_score"] = result["score"]
        result["priority_ingredients"] = ""
        return result

    result = result.copy()
    priority_bonuses = []
    final_scores = []
    priority_ingredients_list = []

    for _, row in result.iterrows():
        matched = parse_ingredients(row["matched_ingredients"])
        used_priority = [ingredient for ingredient in matched if ingredient in priority_profiles]
        priority_total = sum(priority_profiles[ingredient]["priority_score"] for ingredient in used_priority)
        high_priority_count = sum(1 for ingredient in used_priority if priority_profiles[ingredient]["level"] == "高")
        priority_bonus = min(priority_total / 8 + high_priority_count * 5, 25)
        priority_bonuses.append(round(priority_bonus, 1))
        final_scores.append(round(min(row["score"] + priority_bonus, 125), 1))
        priority_ingredients_list.append("、".join(used_priority))

    result["priority_bonus"] = priority_bonuses
    result["final_score"] = final_scores
    result["priority_ingredients"] = priority_ingredients_list
    return result.sort_values(by=["final_score", "priority_bonus", "score"], ascending=[False, False, False])


def render_ingredient_priority_summary(priority_profiles):
    if not priority_profiles:
        return

    rows = []
    for ingredient, profile in sorted(
        priority_profiles.items(),
        key=lambda item: (-item[1]["priority_score"], -item[1]["scheduling_ratio"], item[0]),
    ):
        rows.append(
            {
                "食材": ingredient,
                "優先級": profile["level"],
                "優先分數": profile["priority_score"],
                "剩餘天數": profile["remaining_days"],
                "價格": f"{profile['price']} 元",
                "排序比值": profile["scheduling_ratio"],
            }
        )

    with st.expander("食材使用優先級排序", expanded=True):
        st.caption("排序比值概念參考鞋匠排程問題：浪費成本越高、剩餘時間越短，越應該優先處理。")
        st.dataframe(rows, hide_index=True, use_container_width=True)
        top_items = [row["食材"] for row in rows if row["優先級"] == "高"] or [rows[0]["食材"]]
        st.info(f"今日建議優先使用：{'、'.join(top_items[:3])}")


def build_recipe_fortune(result, ingredient_text):
    if result.empty:
        return None
    ingredients = sorted(parse_ingredients(ingredient_text))
    seed_text = "".join(ingredients) or "內食"
    selected = result.iloc[get_daily_index(seed_text, len(result))]
    if selected["missing_count"] == 0:
        hint = "現有食材已經夠用，今天可以直接開煮。"
    elif selected["missing_count"] <= 1:
        hint = "只差一點材料，補一樣就能做出完整料理。"
    else:
        hint = "可以先用現有食材做變化版，不一定要完全照食譜。"
    return f"今日內食籤：{hint} 幸運料理是 {selected['name']}，預估 {selected['time']} 分鐘完成。"


def render_daily_fortune(message):
    if message:
        st.success(message)


def render_tags(tags):
    if tags:
        tag_html = "".join(f'<span class="tag-pill">{html.escape(str(tag))}</span>' for tag in tags)
        st.markdown(f'<div class="tag-row">{tag_html}</div>', unsafe_allow_html=True)


def render_ranked_title(rank, name):
    st.markdown(
        f'<h3><span class="rank-chip">{rank}</span>{html.escape(str(name))}</h3>',
        unsafe_allow_html=True,
    )


def render_reason(reason):
    st.markdown(
        f'<div class="reason-box">推薦理由：{html.escape(str(reason))}</div>',
        unsafe_allow_html=True,
    )


def get_restaurant_tags(row):
    tags = []
    if row["cp_score"] >= 85:
        tags.append("高 CP")
    elif row["cp_score"] >= 70:
        tags.append("中高 CP")
    if row["distance"] <= 5:
        tags.append("近距離")
    if row["serve_speed"] == "快":
        tags.append("快速出餐")
    if row["price"] <= 100:
        tags.append("省錢友善")
    if row["rating"] >= 4.3:
        tags.append("評分高")
    if row["spicy_level"] == 0:
        tags.append("不辣")
    if row["takeout"] == "yes":
        tags.append("可外帶")
    return tags[:5]


def get_recipe_tags(row):
    tags = []
    if row["time"] <= 15:
        tags.append("快速料理")
    if row["missing_count"] == 0:
        tags.append("食材足夠")
    elif row["missing_count"] <= 1:
        tags.append("少買食材")
    if row["calories"] <= 350:
        tags.append("低熱量")
    if row["difficulty"] == "簡單":
        tags.append("新手友善")
    if row["matched_count"] >= 3:
        tags.append("食材符合高")
    return tags[:5]


def render_restaurant_card(rank, row):
    with st.container(border=True):
        title_col, action_col, score_col = st.columns([3.5, 1, 1])
        with title_col:
            render_ranked_title(rank, row["name"])
        if row["name"] in st.session_state.favorite_restaurants:
            action_col.button("已收藏", key=f"restaurant_fav_{rank}_{row['name']}", disabled=True)
        elif action_col.button("收藏", key=f"restaurant_fav_{rank}_{row['name']}"):
            add_favorite("restaurant", row["name"])
            st.rerun()
        score_col.metric("推薦分數", f"{row['score']}")
        render_tags(get_restaurant_tags(row))

        info_col1, info_col2, info_col3, info_col4 = st.columns(4)
        info_col1.write(f"類型：{row['category']}")
        info_col1.write(f"平均價格：{row['price']} 元")
        info_col2.write(f"評分：{row['rating']}")
        info_col2.write(f"距離：{row['distance']} 分鐘")
        info_col3.write(f"出餐速度：{row['serve_speed']}")
        info_col3.write(f"辣度：{row['spicy_level']} / 5")
        info_col4.write(f"CP 值：{row['cp_score']}")
        info_col4.write(f"外帶：{row['takeout']}")
        render_reason(row["reason"])


def get_cp_marker_color(cp_score, rank):
    if rank == 1:
        return "red"
    if cp_score >= 85:
        return "green"
    if cp_score >= 70:
        return "orange"
    return "blue"


def render_restaurant_map(result):
    st.subheader("推薦餐廳地圖")
    map_data = result.dropna(subset=["latitude", "longitude"])
    if map_data.empty:
        st.info("目前餐廳資料尚未包含座標，無法顯示地圖。")
        return

    st.caption("圖針顏色：紅色＝本次第一名｜綠色＝高 CP 值｜橘色＝中高 CP 值｜藍色＝一般推薦")
    center = [map_data["latitude"].mean(), map_data["longitude"].mean()]
    restaurant_map = folium.Map(location=center, zoom_start=16, control_scale=True)

    for rank, (_, row) in enumerate(map_data.iterrows(), start=1):
        cp_score = float(row["cp_score"])
        popup_html = f"""
        <b>{rank}. {html.escape(str(row['name']))}</b><br>
        類型：{html.escape(str(row['category']))}<br>
        平均價格：{row['price']} 元<br>
        評分：{row['rating']}<br>
        距離：{row['distance']} 分鐘<br>
        推薦分數：{row['score']}<br>
        CP值：{cp_score:.2f}<br>
        推薦理由：{html.escape(str(row['reason']))}
        """
        marker_color = get_cp_marker_color(cp_score, rank)
        folium.Marker(
            location=[row["latitude"], row["longitude"]],
            tooltip=f"{rank}. {row['name']}｜推薦 {row['score']} 分｜CP {cp_score:.1f}",
            popup=folium.Popup(popup_html, max_width=320),
            icon=folium.Icon(color=marker_color, icon="cutlery", prefix="fa"),
        ).add_to(restaurant_map)

    st_folium(restaurant_map, use_container_width=True, height=500)


def render_restaurant_highlights(result):
    if result.empty:
        return
    best_cp = result.sort_values(by=["cp_score", "score"], ascending=[False, False]).iloc[0]
    nearest = result.sort_values(by=["distance", "score"], ascending=[True, False]).iloc[0]
    best_rating = result.sort_values(by=["rating", "score"], ascending=[False, False]).iloc[0]
    st.info(
        f"本次推薦重點：最高 CP 值是 {best_cp['name']}（CP {best_cp['cp_score']}）；"
        f"最近的是 {nearest['name']}（{nearest['distance']} 分鐘）；"
        f"最高評分是 {best_rating['name']}（{best_rating['rating']} 分）。"
    )


def render_recipe_highlights(result):
    if result.empty:
        return
    score_column = "final_score" if "final_score" in result.columns else "score"
    fastest = result.sort_values(by=["time", score_column], ascending=[True, False]).iloc[0]
    best_match = result.sort_values(by=["missing_count", "matched_count", score_column], ascending=[True, False, False]).iloc[0]
    lowest_calorie = result.sort_values(by=["calories", score_column], ascending=[True, False]).iloc[0]
    st.info(
        f"本次推薦重點：最快可完成的是 {fastest['name']}（{fastest['time']} 分鐘）；"
        f"食材最接近的是 {best_match['name']}（缺少 {best_match['missing_count']} 項）；"
        f"熱量最低的是 {lowest_calorie['name']}（{lowest_calorie['calories']} kcal）。"
    )


def render_restaurant_comparison(result):
    if len(result) < 2:
        return

    with st.expander("比較兩個外食選項", expanded=False):
        names = result["name"].tolist()
        left_col, right_col = st.columns(2)
        left_name = left_col.selectbox("選項 A", names, index=0, key="restaurant_compare_left")
        right_name = right_col.selectbox("選項 B", names, index=1, key="restaurant_compare_right")

        left = result[result["name"] == left_name].iloc[0]
        right = result[result["name"] == right_name].iloc[0]
        comparison = {
            "比較項目": ["推薦分數", "平均價格", "距離", "評分", "CP 值", "出餐速度", "外帶"],
            left_name: [
                left["score"],
                f"{left['price']} 元",
                f"{left['distance']} 分鐘",
                left["rating"],
                left["cp_score"],
                left["serve_speed"],
                left["takeout"],
            ],
            right_name: [
                right["score"],
                f"{right['price']} 元",
                f"{right['distance']} 分鐘",
                right["rating"],
                right["cp_score"],
                right["serve_speed"],
                right["takeout"],
            ],
        }
        st.dataframe(comparison, hide_index=True, use_container_width=True)

        if left["score"] > right["score"]:
            st.success(f"綜合分數較推薦：{left_name}")
        elif right["score"] > left["score"]:
            st.success(f"綜合分數較推薦：{right_name}")
        else:
            st.info("兩個選項綜合分數相同，可以改看距離、價格或 CP 值。")


def render_recipe_comparison(result):
    if len(result) < 2:
        return

    with st.expander("比較兩個內食選項", expanded=False):
        names = result["name"].tolist()
        left_col, right_col = st.columns(2)
        left_name = left_col.selectbox("選項 A", names, index=0, key="recipe_compare_left")
        right_name = right_col.selectbox("選項 B", names, index=1, key="recipe_compare_right")

        left = result[result["name"] == left_name].iloc[0]
        right = result[result["name"] == right_name].iloc[0]
        comparison = {
            "比較項目": ["推薦分數", "料理時間", "熱量", "難度", "符合食材數", "缺少食材數", "缺少食材"],
            left_name: [
                left.get("final_score", left["score"]),
                f"{left['time']} 分鐘",
                f"{left['calories']} kcal",
                left["difficulty"],
                left["matched_count"],
                left["missing_count"],
                left["missing_ingredients"] or "無",
            ],
            right_name: [
                right.get("final_score", right["score"]),
                f"{right['time']} 分鐘",
                f"{right['calories']} kcal",
                right["difficulty"],
                right["matched_count"],
                right["missing_count"],
                right["missing_ingredients"] or "無",
            ],
        }
        st.dataframe(comparison, hide_index=True, use_container_width=True)

        if left["missing_count"] < right["missing_count"]:
            st.success(f"食材準備較容易：{left_name}")
        elif right["missing_count"] < left["missing_count"]:
            st.success(f"食材準備較容易：{right_name}")
        elif left["time"] < right["time"]:
            st.success(f"時間較快：{left_name}")
        elif right["time"] < left["time"]:
            st.success(f"時間較快：{right_name}")
        else:
            st.info("兩個選項條件接近，可以依照今天想吃的口味決定。")


def render_shopping_list(result):
    if result.empty:
        return

    missing_counts = {}
    for value in result["missing_ingredients"]:
        for ingredient in parse_ingredients(value):
            missing_counts[ingredient] = missing_counts.get(ingredient, 0) + 1

    with st.expander("缺少食材購物清單", expanded=False):
        if not missing_counts:
            st.success("目前推薦食譜都不缺食材，可以直接開始料理。")
            return

        shopping_rows = [
            {"缺少食材": ingredient, "出現次數": count}
            for ingredient, count in sorted(missing_counts.items(), key=lambda item: (-item[1], item[0]))
        ]
        st.caption("依照目前推薦結果統計，出現次數越高，代表越常是推薦食譜會用到但你目前沒有的食材。")
        st.dataframe(shopping_rows, hide_index=True, use_container_width=True)

        names = result["name"].tolist()
        selected_name = st.selectbox("查看單一道食譜需要補買什麼", names, key="shopping_recipe_select")
        selected = result[result["name"] == selected_name].iloc[0]
        missing_items = sorted(parse_ingredients(selected["missing_ingredients"]))
        if missing_items:
            st.write("、".join(missing_items))
        else:
            st.success(f"{selected_name} 目前不需要補買食材。")


def render_recipe_card(rank, row):
    with st.container(border=True):
        title_col, action_col, score_col = st.columns([3.5, 1, 1])
        with title_col:
            render_ranked_title(rank, row["name"])
        if row["name"] in st.session_state.favorite_recipes:
            action_col.button("已收藏", key=f"recipe_fav_{rank}_{row['name']}", disabled=True)
        elif action_col.button("收藏", key=f"recipe_fav_{rank}_{row['name']}"):
            add_favorite("recipe", row["name"])
            st.rerun()
        score_col.metric("推薦分數", f"{row['final_score']}")
        if row.get("priority_bonus", 0) > 0:
            score_col.caption(f"含食材優先加權 +{row['priority_bonus']}")
        render_tags(get_recipe_tags(row))

        info_col1, info_col2, info_col3, info_col4 = st.columns(4)
        info_col1.write(f"類型：{row['category']}")
        info_col1.write(f"料理時間：{row['time']} 分鐘")
        info_col2.write(f"難度：{row['difficulty']}")
        info_col2.write(f"熱量：{row['calories']} kcal")
        info_col3.write(f"符合食材：{row['matched_ingredients'] or '無'}")
        info_col3.write(f"缺少食材：{row['missing_ingredients'] or '無'}")
        info_col4.write(f"符合數：{row['matched_count']}")
        info_col4.write(f"缺少數：{row['missing_count']}")
        if row.get("priority_ingredients", ""):
            info_col4.write(f"優先食材：{row['priority_ingredients']}")
        render_reason(row["reason"])


if mode == "我要外食":
    df = load_data("restaurants.csv")

    st.sidebar.header("外食條件")
    st.sidebar.caption("先設定最常用的條件，需要更細再展開進階條件。")

    budget = st.sidebar.slider("預算上限", 50, 300, 150, step=5)
    max_distance = st.sidebar.slider("可接受距離（分鐘）", 1, 20, 10)
    category_list = ["不限"] + sorted(df["category"].unique().tolist())
    category = st.sidebar.selectbox("餐點類型", category_list)
    mood = st.sidebar.selectbox("目前心情", ["省錢", "疲累", "開心", "心情不好", "選擇困難"])

    with st.sidebar.expander("進階條件", expanded=False):
        weather = st.selectbox("目前天氣", ["普通", "熱", "冷", "雨天"])
        need_takeout = st.selectbox("是否需要外帶", ["不限", "yes", "no"])
        max_spicy_level = st.slider("可接受辣度", 0, 5, 2)
        prefer_fast = st.checkbox("希望快速出餐")
        sort_by = st.selectbox("排序方式", ["綜合推薦", "CP值優先", "距離最近", "評分最高"])
        min_rating = st.slider("最低評分", 0.0, 5.0, 0.0, step=0.1)
        top_n = st.slider("顯示推薦筆數", 3, 10, 5)

    result = recommend_restaurants(
        df,
        budget,
        max_distance,
        category,
        weather,
        mood,
        need_takeout,
        max_spicy_level,
        prefer_fast,
        top_n,
        sort_by,
        min_rating,
    )

    render_section_kicker("外食推薦")
    st.markdown(
        '<div class="soft-note">系統會綜合預算、距離、心情、天氣、評分與 CP 值，產生今天最適合的外食選項。</div>',
        unsafe_allow_html=True,
    )

    if st.session_state.restaurant_decision is not None:
        current_names = set(result["name"].tolist())
        if st.session_state.restaurant_decision["name"] not in current_names:
            st.session_state.restaurant_decision = None

    st.info(f"目前情緒策略：{get_mood_strategy(mood)}")
    st.caption(f"排序方式：{sort_by}｜最低評分：{min_rating:.1f}｜顯示 {top_n} 筆")

    decision_col, clear_decision_col, _ = st.columns([1.2, 1.2, 3])
    if decision_col.button("幫我決定", disabled=result.empty, help="從目前推薦結果中隨機選一間"):
        pick = result.sample(1).iloc[0]
        st.session_state.restaurant_decision = {
            "name": pick["name"],
            "score": pick["score"],
            "reason": pick["reason"],
        }
    if clear_decision_col.button("清除決定", disabled=st.session_state.restaurant_decision is None):
        st.session_state.restaurant_decision = None
    if st.session_state.restaurant_decision is not None:
        pick = st.session_state.restaurant_decision
        st.success(f"本次幫你決定：{pick['name']}｜推薦分數 {pick['score']}｜{pick['reason']}")

    if mood == "選擇困難" and not result.empty:
        surprise = result.sample(1, random_state=int(result["score"].sum() * 10)).iloc[0]
        st.success(f"今日驚喜推薦：{surprise['name']}｜推薦分數 {surprise['score']}｜{surprise['reason']}")


    summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)
    summary_col1.metric("本次推薦筆數", len(result))
    if result.empty:
        summary_col2.metric("平均價格", "--")
        summary_col3.metric("平均距離", "--")
        summary_col4.metric("最高推薦分數", "--")
    else:
        summary_col2.metric("平均價格", f"{result['price'].mean():.0f} 元")
        summary_col3.metric("平均距離", f"{result['distance'].mean():.1f} 分鐘")
        summary_col4.metric("最高推薦分數", f"{result['score'].max():.1f}")

    render_restaurant_highlights(result)
    render_daily_fortune(build_restaurant_fortune(result, mood))
    render_restaurant_comparison(result)

    st.divider()
    render_section_kicker("推薦清單")
    st.subheader(f"外食推薦前 {top_n} 名")
    if result.empty:
        st.warning("目前條件太嚴格，沒有找到符合的餐廳。可以降低最低評分、放寬距離或調整餐點類型。")
    for rank, (_, row) in enumerate(result.iterrows(), start=1):
        render_restaurant_card(rank, row)

    st.divider()
    render_restaurant_map(result)

    with st.expander("查看完整餐廳資料表", expanded=False):
        st.dataframe(df, use_container_width=True)

else:
    recipes = load_recipes("recipes.csv")

    st.sidebar.header("內食條件")
    st.sidebar.caption("選擇冰箱食材，再用進階條件調整時間、熱量與難度。")

    ingredient_options = collect_ingredient_options(recipes)
    selected_ingredients = st.sidebar.multiselect(
        "冰箱常見食材",
        ingredient_options,
        default=[item for item in ["雞蛋", "白飯", "蔥"] if item in ingredient_options],
    )
    custom_ingredients = st.sidebar.text_area(
        "其他食材",
        value="",
        help="可用逗號、頓號或空白分隔，例如：豆腐, 番茄",
    )
    ingredient_text = ",".join(selected_ingredients + [custom_ingredients])
    current_ingredients = sorted(parse_ingredients(ingredient_text))
    priority_profiles = render_ingredient_priority_inputs(current_ingredients)

    with st.sidebar.expander("進階條件", expanded=False):
        max_time = st.slider("可接受烹飪時間（分鐘）", 5, 60, 20, step=5)
        difficulty_preference = st.selectbox("料理難度", ["不限", "簡單", "中等", "困難"])
        max_calories = st.slider("熱量上限（kcal）", 150, 900, 650, step=50)
        max_missing = st.slider("最多可缺少食材數", 0, 5, 2)
        only_cookable = st.checkbox("只顯示現有食材足夠的食譜")
        top_n = st.slider("顯示推薦筆數", 3, 10, 5)

    candidate_result = recommend_recipes(
        recipes,
        ingredient_text,
        max_time,
        difficulty_preference,
        len(recipes),
        max_calories,
        max_missing,
        only_cookable,
    )
    result = apply_ingredient_priority_to_recipes(candidate_result, priority_profiles).head(top_n)

    if st.session_state.recipe_decision is not None:
        current_recipe_names = set(result["name"].tolist())
        if st.session_state.recipe_decision["name"] not in current_recipe_names:
            st.session_state.recipe_decision = None

    render_section_kicker("內食推薦")
    st.markdown(
        '<div class="soft-note">系統會依照冰箱食材、料理時間、熱量與食材保存狀態，優先推薦更適合先做的食譜。</div>',
        unsafe_allow_html=True,
    )

    summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)
    summary_col1.metric("本次推薦筆數", len(result))
    if result.empty:
        summary_col2.metric("平均時間", "--")
        summary_col3.metric("平均熱量", "--")
        summary_col4.metric("最高分數", "--")
    else:
        summary_col2.metric("平均時間", f"{result['time'].mean():.0f} 分鐘")
        summary_col3.metric("平均熱量", f"{result['calories'].mean():.0f} kcal")
        summary_col4.metric("最高分數", f"{result['final_score'].max():.1f}")

    render_ingredient_priority_summary(priority_profiles)

    st.divider()
    decision_col, clear_decision_col, _ = st.columns([1.2, 1.2, 3])
    if decision_col.button("幫我決定", disabled=result.empty, help="從目前推薦食譜中隨機選一道"):
        pick = result.sample(1).iloc[0]
        st.session_state.recipe_decision = {
            "name": pick["name"],
            "score": pick["final_score"],
            "reason": pick["reason"],
        }
    if clear_decision_col.button("清除決定", disabled=st.session_state.recipe_decision is None):
        st.session_state.recipe_decision = None
    if st.session_state.recipe_decision is not None:
        pick = st.session_state.recipe_decision
        st.success(f"本次幫你決定：{pick['name']}｜推薦分數 {pick['score']}｜{pick['reason']}")

    render_recipe_highlights(result)
    render_daily_fortune(build_recipe_fortune(result, ingredient_text))
    render_recipe_comparison(result)
    render_shopping_list(result)

    render_section_kicker("推薦清單")
    st.subheader(f"內食食譜推薦前 {top_n} 名")
    display_ingredients = "、".join(sorted(parse_ingredients(ingredient_text))) or "尚未輸入"
    st.caption(f"目前食材：{display_ingredients}")

    if result.empty:
        st.warning("目前條件太嚴格，沒有找到符合的食譜。可以提高熱量上限、增加可缺少食材數，或取消只顯示現有食材足夠。")
    for rank, (_, row) in enumerate(result.iterrows(), start=1):
        render_recipe_card(rank, row)

    with st.expander("查看完整食譜資料表", expanded=False):
        st.dataframe(recipes, use_container_width=True)
