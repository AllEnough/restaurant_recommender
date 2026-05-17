import streamlit as st

from recommender import load_data, recommend_restaurants
from recipe_recommender import load_recipes, recommend_recipes

st.set_page_config(page_title="今天吃什麼", layout="wide")

st.title("今天吃什麼：餐廳與食譜智慧推薦系統")
st.caption("外食族可依照條件推薦餐廳，內食族可輸入冰箱食材推薦食譜。")

mode = st.sidebar.radio("選擇使用情境", ["外食推薦", "內食推薦"])

if mode == "外食推薦":
    df = load_data("restaurants.csv")

    st.sidebar.header("外食需求")
    budget = st.sidebar.slider("預算上限", 50, 300, 150, step=5)
    max_distance = st.sidebar.slider("可接受距離（分鐘）", 1, 20, 10)

    category_list = ["不限"] + sorted(df["category"].unique().tolist())
    category = st.sidebar.selectbox("餐點類型", category_list)

    weather = st.sidebar.selectbox("目前天氣", ["普通", "熱", "冷", "雨天"])
    mood = st.sidebar.selectbox("目前心情", ["省錢", "疲累", "開心", "心情不好"])
    need_takeout = st.sidebar.selectbox("是否需要外帶", ["不限", "yes", "no"])
    max_spicy_level = st.sidebar.slider("可接受辣度", 0, 5, 2)
    prefer_fast = st.sidebar.checkbox("希望快速出餐")
    top_n = st.sidebar.slider("顯示推薦筆數", 3, 10, 5)

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
    )

    summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)
    summary_col1.metric("餐廳資料筆數", len(df))
    summary_col2.metric("平均價格", f"{df['price'].mean():.0f} 元")
    summary_col3.metric("平均評分", f"{df['rating'].mean():.2f}")
    summary_col4.metric("餐點類型", df["category"].nunique())

    st.divider()
    st.subheader(f"外食推薦前 {top_n} 名")

    for rank, (_, row) in enumerate(result.iterrows(), start=1):
        with st.container(border=True):
            st.markdown(f"### {rank}. {row['name']}")
            col1, col2, col3, col4 = st.columns(4)
            col1.write(f"類型：{row['category']}")
            col1.write(f"平均價格：{row['price']} 元")
            col2.write(f"評分：{row['rating']}")
            col2.write(f"距離：{row['distance']} 分鐘")
            col3.write(f"出餐速度：{row['serve_speed']}")
            col3.write(f"辣度：{row['spicy_level']} / 5")
            col4.metric("推薦分數", f"{row['score']}")
            st.write(f"推薦理由：{row['reason']}")

    st.divider()
    st.subheader("外食推薦結果視覺化")
    st.bar_chart(result.set_index("name")["score"])

    st.subheader("餐廳資料分析")
    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.write("各類型餐廳數量")
        st.bar_chart(df["category"].value_counts())
    with chart_col2:
        st.write("各類型平均價格")
        avg_price = df.groupby("category")["price"].mean().sort_values(ascending=False)
        st.bar_chart(avg_price)

    st.subheader("完整餐廳資料表")
    st.dataframe(df, use_container_width=True)

else:
    recipes = load_recipes("recipes.csv")

    st.sidebar.header("內食需求")
    ingredient_text = st.sidebar.text_area(
        "冰箱現有食材",
        value="雞蛋, 白飯, 蔥",
        help="可用逗號、頓號或空白分隔，例如：雞蛋, 白飯, 蔥",
    )
    max_time = st.sidebar.slider("可接受烹飪時間（分鐘）", 5, 60, 20, step=5)
    difficulty_preference = st.sidebar.selectbox("料理難度", ["不限", "簡單", "中等", "困難"])
    top_n = st.sidebar.slider("顯示推薦筆數", 3, 10, 5)

    result = recommend_recipes(recipes, ingredient_text, max_time, difficulty_preference, top_n)

    summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)
    summary_col1.metric("食譜資料筆數", len(recipes))
    summary_col2.metric("平均時間", f"{recipes['time'].mean():.0f} 分鐘")
    summary_col3.metric("平均熱量", f"{recipes['calories'].mean():.0f} kcal")
    summary_col4.metric("食譜類型", recipes["category"].nunique())

    st.divider()
    st.subheader(f"內食食譜推薦前 {top_n} 名")

    for rank, (_, row) in enumerate(result.iterrows(), start=1):
        with st.container(border=True):
            st.markdown(f"### {rank}. {row['name']}")
            col1, col2, col3, col4 = st.columns(4)
            col1.write(f"類型：{row['category']}")
            col1.write(f"料理時間：{row['time']} 分鐘")
            col2.write(f"難度：{row['difficulty']}")
            col2.write(f"熱量：{row['calories']} kcal")
            col3.write(f"符合食材：{row['matched_ingredients'] or '無'}")
            col3.write(f"缺少食材：{row['missing_ingredients'] or '無'}")
            col4.metric("推薦分數", f"{row['score']}")
            st.write(f"推薦理由：{row['reason']}")

    st.divider()
    st.subheader("食譜推薦結果視覺化")
    st.bar_chart(result.set_index("name")["score"])

    st.subheader("食譜資料分析")
    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.write("各類型食譜數量")
        st.bar_chart(recipes["category"].value_counts())
    with chart_col2:
        st.write("各類型平均烹飪時間")
        avg_time = recipes.groupby("category")["time"].mean().sort_values(ascending=False)
        st.bar_chart(avg_time)

    st.subheader("完整食譜資料表")
    st.dataframe(recipes, use_container_width=True)
