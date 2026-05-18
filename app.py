import hashlib
import html
from datetime import date

import folium
import streamlit as st
from streamlit_folium import st_folium

from recommender import get_mood_strategy, load_data, recommend_restaurants
from recipe_recommender import collect_ingredient_options, load_recipes, parse_ingredients, recommend_recipes

st.set_page_config(page_title="今天吃什麼", layout="wide")

st.title("今天吃什麼：餐廳與食譜智慧推薦系統")
st.caption("先選擇今天的用餐情境，系統會依照條件產生推薦結果與推薦理由。")

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


def render_restaurant_card(rank, row):
    with st.container(border=True):
        title_col, action_col, score_col = st.columns([3.5, 1, 1])
        title_col.markdown(f"### {rank}. {row['name']}")
        if row["name"] in st.session_state.favorite_restaurants:
            action_col.button("已收藏", key=f"restaurant_fav_{rank}_{row['name']}", disabled=True)
        elif action_col.button("收藏", key=f"restaurant_fav_{rank}_{row['name']}"):
            add_favorite("restaurant", row["name"])
            st.rerun()
        score_col.metric("推薦分數", f"{row['score']}")

        info_col1, info_col2, info_col3, info_col4 = st.columns(4)
        info_col1.write(f"類型：{row['category']}")
        info_col1.write(f"平均價格：{row['price']} 元")
        info_col2.write(f"評分：{row['rating']}")
        info_col2.write(f"距離：{row['distance']} 分鐘")
        info_col3.write(f"出餐速度：{row['serve_speed']}")
        info_col3.write(f"辣度：{row['spicy_level']} / 5")
        info_col4.write(f"CP 值：{row['cp_score']}")
        info_col4.write(f"外帶：{row['takeout']}")
        st.write(f"推薦理由：{row['reason']}")


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
    fastest = result.sort_values(by=["time", "score"], ascending=[True, False]).iloc[0]
    best_match = result.sort_values(by=["missing_count", "matched_count", "score"], ascending=[True, False, False]).iloc[0]
    lowest_calorie = result.sort_values(by=["calories", "score"], ascending=[True, False]).iloc[0]
    st.info(
        f"本次推薦重點：最快可完成的是 {fastest['name']}（{fastest['time']} 分鐘）；"
        f"食材最接近的是 {best_match['name']}（缺少 {best_match['missing_count']} 項）；"
        f"熱量最低的是 {lowest_calorie['name']}（{lowest_calorie['calories']} kcal）。"
    )


def render_recipe_card(rank, row):
    with st.container(border=True):
        title_col, action_col, score_col = st.columns([3.5, 1, 1])
        title_col.markdown(f"### {rank}. {row['name']}")
        if row["name"] in st.session_state.favorite_recipes:
            action_col.button("已收藏", key=f"recipe_fav_{rank}_{row['name']}", disabled=True)
        elif action_col.button("收藏", key=f"recipe_fav_{rank}_{row['name']}"):
            add_favorite("recipe", row["name"])
            st.rerun()
        score_col.metric("推薦分數", f"{row['score']}")

        info_col1, info_col2, info_col3, info_col4 = st.columns(4)
        info_col1.write(f"類型：{row['category']}")
        info_col1.write(f"料理時間：{row['time']} 分鐘")
        info_col2.write(f"難度：{row['difficulty']}")
        info_col2.write(f"熱量：{row['calories']} kcal")
        info_col3.write(f"符合食材：{row['matched_ingredients'] or '無'}")
        info_col3.write(f"缺少食材：{row['missing_ingredients'] or '無'}")
        info_col4.write(f"符合數：{row['matched_count']}")
        info_col4.write(f"缺少數：{row['missing_count']}")
        st.write(f"推薦理由：{row['reason']}")


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

    st.divider()
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

    with st.sidebar.expander("進階條件", expanded=False):
        max_time = st.slider("可接受烹飪時間（分鐘）", 5, 60, 20, step=5)
        difficulty_preference = st.selectbox("料理難度", ["不限", "簡單", "中等", "困難"])
        max_calories = st.slider("熱量上限（kcal）", 150, 900, 650, step=50)
        max_missing = st.slider("最多可缺少食材數", 0, 5, 2)
        only_cookable = st.checkbox("只顯示現有食材足夠的食譜")
        top_n = st.slider("顯示推薦筆數", 3, 10, 5)

    result = recommend_recipes(
        recipes,
        ingredient_text,
        max_time,
        difficulty_preference,
        top_n,
        max_calories,
        max_missing,
        only_cookable,
    )

    if st.session_state.recipe_decision is not None:
        current_recipe_names = set(result["name"].tolist())
        if st.session_state.recipe_decision["name"] not in current_recipe_names:
            st.session_state.recipe_decision = None

    summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)
    summary_col1.metric("本次推薦筆數", len(result))
    if result.empty:
        summary_col2.metric("平均時間", "--")
        summary_col3.metric("平均熱量", "--")
        summary_col4.metric("最高推薦分數", "--")
    else:
        summary_col2.metric("平均時間", f"{result['time'].mean():.0f} 分鐘")
        summary_col3.metric("平均熱量", f"{result['calories'].mean():.0f} kcal")
        summary_col4.metric("最高推薦分數", f"{result['score'].max():.1f}")

    st.divider()
    decision_col, clear_decision_col, _ = st.columns([1.2, 1.2, 3])
    if decision_col.button("幫我決定", disabled=result.empty, help="從目前推薦食譜中隨機選一道"):
        pick = result.sample(1).iloc[0]
        st.session_state.recipe_decision = {
            "name": pick["name"],
            "score": pick["score"],
            "reason": pick["reason"],
        }
    if clear_decision_col.button("清除決定", disabled=st.session_state.recipe_decision is None):
        st.session_state.recipe_decision = None
    if st.session_state.recipe_decision is not None:
        pick = st.session_state.recipe_decision
        st.success(f"本次幫你決定：{pick['name']}｜推薦分數 {pick['score']}｜{pick['reason']}")

    render_recipe_highlights(result)
    render_daily_fortune(build_recipe_fortune(result, ingredient_text))

    st.subheader(f"內食食譜推薦前 {top_n} 名")
    display_ingredients = "、".join(sorted(parse_ingredients(ingredient_text))) or "尚未輸入"
    st.caption(f"目前食材：{display_ingredients}")

    if result.empty:
        st.warning("目前條件太嚴格，沒有找到符合的食譜。可以提高熱量上限、增加可缺少食材數，或取消只顯示現有食材足夠。")
    for rank, (_, row) in enumerate(result.iterrows(), start=1):
        render_recipe_card(rank, row)

    with st.expander("查看完整食譜資料表", expanded=False):
        st.dataframe(recipes, use_container_width=True)
