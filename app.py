import hashlib
import html
import math
from datetime import date, datetime
from zoneinfo import ZoneInfo

import folium
import streamlit as st
from streamlit_folium import st_folium

try:
    from streamlit_js_eval import get_geolocation
except ImportError:
    get_geolocation = None

from recommender import (
    calculate_score_breakdown,
    get_meal_time_strategy,
    get_mood_strategy,
    load_data,
    recommend_restaurants,
)
from recipe_recommender import collect_ingredient_options, load_recipes, parse_ingredients, recommend_recipes
from review_analyzer import analyze_reviews, load_reviews, merge_review_analysis
from weather_service import fetch_current_weather

st.set_page_config(page_title="智慧飲食決策系統", layout="wide")

def inject_design_system():
    st.markdown(
        """
        <style>
        :root {
            --bg: #f7f7f4;
            --surface: #ffffff;
            --surface-soft: #fbfaf6;
            --paper: #ffffff;
            --paper-strong: #ffffff;
            --ink: #1f2933;
            --muted: #687076;
            --line: #e7e2d8;
            --primary: #e4572e;
            --primary-dark: #b83219;
            --green: #276749;
            --green-soft: #eaf6ef;
            --red-soft: #fff1e8;
            --yellow-soft: #fff7d6;
            --shadow: 0 14px 34px rgba(31, 41, 51, 0.08);
            --shadow-soft: 0 8px 18px rgba(31, 41, 51, 0.06);
        }

        .stApp {
            background: var(--bg);
            color: var(--ink);
        }

        header[data-testid="stHeader"] {
            background: rgba(247, 247, 244, 0.86);
            border-bottom: 1px solid rgba(231, 226, 216, 0.78);
            backdrop-filter: blur(14px);
        }

        [data-testid="stDecoration"] {
            display: none;
        }

        section[data-testid="stSidebar"] {
            background: #f0eee8;
            border-right: 1px solid var(--line);
            box-shadow: none;
        }

        section[data-testid="stSidebar"] > div {
            padding-top: 1.3rem;
        }

        section[data-testid="stSidebar"] *,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span {
            color: var(--ink);
        }

        .block-container {
            padding-top: 1rem;
            padding-bottom: 4rem;
            max-width: 1180px;
        }

        h1, h2, h3 {
            color: var(--ink);
            letter-spacing: 0;
        }

        div[data-testid="stMetric"] {
            background: var(--paper-strong);
            border: 1px solid var(--line);
            border-radius: 12px;
            padding: 1rem 1.1rem;
            box-shadow: var(--shadow-soft);
        }

        div[data-testid="stMetric"] label,
        div[data-testid="stMetricLabel"] {
            color: var(--muted);
            font-size: 0.88rem;
        }

        div[data-testid="stMetricValue"] {
            color: var(--ink);
            font-weight: 800;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            border: 1px solid var(--line);
            border-radius: 14px;
            background: var(--paper-strong);
            box-shadow: var(--shadow-soft);
        }

        div[data-testid="stAlert"] {
            border-radius: 14px;
            border: 1px solid var(--line);
            box-shadow: none;
        }

        .stButton > button {
            border-radius: 10px;
            border: 1px solid #f4b49b;
            background: #fff7f2 !important;
            color: var(--primary-dark) !important;
            font-weight: 700;
            padding: 0.48rem 0.95rem;
            transition: all 0.15s ease;
        }

        .stButton > button:hover {
            border-color: var(--primary);
            background: #ffede5 !important;
            color: var(--primary-dark) !important;
            box-shadow: 0 8px 16px rgba(228, 87, 46, 0.12);
        }

        button[data-testid="stBaseButton-secondary"] {
            border-radius: 10px !important;
            border: 1px solid #f4b49b !important;
            background: #fff7f2 !important;
            color: var(--primary-dark) !important;
            font-weight: 800 !important;
        }

        button[data-testid="stBaseButton-secondary"]:hover {
            background: #ffede5 !important;
            color: var(--primary-dark) !important;
            border-color: var(--primary) !important;
            box-shadow: 0 8px 16px rgba(228, 87, 46, 0.12) !important;
        }

        .stButton > button:disabled {
            background: #eee7dd !important;
            color: #a89c90 !important;
            border-color: #e4d8ca;
            box-shadow: none;
        }

        button[data-testid="stBaseButton-secondary"]:disabled {
            background: #eee7dd !important;
            color: #a89c90 !important;
            border-color: #e4d8ca !important;
            box-shadow: none !important;
        }

        div[data-testid="stRadio"] {
            background: var(--paper-strong);
            border: 1px solid var(--line);
            border-radius: 14px;
            padding: 0.8rem 1rem;
            box-shadow: var(--shadow-soft);
        }

        div[data-testid="stRadio"] label,
        div[data-testid="stRadio"] p,
        div[data-testid="stRadio"] span {
            color: var(--ink) !important;
        }

        div[data-testid="stSlider"] [role="slider"] {
            background-color: var(--primary);
            border-color: var(--primary);
        }

        div[data-baseweb="select"] > div {
            background: #ffffff !important;
            border-radius: 10px !important;
            border-color: var(--line) !important;
            color: var(--ink) !important;
        }

        div[data-baseweb="select"] span,
        div[data-baseweb="select"] div {
            color: var(--ink) !important;
        }

        textarea,
        input {
            background: #ffffff !important;
            border-radius: 10px !important;
            border-color: var(--line) !important;
            color: var(--ink) !important;
        }

        textarea::placeholder,
        input::placeholder {
            color: #aa9b8d !important;
        }

        details {
            border-radius: 12px !important;
            border: 1px solid var(--line) !important;
            background: var(--paper-strong) !important;
            box-shadow: none !important;
            overflow: hidden;
        }

        details summary {
            background: #fbfaf6 !important;
            color: var(--ink) !important;
            border-bottom: 1px solid var(--line);
        }

        details summary *,
        div[data-testid="stExpander"] *,
        div[data-testid="stExpander"] p,
        div[data-testid="stExpander"] span {
            color: var(--ink) !important;
        }

        hr {
            margin: 1.6rem 0;
            border-color: var(--line);
        }

        .app-hero {
            position: relative;
            overflow: hidden;
            display: grid;
            grid-template-columns: minmax(0, 1.25fr) minmax(300px, 0.75fr);
            gap: 1.2rem;
            align-items: stretch;
            border-radius: 18px;
            padding: 1.25rem;
            margin-bottom: 1rem;
            background: #ffffff;
            border: 1px solid var(--line);
            color: var(--ink);
            box-shadow: var(--shadow);
        }

        .app-hero::before {
            content: "";
            position: absolute;
            inset: 0;
            border-top: 5px solid var(--primary);
            pointer-events: none;
        }

        .app-hero__content {
            position: relative;
            z-index: 1;
            padding: 0.55rem 0.4rem 0.35rem;
        }

        .app-hero__eyebrow {
            display: inline-flex;
            align-items: center;
            padding: 0.3rem 0.66rem;
            border-radius: 999px;
            background: var(--green-soft);
            border: 1px solid #c7e8d2;
            color: var(--green);
            font-size: 0.78rem;
            font-weight: 800;
        }

        .app-hero h1 {
            color: var(--ink);
            margin: 0.75rem 0 0.45rem;
            font-size: clamp(2rem, 3.7vw, 3.25rem);
            line-height: 1.06;
            font-weight: 900;
        }

        .app-hero p {
            max-width: 44rem;
            margin: 0;
            color: var(--muted);
            font-size: 1rem;
            line-height: 1.7;
        }

        .app-hero__panel {
            position: relative;
            z-index: 1;
            display: grid;
            gap: 0.7rem;
            padding: 0.85rem;
            border-radius: 14px;
            background: #f8f5ef;
            border: 1px solid var(--line);
        }

        .hero-stat {
            display: grid;
            grid-template-columns: 2.15rem minmax(0, 1fr);
            gap: 0.65rem;
            align-items: center;
            padding: 0.72rem;
            border-radius: 12px;
            background: #ffffff;
            border: 1px solid #ebe6dc;
        }

        .hero-stat__icon {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 2.15rem;
            height: 2.15rem;
            border-radius: 10px;
            background: #fff0e9;
            color: var(--primary-dark);
            font-weight: 900;
        }

        .hero-stat__title {
            color: var(--ink);
            font-size: 0.92rem;
            font-weight: 900;
            margin-bottom: 0.12rem;
        }

        .hero-stat__text {
            color: var(--muted);
            font-size: 0.8rem;
            line-height: 1.45;
        }

        .hero-meta {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-top: 1rem;
        }

        .hero-chip {
            display: inline-flex;
            align-items: center;
            padding: 0.38rem 0.68rem;
            border-radius: 999px;
            background: #fbfaf6;
            border: 1px solid var(--line);
            color: #46515a;
            font-size: 0.82rem;
            font-weight: 800;
        }

        .app-nav {
            position: sticky;
            top: 3.6rem;
            z-index: 50;
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
            align-items: center;
            margin: 0 0 1rem;
            padding: 0.52rem;
            border: 1px solid var(--line);
            border-radius: 14px;
            background: rgba(255, 255, 255, 0.92);
            backdrop-filter: blur(10px);
            box-shadow: var(--shadow-soft);
        }

        .app-nav a,
        .side-nav a {
            text-decoration: none !important;
        }

        .app-nav__label {
            color: var(--muted);
            font-size: 0.82rem;
            font-weight: 800;
            padding: 0.32rem 0.45rem;
        }

        .app-nav__link {
            display: inline-flex;
            align-items: center;
            min-height: 2rem;
            padding: 0.42rem 0.7rem;
            border: 1px solid transparent;
            border-radius: 999px;
            color: var(--ink) !important;
            font-size: 0.86rem;
            font-weight: 800;
            transition: all 0.15s ease;
        }

        .app-nav__link:hover {
            border-color: #ffd1bf;
            background: #fff1eb;
            color: var(--primary-dark) !important;
        }

        .side-nav {
            margin: 0.25rem 0 1rem;
            padding: 0.75rem;
            border: 1px solid var(--line);
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.64);
        }

        .side-nav__title {
            margin-bottom: 0.5rem;
            color: var(--muted);
            font-size: 0.78rem;
            font-weight: 900;
        }

        .side-nav__link {
            display: block;
            padding: 0.48rem 0.55rem;
            border-radius: 10px;
            color: var(--ink) !important;
            font-size: 0.9rem;
            font-weight: 800;
        }

        .side-nav__link:hover {
            background: #fff1eb;
            color: var(--primary-dark) !important;
        }

        .section-anchor {
            scroll-margin-top: 7.2rem;
            height: 0;
        }

        .section-kicker {
            display: inline-flex;
            align-items: center;
            padding: 0.32rem 0.64rem;
            border-radius: 999px;
            background: var(--green-soft);
            color: var(--green);
            font-size: 0.82rem;
            font-weight: 800;
            margin: 0.4rem 0 0.6rem;
        }

        .soft-note {
            border: 1px solid var(--line);
            border-radius: 12px;
            background: var(--paper-strong);
            padding: 1rem 1.1rem;
            color: var(--muted);
            margin-bottom: 1rem;
        }

        .demo-flow {
            border: 1px solid #cfe2d9;
            border-radius: 16px;
            background: linear-gradient(135deg, #f4fbf7 0%, #ffffff 62%);
            padding: 1rem;
            margin: 0.75rem 0 1rem;
        }

        .demo-flow__header {
            display: flex;
            justify-content: space-between;
            gap: 1rem;
            align-items: flex-start;
            margin-bottom: 0.8rem;
        }

        .demo-flow__title {
            color: var(--ink);
            font-weight: 900;
            font-size: 1.05rem;
        }

        .demo-flow__case {
            color: var(--green);
            font-size: 0.86rem;
            font-weight: 900;
            text-align: right;
        }

        .demo-steps {
            display: grid;
            grid-template-columns: repeat(5, minmax(0, 1fr));
            gap: 0.6rem;
        }

        .demo-step {
            border: 1px solid var(--line);
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.78);
            padding: 0.78rem;
        }

        .demo-step__number {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 1.65rem;
            height: 1.65rem;
            border-radius: 8px;
            background: var(--green);
            color: #ffffff;
            font-size: 0.78rem;
            font-weight: 900;
            margin-bottom: 0.48rem;
        }

        .demo-step__title {
            color: var(--ink);
            font-size: 0.88rem;
            font-weight: 900;
            margin-bottom: 0.25rem;
        }

        .demo-step__text {
            color: var(--muted);
            font-size: 0.78rem;
            line-height: 1.5;
        }

        .decision-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.75rem;
            margin: 0.8rem 0 1rem;
        }

        .decision-tile {
            border: 1px solid var(--line);
            border-radius: 12px;
            background: #ffffff;
            padding: 0.9rem 1rem;
        }

        .decision-tile__label {
            color: var(--muted);
            font-size: 0.78rem;
            font-weight: 900;
            margin-bottom: 0.35rem;
        }

        .decision-tile__value {
            color: var(--ink);
            font-size: 0.95rem;
            font-weight: 800;
            line-height: 1.5;
        }

        .nudge-box {
            border: 1px solid #f7c59f;
            border-radius: 12px;
            background: #fff8ef;
            padding: 1rem 1.1rem;
            color: #6b4a2d;
            margin: 0.75rem 0 1rem;
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
            background: #fff1eb;
            color: var(--primary-dark);
            font-size: 0.82rem;
            font-weight: 700;
            border: 1px solid #ffd1bf;
        }

        .rank-chip {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-width: 2rem;
            height: 2rem;
            border-radius: 10px;
            background: var(--primary);
            color: #ffffff;
            font-weight: 900;
            margin-right: 0.55rem;
        }

        .reason-box {
            border-radius: 10px;
            padding: 0.8rem 0.95rem;
            background: #fbfaf6;
            border: 1px solid var(--line);
            color: #46515a;
            line-height: 1.65;
        }

        .review-table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            overflow: hidden;
            border: 1px solid var(--line);
            border-radius: 12px;
            background: var(--paper-strong);
            font-size: 0.9rem;
        }

        .review-table th {
            background: #fbfaf6;
            color: var(--ink);
            text-align: left;
            padding: 0.7rem 0.75rem;
            border-bottom: 1px solid var(--line);
            font-weight: 900;
        }

        .review-table td {
            padding: 0.68rem 0.75rem;
            border-bottom: 1px solid #f1e8dc;
            color: #4f4037;
            vertical-align: top;
        }

        .review-table tr:last-child td {
            border-bottom: 0;
        }

        .explain-grid {
            display: grid;
            grid-template-columns: minmax(0, 1.15fr) minmax(280px, 0.85fr);
            gap: 1rem;
            align-items: start;
        }

        .explain-table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            overflow: hidden;
            border: 1px solid var(--line);
            border-radius: 12px;
            background: var(--paper-strong);
            font-size: 0.9rem;
        }

        .explain-table th {
            background: #fbfaf6;
            color: var(--ink);
            text-align: left;
            padding: 0.68rem 0.72rem;
            border-bottom: 1px solid var(--line);
            font-weight: 900;
        }

        .explain-table td {
            padding: 0.64rem 0.72rem;
            border-bottom: 1px solid #f1e8dc;
            color: #4f4037;
            vertical-align: top;
        }

        .explain-table tr:last-child td {
            border-bottom: 0;
        }

        .score-bars {
            padding: 0.85rem;
            border: 1px solid var(--line);
            border-radius: 12px;
            background: var(--paper-strong);
        }

        .score-bar {
            margin-bottom: 0.75rem;
        }

        .score-bar__label {
            display: flex;
            justify-content: space-between;
            gap: 0.75rem;
            margin-bottom: 0.28rem;
            color: var(--ink);
            font-size: 0.84rem;
            font-weight: 800;
        }

        .score-bar__track {
            height: 0.7rem;
            overflow: hidden;
            border-radius: 999px;
            background: #eee9df;
        }

        .score-bar__fill {
            height: 100%;
            border-radius: 999px;
            background: var(--primary);
        }

        .risk-badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-width: 2.1rem;
            padding: 0.18rem 0.45rem;
            border-radius: 999px;
            background: var(--green-soft);
            color: var(--green);
            font-size: 0.78rem;
            font-weight: 900;
        }

        .risk-badge--mid {
            background: var(--yellow-soft);
            color: #854d0e;
        }

        .risk-badge--high {
            background: #fee2e2;
            color: #991b1b;
        }

        .dashboard-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 1rem;
            margin: 0.85rem 0 1.1rem;
        }

        .insight-panel {
            border: 1px solid var(--line);
            border-radius: 14px;
            background: var(--paper-strong);
            box-shadow: var(--shadow-soft);
            padding: 1rem 1.05rem;
        }

        .insight-panel__title {
            color: var(--ink);
            font-weight: 900;
            margin-bottom: 0.45rem;
        }

        .insight-panel__body {
            color: var(--muted);
            line-height: 1.65;
            font-size: 0.93rem;
        }

        .mini-table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            overflow: hidden;
            border: 1px solid var(--line);
            border-radius: 12px;
            background: var(--paper-strong);
            font-size: 0.9rem;
            margin-top: 0.8rem;
        }

        .mini-table th {
            background: #fbfaf6;
            color: var(--ink);
            text-align: left;
            padding: 0.62rem 0.7rem;
            border-bottom: 1px solid var(--line);
            font-weight: 900;
        }

        .mini-table td {
            padding: 0.6rem 0.7rem;
            border-bottom: 1px solid #f1e8dc;
            color: #4f4037;
            vertical-align: top;
        }

        .mini-table tr:last-child td {
            border-bottom: 0;
        }

        @media (max-width: 768px) {
            .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
            }
            .app-hero {
                grid-template-columns: 1fr;
                border-radius: 16px;
                padding: 1rem;
            }
            .dashboard-grid,
            .explain-grid,
            .decision-grid,
            .demo-steps {
                grid-template-columns: 1fr;
            }
            .demo-flow__header {
                display: block;
            }
            .demo-flow__case {
                text-align: left;
                margin-top: 0.4rem;
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
            <div class="app-hero__content">
                <div class="app-hero__eyebrow">外食避雷 × 內食減浪費</div>
                <h1>智慧飲食決策系統</h1>
                <p>把餐廳評論、距離價格、冰箱食材與保存期限整理成可解釋的飲食建議，讓外食少踩雷、內食少浪費。</p>
                <div class="hero-meta">
                    <span class="hero-chip">外食決策</span>
                    <span class="hero-chip">模型評估</span>
                    <span class="hero-chip">食材優先級</span>
                </div>
            </div>
            <div class="app-hero__panel">
                <div class="hero-stat">
                    <div class="hero-stat__icon">01</div>
                    <div>
                        <div class="hero-stat__title">評論風險分析</div>
                        <div class="hero-stat__text">整理情緒分數、負評比例與常見疑慮。</div>
                    </div>
                </div>
                <div class="hero-stat">
                    <div class="hero-stat__icon">02</div>
                    <div>
                        <div class="hero-stat__title">推薦模型解釋</div>
                        <div class="hero-stat__text">拆解分數來源，比較加入模型前後差異。</div>
                    </div>
                </div>
                <div class="hero-stat">
                    <div class="hero-stat__icon">03</div>
                    <div>
                        <div class="hero-stat__title">食材減浪費決策</div>
                        <div class="hero-stat__text">依保存天數、價格與易腐程度排序。</div>
                    </div>
                </div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_section_kicker(text):
    st.markdown(f'<div class="section-kicker">{html.escape(text)}</div>', unsafe_allow_html=True)


def render_anchor(anchor_id):
    st.markdown(f'<div id="{html.escape(anchor_id)}" class="section-anchor"></div>', unsafe_allow_html=True)


def render_demo_flow(current_mode, case_name, case_description):
    if current_mode == "我要外食":
        steps = [
            ("選情境", "用展示案例快速套用預算、距離、心情與評論門檻。"),
            ("看結論", "先看本次最佳建議、適合族群與關鍵取捨。"),
            ("驗模型", "展開模型評估，觀察評論分析前後排名差異。"),
            ("做回饋", "對餐廳按喜歡或不喜歡，展示偏好學習。"),
            ("看地圖", "用互動式圖針呈現空間位置與 CP 值。"),
        ]
    else:
        steps = [
            ("選情境", "用展示案例套用冰箱食材、料理時間與熱量限制。"),
            ("看結論", "先看本次最佳食譜、適合族群與第二名比較。"),
            ("看食材", "檢查保存優先級，說明如何減少食材浪費。"),
            ("做回饋", "對食譜按喜歡或不喜歡，展示偏好學習。"),
            ("看購物", "查看缺少食材清單，說明內食決策如何落地。"),
        ]

    step_html = "".join(
        "<div class='demo-step'>"
        f"<div class='demo-step__number'>{index:02d}</div>"
        f"<div class='demo-step__title'>{html.escape(title)}</div>"
        f"<div class='demo-step__text'>{html.escape(text)}</div>"
        "</div>"
        for index, (title, text) in enumerate(steps, start=1)
    )
    st.markdown(
        "<section class='demo-flow'>"
        "<div class='demo-flow__header'>"
        "<div>"
        "<div class='demo-flow__title'>專題展示流程</div>"
        "<div class='demo-step__text'>照這個順序展示，老師能快速看到系統的資料處理、推薦模型、可解釋性與互動回饋。</div>"
        "</div>"
        f"<div class='demo-flow__case'>目前案例：{html.escape(case_name)}<br>{html.escape(case_description)}</div>"
        "</div>"
        f"<div class='demo-steps'>{step_html}</div>"
        "</section>",
        unsafe_allow_html=True,
    )


def get_nav_items(current_mode):
    if current_mode == "我要外食":
        return [
            ("展示流程", "demo"),
            ("推薦概覽", "overview"),
            ("決策儀表板", "dashboard"),
            ("模型評估", "evaluation"),
            ("評論分析", "reviews"),
            ("模型解釋", "model"),
            ("重點摘要", "summary"),
            ("推薦清單", "list"),
            ("美食地圖", "map"),
            ("資料表", "data"),
        ]
    return [
        ("展示流程", "demo"),
        ("推薦概覽", "overview"),
        ("決策儀表板", "dashboard"),
        ("模型評估", "evaluation"),
        ("食材優先級", "priority"),
        ("推薦操作", "actions"),
        ("食譜清單", "list"),
        ("資料表", "data"),
    ]


def render_page_nav(current_mode):
    links = "".join(
        (
            f'<a class="app-nav__link" href="#{anchor_id}" '
            f'onclick="document.getElementById(&quot;{anchor_id}&quot;)?.scrollIntoView({{behavior:&quot;smooth&quot;,block:&quot;start&quot;}})">'
            f'{html.escape(label)}</a>'
        )
        for label, anchor_id in get_nav_items(current_mode)
    )
    st.markdown(
        f'<nav class="app-nav"><span class="app-nav__label">快速導覽</span>{links}</nav>',
        unsafe_allow_html=True,
    )


def render_sidebar_nav(current_mode):
    links = "".join(
        (
            f'<a class="side-nav__link" href="#{anchor_id}" '
            f'onclick="document.getElementById(&quot;{anchor_id}&quot;)?.scrollIntoView({{behavior:&quot;smooth&quot;,block:&quot;start&quot;}})">'
            f'{html.escape(label)}</a>'
        )
        for label, anchor_id in get_nav_items(current_mode)
    )
    st.sidebar.markdown(
        f'<div class="side-nav"><div class="side-nav__title">快速導覽</div>{links}</div>',
        unsafe_allow_html=True,
    )


inject_design_system()
render_page_header()

mode = st.radio(
    "今天想怎麼吃？",
    ["我要外食", "我要自己煮"],
    horizontal=True,
    label_visibility="visible",
)
render_page_nav(mode)

if "favorite_restaurants" not in st.session_state:
    st.session_state.favorite_restaurants = []
if "favorite_recipes" not in st.session_state:
    st.session_state.favorite_recipes = []
if "restaurant_decision" not in st.session_state:
    st.session_state.restaurant_decision = None
if "recipe_decision" not in st.session_state:
    st.session_state.recipe_decision = None
if "restaurant_feedback" not in st.session_state:
    st.session_state.restaurant_feedback = {"liked": [], "disliked": []}
if "recipe_feedback" not in st.session_state:
    st.session_state.recipe_feedback = {"liked": [], "disliked": []}


render_sidebar_nav(mode)


def add_favorite(kind, name):
    key = "favorite_restaurants" if kind == "restaurant" else "favorite_recipes"
    if name not in st.session_state[key]:
        st.session_state[key].append(name)


def record_feedback(kind, name, preference):
    feedback_key = "restaurant_feedback" if kind == "restaurant" else "recipe_feedback"
    target_key = "liked" if preference == "like" else "disliked"
    opposite_key = "disliked" if preference == "like" else "liked"
    if name not in st.session_state[feedback_key][target_key]:
        st.session_state[feedback_key][target_key].append(name)
    if name in st.session_state[feedback_key][opposite_key]:
        st.session_state[feedback_key][opposite_key].remove(name)


def clear_feedback(kind=None):
    if kind in (None, "restaurant"):
        st.session_state.restaurant_feedback = {"liked": [], "disliked": []}
    if kind in (None, "recipe"):
        st.session_state.recipe_feedback = {"liked": [], "disliked": []}


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
        liked_restaurants = st.session_state.restaurant_feedback["liked"]
        disliked_restaurants = st.session_state.restaurant_feedback["disliked"]
        liked_recipes = st.session_state.recipe_feedback["liked"]
        disliked_recipes = st.session_state.recipe_feedback["disliked"]
        if liked_restaurants or disliked_restaurants or liked_recipes or disliked_recipes:
            st.divider()
            st.write("偏好學習")
            if liked_restaurants:
                st.caption(f"喜歡餐廳：{'、'.join(liked_restaurants[:4])}")
            if disliked_restaurants:
                st.caption(f"不喜歡餐廳：{'、'.join(disliked_restaurants[:4])}")
            if liked_recipes:
                st.caption(f"喜歡食譜：{'、'.join(liked_recipes[:4])}")
            if disliked_recipes:
                st.caption(f"不喜歡食譜：{'、'.join(disliked_recipes[:4])}")
            if st.button("清除偏好學習"):
                clear_feedback()
                st.rerun()


render_favorites()


@st.cache_data(ttl=900, show_spinner=False)
def get_cached_weather(location):
    return fetch_current_weather(location)


def detect_meal_time(current_time=None):
    now = current_time or datetime.now(ZoneInfo("Asia/Taipei"))
    minutes = now.hour * 60 + now.minute
    if 5 * 60 <= minutes < 10 * 60 + 30:
        return "早餐"
    if 10 * 60 + 30 <= minutes < 14 * 60:
        return "午餐"
    if 14 * 60 <= minutes < 17 * 60:
        return "下午茶"
    if 17 * 60 <= minutes < 21 * 60:
        return "晚餐"
    return "宵夜"


LOCATION_PRESETS = {
    "逢甲大學": {"latitude": 24.1790, "longitude": 120.6466},
    "逢甲夜市": {"latitude": 24.1778, "longitude": 120.6458},
    "文華路商圈": {"latitude": 24.1769, "longitude": 120.6450},
    "西屯路口": {"latitude": 24.1760, "longitude": 120.6480},
}


def haversine_distance_meters(lat1, lon1, lat2, lon2):
    earth_radius = 6371000
    phi1 = math.radians(float(lat1))
    phi2 = math.radians(float(lat2))
    delta_phi = math.radians(float(lat2) - float(lat1))
    delta_lambda = math.radians(float(lon2) - float(lon1))
    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    return earth_radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def normalize_browser_location(raw_location):
    if not raw_location:
        return None
    coords = raw_location.get("coords", raw_location)
    try:
        latitude = float(coords["latitude"])
        longitude = float(coords["longitude"])
    except (KeyError, TypeError, ValueError):
        return None
    return {
        "latitude": latitude,
        "longitude": longitude,
        "accuracy": coords.get("accuracy"),
        "source": "瀏覽器定位",
    }


def apply_user_location_to_restaurants(restaurants, user_location):
    if not user_location:
        return restaurants.copy()

    results = restaurants.copy()
    if "original_distance" not in results.columns:
        results["original_distance"] = results["distance"]

    distances = []
    walking_minutes = []
    for _, row in results.iterrows():
        distance_m = haversine_distance_meters(
            user_location["latitude"],
            user_location["longitude"],
            row["latitude"],
            row["longitude"],
        )
        distances.append(round(distance_m))
        walking_minutes.append(max(1, round(distance_m / 80)))

    results["distance_meters"] = distances
    results["distance"] = walking_minutes
    return results


def format_takeout(value):
    mapping = {
        "yes": "可外帶",
        "no": "不支援外帶",
        "不限": "不限",
    }
    return mapping.get(str(value), str(value))


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


def apply_review_adjustment(result, use_review_analysis, review_weight):
    result = result.copy()
    if not use_review_analysis or result.empty:
        result["final_score"] = result["score"]
        return result

    weight_ratio = review_weight / 100
    result["final_score"] = (result["score"] + result["review_adjustment"] * weight_ratio).clip(0, 110).round(1)
    return result.sort_values(
        by=["final_score", "sentiment_score", "score", "rating"],
        ascending=[False, False, False, False],
    )


def apply_restaurant_intent_adjustment(result, intent_name):
    result = result.copy()
    if result.empty:
        result["intent_adjustment"] = 0
        return result

    adjustments = []
    for _, row in result.iterrows():
        adjustment = 0
        if intent_name in ("省錢外食", "大學生省錢午餐"):
            adjustment += min(float(row.get("cp_score", 0)) / 10, 10)
            adjustment += max(0, (140 - float(row["price"])) / 20)
            if row["category"] in ["便當", "飯類", "麵食", "水餃", "鍋貼", "素食"]:
                adjustment += 3
            if row["category"] in ["飲料", "甜點", "早餐"]:
                adjustment -= 8
        elif intent_name in ("快速午餐", "疲累近距離", "上班族快速外帶"):
            adjustment += max(0, (10 - float(row["distance"])) * 1.6)
            if row["serve_speed"] == "快":
                adjustment += 7
            elif row["serve_speed"] == "中":
                adjustment += 3
            if row["takeout"] == "yes":
                adjustment += 5
            if row["category"] in ["便當", "飯類", "麵食", "水餃", "鍋貼", "輕食"]:
                adjustment += 3
            if row["category"] in ["飲料", "甜點", "早餐"]:
                adjustment -= 8
        elif intent_name in ("不想踩雷", "老師聚餐不踩雷"):
            adjustment += max(0, (float(row["rating"]) - 4.0) * 10)
            adjustment += max(0, (40 - float(row.get("negative_ratio", 40))) / 4)
            adjustment += max(0, (float(row.get("sentiment_score", 60)) - 60) / 8)
            if row.get("review_risk") == "低":
                adjustment += 5
            elif row.get("review_risk") == "高":
                adjustment -= 8
            if row["category"] in ["日式", "義式", "火鍋", "鐵板燒", "美式", "韓式", "泰式", "港式"]:
                adjustment += 4
        adjustments.append(round(max(min(adjustment, 18), -12), 1))

    score_column = "final_score" if "final_score" in result.columns else "score"
    result["intent_adjustment"] = adjustments
    result["final_score"] = (result[score_column] + result["intent_adjustment"]).clip(0, 135).round(1)
    return result.sort_values(
        by=["final_score", "intent_adjustment", "score", "rating"],
        ascending=[False, False, False, False],
    )


def price_bucket(price):
    if price <= 100:
        return "低價"
    if price <= 180:
        return "中價"
    return "高價"


def time_bucket(minutes):
    if minutes <= 15:
        return "快速"
    if minutes <= 30:
        return "一般"
    return "較久"


def calorie_bucket(calories):
    if calories <= 450:
        return "低熱量"
    if calories <= 650:
        return "中熱量"
    return "高熱量"


def build_restaurant_preference_profile(all_restaurants):
    feedback = st.session_state.restaurant_feedback
    if not feedback["liked"] and not feedback["disliked"]:
        return {}

    profile = {}

    def add_weight(feature, weight):
        profile[feature] = profile.get(feature, 0) + weight

    for preference, names in (("liked", feedback["liked"]), ("disliked", feedback["disliked"])):
        weight = 1 if preference == "liked" else -1
        matches = all_restaurants[all_restaurants["name"].isin(names)]
        for _, row in matches.iterrows():
            add_weight(("category", row["category"]), weight * 5)
            add_weight(("price_bucket", price_bucket(row["price"])), weight * 3)
            add_weight(("serve_speed", row["serve_speed"]), weight * 2)
            add_weight(("takeout", row["takeout"]), weight * 1.5)
            add_weight(("spicy_level", min(int(row["spicy_level"]), 3)), weight * 1)
            if "review_risk" in row:
                add_weight(("review_risk", row["review_risk"]), weight * 2)
    return profile


def apply_restaurant_preference_learning(result, all_restaurants):
    result = result.copy()
    profile = build_restaurant_preference_profile(all_restaurants)
    if result.empty or not profile:
        result["preference_adjustment"] = 0
        return result

    adjustments = []
    for _, row in result.iterrows():
        adjustment = 0
        adjustment += profile.get(("category", row["category"]), 0)
        adjustment += profile.get(("price_bucket", price_bucket(row["price"])), 0)
        adjustment += profile.get(("serve_speed", row["serve_speed"]), 0)
        adjustment += profile.get(("takeout", row["takeout"]), 0)
        adjustment += profile.get(("spicy_level", min(int(row["spicy_level"]), 3)), 0)
        adjustment += profile.get(("review_risk", row.get("review_risk", "未知")), 0)
        adjustments.append(round(max(min(adjustment, 12), -12), 1))

    score_column = "final_score" if "final_score" in result.columns else "score"
    result["preference_adjustment"] = adjustments
    result["final_score"] = (result[score_column] + result["preference_adjustment"]).clip(0, 125).round(1)
    sort_columns = ["final_score", "preference_adjustment", "score", "rating"]
    return result.sort_values(by=sort_columns, ascending=[False, False, False, False])


def build_recipe_preference_profile(all_recipes):
    feedback = st.session_state.recipe_feedback
    if not feedback["liked"] and not feedback["disliked"]:
        return {}

    profile = {}

    def add_weight(feature, weight):
        profile[feature] = profile.get(feature, 0) + weight

    for preference, names in (("liked", feedback["liked"]), ("disliked", feedback["disliked"])):
        weight = 1 if preference == "liked" else -1
        matches = all_recipes[all_recipes["name"].isin(names)]
        for _, row in matches.iterrows():
            add_weight(("category", row["category"]), weight * 5)
            add_weight(("difficulty", row["difficulty"]), weight * 2)
            add_weight(("time_bucket", time_bucket(row["time"])), weight * 3)
            add_weight(("calorie_bucket", calorie_bucket(row["calories"])), weight * 2)
            for ingredient in parse_ingredients(row.get("ingredients", "")):
                add_weight(("ingredient", ingredient), weight * 1.5)
    return profile


def apply_recipe_preference_learning(result, all_recipes):
    result = result.copy()
    profile = build_recipe_preference_profile(all_recipes)
    if result.empty or not profile:
        result["preference_adjustment"] = 0
        return result

    adjustments = []
    for _, row in result.iterrows():
        adjustment = 0
        adjustment += profile.get(("category", row["category"]), 0)
        adjustment += profile.get(("difficulty", row["difficulty"]), 0)
        adjustment += profile.get(("time_bucket", time_bucket(row["time"])), 0)
        adjustment += profile.get(("calorie_bucket", calorie_bucket(row["calories"])), 0)
        for ingredient in parse_ingredients(row.get("ingredients", "")):
            adjustment += profile.get(("ingredient", ingredient), 0)
        adjustments.append(round(max(min(adjustment, 12), -12), 1))

    score_column = "final_score" if "final_score" in result.columns else "score"
    result["preference_adjustment"] = adjustments
    result["final_score"] = (result[score_column] + result["preference_adjustment"]).clip(0, 140).round(1)
    return result.sort_values(by=["final_score", "preference_adjustment", "score"], ascending=[False, False, False])


def summarize_preference_profile(profile):
    if not profile:
        return "尚未累積偏好。對推薦卡片按喜歡或不喜歡後，系統會自動調整相似項目的分數。"
    strongest = sorted(profile.items(), key=lambda item: abs(item[1]), reverse=True)[:4]
    pieces = []
    for (kind, value), weight in strongest:
        direction = "偏好" if weight > 0 else "避開"
        pieces.append(f"{direction}{value}")
    return "、".join(pieces)


def render_preference_learning_summary(kind, source_data):
    if kind == "restaurant":
        feedback = st.session_state.restaurant_feedback
        profile = build_restaurant_preference_profile(source_data)
        title = "外食偏好學習"
    else:
        feedback = st.session_state.recipe_feedback
        profile = build_recipe_preference_profile(source_data)
        title = "內食偏好學習"

    liked_count = len(feedback["liked"])
    disliked_count = len(feedback["disliked"])
    with st.expander(title, expanded=bool(liked_count or disliked_count)):
        st.caption("使用者按喜歡或不喜歡後，系統會把回饋轉成輕量化偏好權重，影響本次 session 後續排序。")
        col1, col2, col3 = st.columns(3)
        col1.metric("喜歡", liked_count)
        col2.metric("不喜歡", disliked_count)
        col3.metric("偏好特徵數", len(profile))
        st.write(summarize_preference_profile(profile))
        if liked_count or disliked_count:
            if st.button(f"清除{title}", key=f"clear_{kind}_preference_panel"):
                clear_feedback(kind)
                st.rerun()


def render_review_analysis_panel(result):
    if result.empty or "sentiment_score" not in result.columns:
        return

    review_data = result[result["review_count"] > 0]
    with st.expander("餐廳評論文字分析", expanded=False):
        if review_data.empty:
            st.info("目前推薦結果沒有可分析的評論資料。")
            return

        avg_sentiment = review_data["sentiment_score"].mean()
        avg_negative = review_data["negative_ratio"].mean()
        high_risk_count = int((review_data["review_risk"] == "高").sum())
        stable_count = int((review_data["review_risk"] == "低").sum())

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("平均評論情緒", f"{avg_sentiment:.1f}")
        col2.metric("平均負評比例", f"{avg_negative:.1f}%")
        col3.metric("低風險餐廳", stable_count)
        col4.metric("高風險餐廳", high_risk_count)

        safest = review_data.sort_values(by=["review_risk", "sentiment_score"], ascending=[True, False]).iloc[0]
        risky = review_data.sort_values(by=["negative_ratio", "sentiment_score"], ascending=[False, True]).iloc[0]
        if risky["negative_ratio"] < 10 and high_risk_count == 0:
            st.info(
                f"評論最穩定：{safest['name']}（情緒 {safest['sentiment_score']}，負評 {safest['negative_ratio']}%）；"
                "本次推薦餐廳評論風險皆偏低。"
            )
        else:
            st.info(
                f"評論最穩定：{safest['name']}（情緒 {safest['sentiment_score']}，負評 {safest['negative_ratio']}%）；"
                f"需注意：{risky['name']}（負評 {risky['negative_ratio']}%）。"
            )

        risk_classes = {"高": "risk-badge--high", "中": "risk-badge--mid", "低": ""}
        table_rows = []
        for _, row in review_data.iterrows():
            risk_class = risk_classes.get(row["review_risk"], "")
            table_rows.append(
                "<tr>"
                f"<td>{html.escape(str(row['name']))}</td>"
                f"<td>{int(row['review_count'])}</td>"
                f"<td>{row['sentiment_score']}</td>"
                f"<td>{row['negative_ratio']}%</td>"
                f"<td><span class='risk-badge {risk_class}'>{html.escape(str(row['review_risk']))}</span></td>"
                f"<td>{html.escape(str(row['positive_keywords'] or '無'))}</td>"
                f"<td>{html.escape(str(row['negative_keywords'] or '無'))}</td>"
                f"<td>{html.escape(str(row['review_topics'] or '無'))}</td>"
                "</tr>"
            )

        st.markdown(
            "<table class='review-table'>"
            "<thead><tr>"
            "<th>餐廳</th><th>評論數</th><th>情緒分數</th><th>負評比例</th>"
            "<th>風險</th><th>常見優點</th><th>常見疑慮</th><th>常見主題</th>"
            "</tr></thead>"
            f"<tbody>{''.join(table_rows)}</tbody></table>",
            unsafe_allow_html=True,
        )


def render_restaurant_model_explainer(
    result,
    budget,
    max_distance,
    category,
    weather,
    mood,
    need_takeout,
    max_spicy_level,
    prefer_fast,
    meal_time,
    use_review_analysis,
    review_weight,
):
    if result.empty:
        return

    with st.expander("推薦模型解釋器", expanded=False):
        names = result["name"].tolist()
        selected_name = st.selectbox("選擇要解釋的餐廳", names, key="restaurant_model_explainer")
        selected = result[result["name"] == selected_name].iloc[0]
        components, base_total = calculate_score_breakdown(
            selected,
            budget,
            max_distance,
            category,
            weather,
            mood,
            need_takeout,
            max_spicy_level,
            prefer_fast,
            meal_time,
        )

        rows = [
            {"分數來源": label, "分數": score, "說明": note}
            for label, score, note in components
        ]
        review_adjustment = selected.get("review_adjustment", 0) * (review_weight / 100 if use_review_analysis else 0)
        if use_review_analysis:
            rows.append(
                {
                    "分數來源": "評論調整",
                    "分數": round(review_adjustment, 2),
                    "說明": f"情緒分數 {selected.get('sentiment_score', 50)}，負評比例 {selected.get('negative_ratio', 0)}%",
                }
            )

        final_score = selected.get("final_score", selected["score"])
        max_score = max([abs(row["分數"]) for row in rows] + [1])
        table_rows = []
        bar_rows = []
        for row in rows:
            source = html.escape(str(row["分數來源"]))
            score = float(row["分數"])
            note = html.escape(str(row["說明"]))
            width = min(abs(score) / max_score * 100, 100)
            table_rows.append(
                f"<tr><td>{source}</td><td>{score:g}</td><td>{note}</td></tr>"
            )
            bar_rows.append(
                "<div class='score-bar'>"
                f"<div class='score-bar__label'><span>{source}</span><span>{score:g}</span></div>"
                f"<div class='score-bar__track'><div class='score-bar__fill' style='width:{width:.1f}%'></div></div>"
                "</div>"
            )

        st.markdown(
            "<div class='explain-grid'>"
            "<table class='explain-table'>"
            "<thead><tr><th>分數來源</th><th>分數</th><th>說明</th></tr></thead>"
            f"<tbody>{''.join(table_rows)}</tbody></table>"
            f"<div class='score-bars'>{''.join(bar_rows)}</div>"
            "</div>",
            unsafe_allow_html=True,
        )

        st.info(
            f"{selected_name} 的基礎分數為 {base_total}，"
            f"評論加權後最終分數為 {final_score}。"
        )


def render_restaurant_sensitivity_analysis(result):
    if result.empty:
        return

    with st.expander("權重敏感度分析", expanded=False):
        scenario_definitions = [
            ("目前排序", "final_score" if "final_score" in result.columns else "score", False),
            ("省錢優先", "cp_score", False),
            ("距離優先", "distance", True),
            ("評分優先", "rating", False),
        ]
        if "sentiment_score" in result.columns:
            scenario_definitions.append(("口碑優先", "sentiment_score", False))
            scenario_definitions.append(("低負評優先", "negative_ratio", True))

        rows = []
        for scenario, column, ascending in scenario_definitions:
            winner = result.sort_values(by=[column], ascending=[ascending]).iloc[0]
            rows.append(
                {
                    "情境": scenario,
                    "第一名": winner["name"],
                    "排序指標": column,
                    "指標值": winner[column],
                    "原推薦分數": winner["score"],
                    "最終分數": winner.get("final_score", winner["score"]),
                }
            )

        table_rows = []
        for row in rows:
            table_rows.append(
                "<tr>"
                f"<td>{html.escape(str(row['情境']))}</td>"
                f"<td>{html.escape(str(row['第一名']))}</td>"
                f"<td>{html.escape(str(row['排序指標']))}</td>"
                f"<td>{row['指標值']}</td>"
                f"<td>{row['原推薦分數']}</td>"
                f"<td>{row['最終分數']}</td>"
                "</tr>"
            )
        st.markdown(
            "<table class='explain-table'>"
            "<thead><tr><th>情境</th><th>第一名</th><th>排序指標</th><th>指標值</th><th>原推薦分數</th><th>最終分數</th></tr></thead>"
            f"<tbody>{''.join(table_rows)}</tbody></table>",
            unsafe_allow_html=True,
        )
        current_winner = rows[0]["第一名"]
        changed = [row for row in rows[1:] if row["第一名"] != current_winner]
        if changed:
            changed_text = "、".join(f"{row['情境']}會改成 {row['第一名']}" for row in changed[:3])
            st.info(f"排名對使用者偏好有敏感度：{changed_text}。")
        else:
            st.success("不同情境下第一名大致穩定，代表目前推薦結果相對穩健。")


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
        st.dataframe(rows, hide_index=True, width="stretch")
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
    if row.get("sentiment_score", 50) >= 75:
        tags.append("評論穩定")
    if row.get("review_risk", "") == "高":
        tags.append("評論風險")
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
        title_col, action_col, feedback_col, score_col = st.columns([3.2, 1, 1.3, 1])
        with title_col:
            render_ranked_title(rank, row["name"])
        if row["name"] in st.session_state.favorite_restaurants:
            action_col.button("已收藏", key=f"restaurant_fav_{rank}_{row['name']}", disabled=True)
        elif action_col.button("收藏", key=f"restaurant_fav_{rank}_{row['name']}"):
            add_favorite("restaurant", row["name"])
            st.rerun()
        liked = row["name"] in st.session_state.restaurant_feedback["liked"]
        disliked = row["name"] in st.session_state.restaurant_feedback["disliked"]
        like_col, dislike_col = feedback_col.columns(2)
        if like_col.button("喜歡", key=f"restaurant_like_{rank}_{row['name']}", disabled=liked):
            record_feedback("restaurant", row["name"], "like")
            st.rerun()
        if dislike_col.button("不喜歡", key=f"restaurant_dislike_{rank}_{row['name']}", disabled=disliked):
            record_feedback("restaurant", row["name"], "dislike")
            st.rerun()
        score_col.metric("推薦分數", f"{row.get('final_score', row['score'])}")
        if row.get("preference_adjustment", 0) != 0:
            score_col.caption(f"偏好調整 {row['preference_adjustment']:+.1f}")
        if row.get("intent_adjustment", 0) != 0:
            score_col.caption(f"情境調整 {row['intent_adjustment']:+.1f}")
        if row.get("review_adjustment", 0) != 0:
            score_col.caption(f"評論調整 {row['review_adjustment']:+.1f}")
        render_tags(get_restaurant_tags(row))

        info_col1, info_col2, info_col3, info_col4 = st.columns(4)
        info_col1.write(f"類型：{row['category']}")
        info_col1.write(f"平均價格：{row['price']} 元")
        info_col2.write(f"評分：{row['rating']}")
        info_col2.write(f"距離：{row['distance']} 分鐘")
        info_col3.write(f"出餐速度：{row['serve_speed']}")
        info_col3.write(f"辣度：{row['spicy_level']} / 5")
        info_col4.write(f"CP 值：{row['cp_score']}")
        info_col4.write(f"外帶：{format_takeout(row['takeout'])}")
        if "sentiment_score" in row:
            info_col4.write(f"評論情緒：{row['sentiment_score']}")
            info_col4.write(f"負評比例：{row['negative_ratio']}%")
        if row.get("review_summary", ""):
            st.caption(f"評論摘要：{row['review_summary']}")
        render_reason(row["reason"])


def get_cp_marker_color(cp_score, rank):
    if rank == 1:
        return "red"
    if cp_score >= 85:
        return "green"
    if cp_score >= 70:
        return "orange"
    return "blue"


def render_restaurant_map(result, user_location=None):
    st.subheader("推薦餐廳地圖")
    map_data = result.dropna(subset=["latitude", "longitude"])
    if map_data.empty:
        st.info("目前餐廳資料尚未包含座標，無法顯示地圖。")
        return

    st.caption("圖針顏色：紅色＝本次第一名｜綠色＝高 CP 值｜橘色＝中高 CP 值｜藍色＝一般推薦")
    if user_location:
        center = [user_location["latitude"], user_location["longitude"]]
    else:
        center = [map_data["latitude"].mean(), map_data["longitude"].mean()]
    restaurant_map = folium.Map(location=center, zoom_start=16, control_scale=True)

    if user_location:
        folium.Marker(
            location=[user_location["latitude"], user_location["longitude"]],
            tooltip=f"目前位置：{user_location['source']}",
            popup=folium.Popup("系統用這個位置重新計算餐廳步行距離。", max_width=260),
            icon=folium.Icon(color="purple", icon="user", prefix="fa"),
        ).add_to(restaurant_map)

    for rank, (_, row) in enumerate(map_data.iterrows(), start=1):
        cp_score = float(row["cp_score"])
        popup_html = f"""
        <b>{rank}. {html.escape(str(row['name']))}</b><br>
        類型：{html.escape(str(row['category']))}<br>
        平均價格：{row['price']} 元<br>
        評分：{row['rating']}<br>
        步行距離：{row['distance']} 分鐘<br>
        直線距離：{row.get('distance_meters', '無資料')} 公尺<br>
        推薦分數：{row['score']}<br>
        CP值：{cp_score:.2f}<br>
        評論情緒：{row.get('sentiment_score', '無資料')}<br>
        負評比例：{row.get('negative_ratio', 0)}%<br>
        推薦理由：{html.escape(str(row['reason']))}
        """
        marker_color = get_cp_marker_color(cp_score, rank)
        folium.Marker(
            location=[row["latitude"], row["longitude"]],
            tooltip=f"{rank}. {row['name']}｜{row['distance']} 分鐘｜推薦 {row['score']} 分",
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
    message = (
        f"本次推薦重點：最高 CP 值是 {best_cp['name']}（CP {best_cp['cp_score']}）；"
        f"最近的是 {nearest['name']}（{nearest['distance']} 分鐘）；"
        f"最高評分是 {best_rating['name']}（{best_rating['rating']} 分）。"
    )
    if "sentiment_score" in result.columns:
        best_review = result.sort_values(by=["sentiment_score", "negative_ratio"], ascending=[False, True]).iloc[0]
        message += f" 評論最穩定的是 {best_review['name']}（情緒 {best_review['sentiment_score']}）。"
    st.info(message)


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
        comparison_rows = [
            {"比較項目": "推薦分數", left_name: str(left["score"]), right_name: str(right["score"])},
            {"比較項目": "平均價格", left_name: f"{left['price']} 元", right_name: f"{right['price']} 元"},
            {"比較項目": "距離", left_name: f"{left['distance']} 分鐘", right_name: f"{right['distance']} 分鐘"},
            {"比較項目": "評分", left_name: str(left["rating"]), right_name: str(right["rating"])},
            {"比較項目": "CP 值", left_name: str(left["cp_score"]), right_name: str(right["cp_score"])},
            {"比較項目": "出餐速度", left_name: str(left["serve_speed"]), right_name: str(right["serve_speed"])},
            {"比較項目": "外帶", left_name: format_takeout(left["takeout"]), right_name: format_takeout(right["takeout"])},
        ]
        st.dataframe(comparison_rows, hide_index=True, width="stretch")

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
        comparison_rows = [
            {"比較項目": "推薦分數", left_name: str(left.get("final_score", left["score"])), right_name: str(right.get("final_score", right["score"]))},
            {"比較項目": "料理時間", left_name: f"{left['time']} 分鐘", right_name: f"{right['time']} 分鐘"},
            {"比較項目": "熱量", left_name: f"{left['calories']} kcal", right_name: f"{right['calories']} kcal"},
            {"比較項目": "難度", left_name: str(left["difficulty"]), right_name: str(right["difficulty"])},
            {"比較項目": "符合食材數", left_name: str(left["matched_count"]), right_name: str(right["matched_count"])},
            {"比較項目": "缺少食材數", left_name: str(left["missing_count"]), right_name: str(right["missing_count"])},
            {"比較項目": "缺少食材", left_name: left["missing_ingredients"] or "無", right_name: right["missing_ingredients"] or "無"},
        ]
        st.dataframe(comparison_rows, hide_index=True, width="stretch")

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
        st.dataframe(shopping_rows, hide_index=True, width="stretch")

        names = result["name"].tolist()
        selected_name = st.selectbox("查看單一道食譜需要補買什麼", names, key="shopping_recipe_select")
        selected = result[result["name"] == selected_name].iloc[0]
        missing_items = sorted(parse_ingredients(selected["missing_ingredients"]))
        if missing_items:
            st.write("、".join(missing_items))
        else:
            st.success(f"{selected_name} 目前不需要補買食材。")


RESTAURANT_SMART_MODES = {
    "自訂": {
        "description": "保留完整控制權，適合想自行調整每個條件。",
        "budget": 150,
        "distance": 10,
        "category": "不限",
        "mood": "省錢",
        "meal_time_mode": "自動判斷",
        "manual_meal_time": "午餐",
        "weather_mode": "自動偵測",
        "need_takeout": "不限",
        "max_spicy_level": 2,
        "prefer_fast": False,
        "sort_by": "綜合推薦",
        "min_rating": 0.0,
        "top_n": 5,
        "use_review_analysis": True,
        "review_weight": 60,
        "max_negative_ratio": 60,
        "hide_high_risk": False,
    },
    "快速午餐": {
        "description": "適合中午時間有限，優先找近、快、可外帶且不要太踩雷的選項。",
        "budget": 150,
        "distance": 8,
        "category": "不限",
        "mood": "疲累",
        "meal_time_mode": "手動選擇",
        "manual_meal_time": "午餐",
        "weather_mode": "自動偵測",
        "need_takeout": "yes",
        "max_spicy_level": 2,
        "prefer_fast": True,
        "sort_by": "距離最近",
        "min_rating": 3.8,
        "top_n": 5,
        "use_review_analysis": True,
        "review_weight": 70,
        "max_negative_ratio": 35,
        "hide_high_risk": True,
    },
    "省錢外食": {
        "description": "適合月底或學生族群，優先提高 CP 值與價格友善度。",
        "budget": 120,
        "distance": 10,
        "category": "不限",
        "mood": "省錢",
        "meal_time_mode": "自動判斷",
        "manual_meal_time": "午餐",
        "weather_mode": "自動偵測",
        "need_takeout": "不限",
        "max_spicy_level": 2,
        "prefer_fast": False,
        "sort_by": "CP值優先",
        "min_rating": 3.5,
        "top_n": 5,
        "use_review_analysis": True,
        "review_weight": 50,
        "max_negative_ratio": 50,
        "hide_high_risk": False,
    },
    "不想踩雷": {
        "description": "適合聚餐、約會或帶老師吃飯，優先避開負評比例高的餐廳。",
        "budget": 220,
        "distance": 12,
        "category": "不限",
        "mood": "選擇困難",
        "meal_time_mode": "自動判斷",
        "manual_meal_time": "晚餐",
        "weather_mode": "自動偵測",
        "need_takeout": "不限",
        "max_spicy_level": 2,
        "prefer_fast": False,
        "sort_by": "評分最高",
        "min_rating": 4.0,
        "top_n": 5,
        "use_review_analysis": True,
        "review_weight": 80,
        "max_negative_ratio": 25,
        "hide_high_risk": True,
    },
    "疲累近距離": {
        "description": "適合下課或下班後不想走太遠，優先近距離與快速出餐。",
        "budget": 160,
        "distance": 6,
        "category": "不限",
        "mood": "疲累",
        "meal_time_mode": "自動判斷",
        "manual_meal_time": "晚餐",
        "weather_mode": "自動偵測",
        "need_takeout": "yes",
        "max_spicy_level": 1,
        "prefer_fast": True,
        "sort_by": "距離最近",
        "min_rating": 3.7,
        "top_n": 5,
        "use_review_analysis": True,
        "review_weight": 60,
        "max_negative_ratio": 45,
        "hide_high_risk": True,
    },
}


RECIPE_SMART_MODES = {
    "自訂": {
        "description": "保留完整控制權，適合想自己決定時間、熱量與缺少食材數。",
        "default_ingredients": ["雞蛋", "白飯", "蔥"],
        "max_time": 20,
        "difficulty": "不限",
        "max_calories": 650,
        "max_missing": 2,
        "only_cookable": False,
        "top_n": 5,
    },
    "我不想出門": {
        "description": "優先推薦冰箱現有食材就能完成的食譜，降低外出採買需求。",
        "default_ingredients": ["雞蛋", "白飯", "蔥"],
        "max_time": 25,
        "difficulty": "不限",
        "max_calories": 700,
        "max_missing": 0,
        "only_cookable": True,
        "top_n": 5,
    },
    "清冰箱模式": {
        "description": "優先使用保存天數較短、應該先消耗的食材，讓系統幫你減少浪費。",
        "default_ingredients": ["雞蛋", "白飯", "蔥", "番茄"],
        "max_time": 40,
        "difficulty": "不限",
        "max_calories": 750,
        "max_missing": 2,
        "only_cookable": False,
        "top_n": 5,
    },
    "快速料理": {
        "description": "適合剛下課、剛下班或懶得煮太久，優先推薦短時間料理。",
        "default_ingredients": ["雞蛋", "白飯", "蔥"],
        "max_time": 15,
        "difficulty": "簡單",
        "max_calories": 650,
        "max_missing": 2,
        "only_cookable": False,
        "top_n": 5,
    },
    "低熱量": {
        "description": "適合想控制熱量的使用者，優先保留較輕盈的食譜選項。",
        "default_ingredients": ["雞蛋", "番茄", "豆腐"],
        "max_time": 30,
        "difficulty": "不限",
        "max_calories": 450,
        "max_missing": 2,
        "only_cookable": False,
        "top_n": 5,
    },
}


RESTAURANT_DEMO_CASES = {
    "手動自訂": {
        "description": "不套用展示情境，保留完整手動控制。",
        "smart_mode": "自訂",
        "overrides": {},
    },
    "大學生省錢午餐": {
        "description": "預算有限、午餐時段、希望快速找到高 CP 值選項。",
        "smart_mode": "省錢外食",
        "overrides": {
            "budget": 120,
            "distance": 10,
            "required_categories": ["便當", "飯類", "麵食", "水餃", "鍋貼", "小吃", "素食"],
            "weather_mode": "手動選擇",
            "meal_time_mode": "手動選擇",
            "manual_meal_time": "午餐",
            "sort_by": "CP值優先",
            "min_rating": 3.5,
            "max_negative_ratio": 50,
        },
    },
    "上班族快速外帶": {
        "description": "時間少、需要外帶、優先近距離和快速出餐。",
        "smart_mode": "快速午餐",
        "overrides": {
            "budget": 160,
            "distance": 7,
            "required_categories": ["便當", "飯類", "麵食", "水餃", "鍋貼", "輕食"],
            "weather_mode": "手動選擇",
            "meal_time_mode": "手動選擇",
            "manual_meal_time": "午餐",
            "need_takeout": "yes",
            "prefer_fast": True,
            "sort_by": "距離最近",
            "max_negative_ratio": 40,
            "hide_high_risk": True,
        },
    },
    "老師聚餐不踩雷": {
        "description": "展示評論分析價值，優先聚餐友善類型、高評分與低評論風險。",
        "smart_mode": "不想踩雷",
        "overrides": {
            "budget": 240,
            "distance": 14,
            "category": "不限",
            "required_categories": ["日式", "義式", "火鍋", "鐵板燒", "美式", "韓式", "泰式", "港式"],
            "weather_mode": "手動選擇",
            "sort_by": "評分最高",
            "min_rating": 4.0,
            "review_weight": 90,
            "max_negative_ratio": 40,
            "hide_high_risk": True,
        },
    },
}


RECIPE_DEMO_CASES = {
    "手動自訂": {
        "description": "不套用展示情境，保留完整手動控制。",
        "smart_mode": "自訂",
        "custom_ingredients": "",
        "overrides": {},
    },
    "宅家不出門": {
        "description": "只用冰箱現有食材，展示內食族不想出門的情境。",
        "smart_mode": "我不想出門",
        "custom_ingredients": "",
        "overrides": {
            "default_ingredients": ["雞蛋", "白飯", "蔥", "醬油"],
            "max_missing": 0,
            "only_cookable": True,
            "max_time": 25,
        },
    },
    "清冰箱減浪費": {
        "description": "展示保存優先級，讓快過期或浪費成本高的食材優先被使用。",
        "smart_mode": "清冰箱模式",
        "custom_ingredients": "豆腐, 高麗菜",
        "overrides": {
            "default_ingredients": ["雞蛋", "白飯", "蔥", "番茄"],
            "max_time": 40,
            "max_missing": 2,
        },
    },
    "健身低熱量": {
        "description": "展示熱量限制與食譜篩選，適合控制飲食的使用者。",
        "smart_mode": "低熱量",
        "custom_ingredients": "雞胸肉, 青菜",
        "overrides": {
            "default_ingredients": ["雞蛋", "番茄", "豆腐"],
            "max_calories": 450,
            "max_time": 30,
        },
    },
}


def index_of(options, value, fallback=0):
    try:
        return options.index(value)
    except ValueError:
        return fallback


def format_score_delta(current, previous):
    try:
        return f"{float(current) - float(previous):+.1f}"
    except (TypeError, ValueError):
        return "--"


def get_restaurant_persona(row):
    personas = []
    if row.get("price", 999) <= 120 or row.get("cp_score", 0) >= 80:
        personas.append("預算有限者")
    if row.get("distance", 99) <= 6 or row.get("serve_speed") == "快":
        personas.append("趕時間者")
    if row.get("review_risk") == "低" or row.get("rating", 0) >= 4.3:
        personas.append("怕踩雷者")
    if row.get("takeout") == "yes":
        personas.append("外帶族")
    if not personas:
        personas.append("一般外食族")
    return "、".join(personas[:3])


def get_restaurant_decision_tradeoff(best, second=None):
    strengths = []
    if best.get("price", 999) <= 120:
        strengths.append("價格較友善")
    if best.get("distance", 99) <= 6:
        strengths.append("距離近")
    if best.get("rating", 0) >= 4.2:
        strengths.append("評分穩定")
    if best.get("review_risk") == "低":
        strengths.append("評論風險低")
    if best.get("serve_speed") == "快":
        strengths.append("出餐速度快")
    if not strengths:
        strengths.append("整體條件平均")

    if second is None:
        return "、".join(strengths[:3])

    comparisons = []
    if best.get("price", 999) < second.get("price", 999):
        comparisons.append(f"比 {second['name']} 便宜 {int(second['price'] - best['price'])} 元")
    if best.get("distance", 99) < second.get("distance", 99):
        comparisons.append(f"比 {second['name']} 近 {second['distance'] - best['distance']:.1f} 分鐘")
    if best.get("negative_ratio", 100) < second.get("negative_ratio", 100):
        comparisons.append(f"負評比例低 {second['negative_ratio'] - best['negative_ratio']:.1f}%")
    if best.get("rating", 0) > second.get("rating", 0):
        comparisons.append(f"評分高 {best['rating'] - second['rating']:.1f}")
    if comparisons:
        return "；".join(comparisons[:2])
    return "、".join(strengths[:3])


def get_recipe_persona(row):
    personas = []
    if row.get("missing_count", 99) == 0:
        personas.append("不想出門者")
    if row.get("time", 99) <= 15:
        personas.append("趕時間者")
    if row.get("calories", 999) <= 450:
        personas.append("控制熱量者")
    if row.get("priority_bonus", 0) > 0:
        personas.append("清冰箱者")
    if row.get("difficulty") == "簡單":
        personas.append("料理新手")
    if not personas:
        personas.append("一般內食族")
    return "、".join(personas[:3])


def get_recipe_decision_tradeoff(best, second=None):
    strengths = []
    if best.get("missing_count", 99) == 0:
        strengths.append("現有食材可直接完成")
    if best.get("time", 99) <= 20:
        strengths.append("料理時間短")
    if best.get("calories", 999) <= 500:
        strengths.append("熱量較低")
    if best.get("priority_bonus", 0) > 0:
        strengths.append("能消耗高優先食材")
    if not strengths:
        strengths.append("食材與條件整體匹配")

    if second is None:
        return "、".join(strengths[:3])

    comparisons = []
    if best.get("missing_count", 99) < second.get("missing_count", 99):
        comparisons.append(f"比 {second['name']} 少缺 {int(second['missing_count'] - best['missing_count'])} 種食材")
    if best.get("time", 99) < second.get("time", 99):
        comparisons.append(f"比 {second['name']} 快 {int(second['time'] - best['time'])} 分鐘")
    if best.get("calories", 999) < second.get("calories", 999):
        comparisons.append(f"熱量少 {int(second['calories'] - best['calories'])} kcal")
    if best.get("priority_bonus", 0) > second.get("priority_bonus", 0):
        comparisons.append("更能消耗高優先食材")
    if comparisons:
        return "；".join(comparisons[:2])
    return "、".join(strengths[:3])


def render_restaurant_decision_summary(result, smart_mode, weather, meal_time, use_review_analysis):
    if result.empty:
        return

    final_column = "final_score" if "final_score" in result.columns else "score"
    sorted_result = result.sort_values(by=[final_column], ascending=False)
    best = sorted_result.iloc[0]
    second = sorted_result.iloc[1] if len(sorted_result) > 1 else None
    review_risk = best.get("review_risk", "未知")
    negative_ratio = best.get("negative_ratio", 0)
    review_text = (
        f"評論風險 {review_risk}、負評比例 {negative_ratio}%"
        if use_review_analysis
        else "尚未納入評論風險"
    )
    takeout_text = format_takeout(best.get("takeout", "不限"))
    st.markdown(
        "<div class='insight-panel decision-hero'>"
        "<div class='insight-panel__title'>本次最佳建議</div>"
        f"<div class='insight-panel__body'><b>{html.escape(str(best['name']))}</b> "
        f"適合「{html.escape(str(smart_mode))}」情境。"
        f"約 {best['price']} 元、距離 {best['distance']} 分鐘、評分 {best['rating']}，"
        f"{html.escape(review_text)}，{takeout_text}。"
        f"目前時段為 {html.escape(str(meal_time))}、天氣為 {html.escape(str(weather))}，"
        f"系統建議先從這間開始考慮。</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    second_text = "目前沒有第二名可比較。"
    if second is not None:
        delta = format_score_delta(best.get(final_column), second.get(final_column))
        second_text = f"第二名是 {second['name']}，分數差距 {delta}。{get_restaurant_decision_tradeoff(best, second)}。"
    st.markdown(
        "<div class='decision-grid'>"
        "<div class='decision-tile'>"
        "<div class='decision-tile__label'>適合族群</div>"
        f"<div class='decision-tile__value'>{html.escape(get_restaurant_persona(best))}</div>"
        "</div>"
        "<div class='decision-tile'>"
        "<div class='decision-tile__label'>關鍵取捨</div>"
        f"<div class='decision-tile__value'>{html.escape(get_restaurant_decision_tradeoff(best, second))}</div>"
        "</div>"
        "<div class='decision-tile'>"
        "<div class='decision-tile__label'>為什麼不是第二名</div>"
        f"<div class='decision-tile__value'>{html.escape(second_text)}</div>"
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )


def render_recipe_decision_summary(result, smart_mode, current_ingredients):
    if result.empty:
        return

    score_column = "final_score" if "final_score" in result.columns else "score"
    sorted_result = result.sort_values(by=[score_column], ascending=False)
    best = sorted_result.iloc[0]
    second = sorted_result.iloc[1] if len(sorted_result) > 1 else None
    ingredient_text = "、".join(current_ingredients) or "尚未輸入"
    missing_text = best.get("missing_ingredients", "") or "無"
    st.markdown(
        "<div class='insight-panel decision-hero'>"
        "<div class='insight-panel__title'>本次最佳建議</div>"
        f"<div class='insight-panel__body'><b>{html.escape(str(best['name']))}</b> "
        f"適合「{html.escape(str(smart_mode))}」情境。"
        f"料理時間約 {best['time']} 分鐘、熱量 {best['calories']} kcal、難度 {html.escape(str(best['difficulty']))}。"
        f"目前食材：{html.escape(ingredient_text)}；缺少食材：{html.escape(str(missing_text))}。"
        "系統會把食材符合度與保存優先級一起納入排序。</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    second_text = "目前沒有第二名可比較。"
    if second is not None:
        delta = format_score_delta(best.get(score_column), second.get(score_column))
        second_text = f"第二名是 {second['name']}，分數差距 {delta}。{get_recipe_decision_tradeoff(best, second)}。"
    st.markdown(
        "<div class='decision-grid'>"
        "<div class='decision-tile'>"
        "<div class='decision-tile__label'>適合族群</div>"
        f"<div class='decision-tile__value'>{html.escape(get_recipe_persona(best))}</div>"
        "</div>"
        "<div class='decision-tile'>"
        "<div class='decision-tile__label'>關鍵取捨</div>"
        f"<div class='decision-tile__value'>{html.escape(get_recipe_decision_tradeoff(best, second))}</div>"
        "</div>"
        "<div class='decision-tile'>"
        "<div class='decision-tile__label'>為什麼不是第二名</div>"
        f"<div class='decision-tile__value'>{html.escape(second_text)}</div>"
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )


def render_restaurant_empty_guidance(candidate_result, evaluation_baseline, filters):
    st.markdown(
        "<div class='nudge-box'><b>系統放寬建議：</b>目前不是資料不存在，而是條件可能太嚴格。"
        "可以依照下列方向快速調整。</div>",
        unsafe_allow_html=True,
    )
    suggestions = []
    if candidate_result.empty:
        suggestions.append("放寬預算或距離，因為基礎條件已經沒有餐廳通過。")
        suggestions.append("把餐點類型改成不限，先看附近有什麼可行選項。")
        if filters["min_rating"] >= 4:
            suggestions.append("最低評分可先降到 3.8，再交給評論分析避雷。")
    else:
        if filters["use_review_analysis"] and not evaluation_baseline.empty:
            avg_negative = evaluation_baseline["negative_ratio"].mean()
            suggestions.append(
                f"目前候選餐廳平均負評比例約 {avg_negative:.1f}%，可把可接受負評比例提高 10% 觀察。"
            )
        if filters["hide_high_risk"]:
            suggestions.append("暫時取消隱藏高風險評論餐廳，改用評論摘要人工確認。")
        if filters["top_n"] <= 5:
            suggestions.append("推薦筆數可提高到 8 到 10 筆，讓系統保留更多候選。")
    for item in suggestions[:4]:
        st.write(f"- {item}")


def render_recipe_empty_guidance(candidate_result, filters):
    st.markdown(
        "<div class='nudge-box'><b>系統放寬建議：</b>目前條件可能讓可行食譜被排除。"
        "可以先用下面的方式找回候選，再慢慢收斂。</div>",
        unsafe_allow_html=True,
    )
    suggestions = []
    if candidate_result.empty:
        suggestions.append("增加最多可缺少食材數，先找出接近可做的食譜。")
        suggestions.append("把料理難度改成不限，避免簡單食譜資料不足。")
        suggestions.append("提高烹飪時間上限到 30 或 40 分鐘。")
    else:
        if filters["only_cookable"]:
            suggestions.append("取消只顯示現有食材足夠，讓系統列出少量採買就能完成的食譜。")
        if filters["max_calories"] <= 450:
            suggestions.append("熱量上限可先提高 100 kcal，避免排除份量正常的餐點。")
        if filters["max_missing"] <= 1:
            suggestions.append("最多可缺少食材數可提高到 2，通常只需要補買一兩樣。")
    for item in suggestions[:4]:
        st.write(f"- {item}")


def render_restaurant_decision_dashboard(result, all_restaurants, review_analysis, use_review_analysis):
    full_review_data = merge_review_analysis(all_restaurants, review_analysis)
    review_ready = not full_review_data.empty and full_review_data["review_count"].sum() > 0

    with st.expander("外食決策分析 Dashboard", expanded=False):
        if result.empty:
            st.info("目前沒有推薦結果可分析，放寬條件後會顯示決策儀表板。")
            return

        final_column = "final_score" if "final_score" in result.columns else "score"
        best = result.sort_values(by=[final_column], ascending=False).iloc[0]
        avg_negative = result["negative_ratio"].mean() if "negative_ratio" in result.columns else 0
        risk_count = int((result["review_risk"] == "高").sum()) if "review_risk" in result.columns else 0
        stable_count = int((result["review_risk"] == "低").sum()) if "review_risk" in result.columns else 0

        metric1, metric2, metric3, metric4 = st.columns(4)
        metric1.metric("決策候選數", len(result))
        metric2.metric("最佳選項", best["name"])
        metric3.metric("平均負評比例", f"{avg_negative:.1f}%")
        metric4.metric("評論低風險", stable_count, delta=f"高風險 {risk_count}")

        strongest_review = result.sort_values(by=["review_adjustment"], ascending=False).iloc[0]
        weakest_review = result.sort_values(by=["review_adjustment"], ascending=True).iloc[0]
        price_friendly = result.sort_values(by=["price", final_column], ascending=[True, False]).iloc[0]
        review_note = "已納入評論文字分析" if use_review_analysis else "目前未納入評論文字分析"

        st.markdown(
            "<div class='dashboard-grid'>"
            "<div class='insight-panel'>"
            "<div class='insight-panel__title'>評論如何影響推薦</div>"
            f"<div class='insight-panel__body'>{review_note}。"
            f"本次評論加分最高的是 <b>{html.escape(str(strongest_review['name']))}</b>"
            f"（{strongest_review['review_adjustment']:+.1f}），"
            f"最需要注意的是 <b>{html.escape(str(weakest_review['name']))}</b>"
            f"（{weakest_review['review_adjustment']:+.1f}）。</div>"
            "</div>"
            "<div class='insight-panel'>"
            "<div class='insight-panel__title'>決策建議摘要</div>"
            f"<div class='insight-panel__body'>若只看綜合決策，建議優先考慮 "
            f"<b>{html.escape(str(best['name']))}</b>；若今天想省錢，"
            f"可改看 <b>{html.escape(str(price_friendly['name']))}</b>"
            f"（約 {price_friendly['price']} 元）。</div>"
            "</div>"
            "</div>",
            unsafe_allow_html=True,
        )

        dashboard_rows = []
        for _, row in result.sort_values(by=[final_column], ascending=False).head(5).iterrows():
            score_delta = row.get("final_score", row["score"]) - row["score"]
            dashboard_rows.append(
                "<tr>"
                f"<td>{html.escape(str(row['name']))}</td>"
                f"<td>{row['score']}</td>"
                f"<td>{row.get('final_score', row['score'])}</td>"
                f"<td>{score_delta:+.1f}</td>"
                f"<td>{row.get('negative_ratio', 0)}%</td>"
                f"<td>{html.escape(str(row.get('review_risk', '未知')))}</td>"
                "</tr>"
            )
        st.markdown(
            "<table class='mini-table'>"
            "<thead><tr><th>餐廳</th><th>原始分數</th><th>最終分數</th><th>評論影響</th><th>負評比例</th><th>風險</th></tr></thead>"
            f"<tbody>{''.join(dashboard_rows)}</tbody></table>",
            unsafe_allow_html=True,
        )

        if review_ready:
            category_risk = (
                full_review_data.groupby("category", as_index=False)
                .agg(
                    平均負評比例=("negative_ratio", "mean"),
                    平均情緒分數=("sentiment_score", "mean"),
                    餐廳數=("name", "count"),
                )
                .sort_values(by=["平均負評比例", "平均情緒分數"], ascending=[False, True])
                .head(5)
            )
            category_rows = []
            for _, row in category_risk.iterrows():
                category_rows.append(
                    "<tr>"
                    f"<td>{html.escape(str(row['category']))}</td>"
                    f"<td>{row['平均負評比例']:.1f}%</td>"
                    f"<td>{row['平均情緒分數']:.1f}</td>"
                    f"<td>{int(row['餐廳數'])}</td>"
                    "</tr>"
                )
            st.markdown(
                "<table class='mini-table'>"
                "<thead><tr><th>餐點類型</th><th>平均負評比例</th><th>平均情緒</th><th>資料筆數</th></tr></thead>"
                f"<tbody>{''.join(category_rows)}</tbody></table>",
                unsafe_allow_html=True,
            )


def render_recipe_decision_dashboard(result, all_recipes, current_ingredients, priority_profiles):
    with st.expander("內食決策分析 Dashboard", expanded=False):
        if result.empty:
            st.info("目前沒有推薦結果可分析，放寬條件或增加食材後會顯示決策儀表板。")
            return

        score_column = "final_score" if "final_score" in result.columns else "score"
        best = result.sort_values(by=[score_column], ascending=False).iloc[0]
        cookable_count = int((result["missing_count"] == 0).sum())
        avg_missing = result["missing_count"].mean()
        avg_time = result["time"].mean()
        high_priority_items = [
            name
            for name, profile in priority_profiles.items()
            if profile.get("level") == "高"
        ]
        waste_value = sum(
            profile.get("price", 0)
            for profile in priority_profiles.values()
            if profile.get("level") == "高"
        )

        metric1, metric2, metric3, metric4 = st.columns(4)
        metric1.metric("目前食材數", len(current_ingredients))
        metric2.metric("可直接料理", cookable_count)
        metric3.metric("平均缺少食材", f"{avg_missing:.1f} 項")
        metric4.metric("高優先食材", len(high_priority_items), delta=f"約 {waste_value:.0f} 元")

        best_use = result.sort_values(
            by=["priority_bonus", "matched_count", score_column],
            ascending=[False, False, False],
        ).iloc[0]
        fastest = result.sort_values(by=["time", score_column], ascending=[True, False]).iloc[0]

        st.markdown(
            "<div class='dashboard-grid'>"
            "<div class='insight-panel'>"
            "<div class='insight-panel__title'>食材保存決策</div>"
            f"<div class='insight-panel__body'>目前最應優先處理的食材："
            f"<b>{html.escape('、'.join(high_priority_items) if high_priority_items else '尚無高風險食材')}</b>。"
            f"系統會把這些食材轉成推薦加權，讓快過期或成本較高的食材更容易被用掉。</div>"
            "</div>"
            "<div class='insight-panel'>"
            "<div class='insight-panel__title'>料理策略建議</div>"
            f"<div class='insight-panel__body'>綜合分數最高的是 "
            f"<b>{html.escape(str(best['name']))}</b>；"
            f"若要最快完成，可選 <b>{html.escape(str(fastest['name']))}</b>"
            f"（{fastest['time']} 分鐘）；"
            f"最能利用高優先食材的是 <b>{html.escape(str(best_use['name']))}</b>。</div>"
            "</div>"
            "</div>",
            unsafe_allow_html=True,
        )

        fit_rows = []
        for _, row in result.sort_values(by=[score_column], ascending=False).head(5).iterrows():
            fit_rows.append(
                "<tr>"
                f"<td>{html.escape(str(row['name']))}</td>"
                f"<td>{row.get(score_column, row['score'])}</td>"
                f"<td>{row['matched_count']}</td>"
                f"<td>{row['missing_count']}</td>"
                f"<td>{row['time']} 分鐘</td>"
                f"<td>{row.get('priority_bonus', 0)}</td>"
                "</tr>"
            )
        st.markdown(
            "<table class='mini-table'>"
            "<thead><tr><th>食譜</th><th>最終分數</th><th>符合食材</th><th>缺少食材</th><th>時間</th><th>保存加權</th></tr></thead>"
            f"<tbody>{''.join(fit_rows)}</tbody></table>",
            unsafe_allow_html=True,
        )

        category_summary = (
            all_recipes.groupby("category", as_index=False)
            .agg(食譜數=("name", "count"), 平均時間=("time", "mean"), 平均熱量=("calories", "mean"))
            .sort_values(by=["食譜數", "平均時間"], ascending=[False, True])
            .head(6)
        )
        category_rows = []
        for _, row in category_summary.iterrows():
            category_rows.append(
                "<tr>"
                f"<td>{html.escape(str(row['category']))}</td>"
                f"<td>{int(row['食譜數'])}</td>"
                f"<td>{row['平均時間']:.1f} 分鐘</td>"
                f"<td>{row['平均熱量']:.0f} kcal</td>"
                "</tr>"
            )
        st.markdown(
            "<table class='mini-table'>"
            "<thead><tr><th>食譜類型</th><th>資料筆數</th><th>平均時間</th><th>平均熱量</th></tr></thead>"
            f"<tbody>{''.join(category_rows)}</tbody></table>",
            unsafe_allow_html=True,
        )


def calculate_top_overlap(left_names, right_names):
    left_set = set(left_names)
    right_set = set(right_names)
    if not left_set and not right_set:
        return 0
    return round(len(left_set & right_set) / max(len(left_set | right_set), 1) * 100, 1)


def render_restaurant_model_evaluation(baseline_result, enhanced_result, top_n, use_review_analysis):
    with st.expander("外食模型評估：評論分析前後比較", expanded=False):
        if baseline_result.empty or enhanced_result.empty:
            st.info("目前資料不足，無法進行模型評估。")
            return

        baseline_top = baseline_result.head(top_n).copy()
        enhanced_top = enhanced_result.head(top_n).copy()
        baseline_names = baseline_top["name"].tolist()
        enhanced_names = enhanced_top["name"].tolist()
        overlap = calculate_top_overlap(baseline_names, enhanced_names)
        first_changed = baseline_names[0] != enhanced_names[0]
        baseline_negative = baseline_top["negative_ratio"].mean() if "negative_ratio" in baseline_top.columns else 0
        enhanced_negative = enhanced_top["negative_ratio"].mean() if "negative_ratio" in enhanced_top.columns else 0
        baseline_sentiment = baseline_top["sentiment_score"].mean() if "sentiment_score" in baseline_top.columns else 50
        enhanced_sentiment = enhanced_top["sentiment_score"].mean() if "sentiment_score" in enhanced_top.columns else 50

        metric1, metric2, metric3, metric4 = st.columns(4)
        metric1.metric("Top 清單重疊率", f"{overlap:.1f}%")
        metric2.metric("第一名是否改變", "是" if first_changed else "否")
        metric3.metric("平均負評比例變化", f"{enhanced_negative:.1f}%", delta=f"{enhanced_negative - baseline_negative:+.1f}%")
        metric4.metric("平均評論情緒變化", f"{enhanced_sentiment:.1f}", delta=f"{enhanced_sentiment - baseline_sentiment:+.1f}")

        mode_note = "目前排序已啟用評論分析。" if use_review_analysis else "目前排序未啟用評論分析，以下用模擬方式呈現評論分析可造成的差異。"
        st.caption(mode_note)

        baseline_rank = {name: index + 1 for index, name in enumerate(baseline_names)}
        enhanced_rank = {name: index + 1 for index, name in enumerate(enhanced_names)}
        comparison_names = list(dict.fromkeys(baseline_names + enhanced_names))
        rows = []
        for name in comparison_names:
            base_row = baseline_top[baseline_top["name"] == name]
            enhanced_row = enhanced_top[enhanced_top["name"] == name]
            row_source = enhanced_row if not enhanced_row.empty else base_row
            source = row_source.iloc[0]
            before = baseline_rank.get(name, "未進入")
            after = enhanced_rank.get(name, "未進入")
            rows.append(
                "<tr>"
                f"<td>{html.escape(str(name))}</td>"
                f"<td>{before}</td>"
                f"<td>{after}</td>"
                f"<td>{source.get('score', 0)}</td>"
                f"<td>{source.get('final_score', source.get('score', 0))}</td>"
                f"<td>{source.get('review_adjustment', 0):+.1f}</td>"
                f"<td>{source.get('negative_ratio', 0)}%</td>"
                "</tr>"
            )

        st.markdown(
            "<table class='mini-table'>"
            "<thead><tr><th>餐廳</th><th>原始排名</th><th>評論後排名</th><th>原始分數</th><th>最終分數</th><th>評論調整</th><th>負評比例</th></tr></thead>"
            f"<tbody>{''.join(rows)}</tbody></table>",
            unsafe_allow_html=True,
        )

        if enhanced_negative < baseline_negative:
            st.success("評估結果：加入評論分析後，推薦清單的平均負評比例下降，代表系統更偏向避開評論風險較高的餐廳。")
        elif enhanced_sentiment > baseline_sentiment:
            st.success("評估結果：加入評論分析後，推薦清單的平均評論情緒上升，代表系統更偏向口碑穩定的餐廳。")
        else:
            st.info("評估結果：本次條件下評論分析沒有明顯改善平均風險，但仍提供排序解釋與避雷資訊。")


def render_recipe_model_evaluation(baseline_result, enhanced_result, top_n, priority_profiles):
    with st.expander("內食模型評估：保存優先級前後比較", expanded=False):
        if baseline_result.empty or enhanced_result.empty:
            st.info("目前資料不足，無法進行模型評估。")
            return

        baseline_top = baseline_result.head(top_n).copy()
        enhanced_top = enhanced_result.head(top_n).copy()
        baseline_names = baseline_top["name"].tolist()
        enhanced_names = enhanced_top["name"].tolist()
        overlap = calculate_top_overlap(baseline_names, enhanced_names)
        first_changed = baseline_names[0] != enhanced_names[0]
        baseline_bonus = baseline_top.get("priority_bonus", 0)
        enhanced_bonus = enhanced_top.get("priority_bonus", 0)
        baseline_missing = baseline_top["missing_count"].mean()
        enhanced_missing = enhanced_top["missing_count"].mean()

        high_priority_items = {
            name
            for name, profile in priority_profiles.items()
            if profile.get("level") == "高"
        }

        def count_high_priority_usage(data):
            if not high_priority_items or "priority_ingredients" not in data.columns:
                return 0
            total = 0
            for value in data["priority_ingredients"]:
                total += len(parse_ingredients(value) & high_priority_items)
            return total

        baseline_usage = count_high_priority_usage(baseline_top)
        enhanced_usage = count_high_priority_usage(enhanced_top)

        metric1, metric2, metric3, metric4 = st.columns(4)
        metric1.metric("Top 清單重疊率", f"{overlap:.1f}%")
        metric2.metric("第一名是否改變", "是" if first_changed else "否")
        metric3.metric("平均缺少食材變化", f"{enhanced_missing:.1f}", delta=f"{enhanced_missing - baseline_missing:+.1f}")
        metric4.metric("高優先食材使用次數", enhanced_usage, delta=f"{enhanced_usage - baseline_usage:+d}")

        rows = []
        baseline_rank = {name: index + 1 for index, name in enumerate(baseline_names)}
        enhanced_rank = {name: index + 1 for index, name in enumerate(enhanced_names)}
        comparison_names = list(dict.fromkeys(baseline_names + enhanced_names))
        for name in comparison_names:
            base_row = baseline_top[baseline_top["name"] == name]
            enhanced_row = enhanced_top[enhanced_top["name"] == name]
            row_source = enhanced_row if not enhanced_row.empty else base_row
            source = row_source.iloc[0]
            rows.append(
                "<tr>"
                f"<td>{html.escape(str(name))}</td>"
                f"<td>{baseline_rank.get(name, '未進入')}</td>"
                f"<td>{enhanced_rank.get(name, '未進入')}</td>"
                f"<td>{source.get('score', 0)}</td>"
                f"<td>{source.get('final_score', source.get('score', 0))}</td>"
                f"<td>{source.get('priority_bonus', 0)}</td>"
                f"<td>{html.escape(str(source.get('priority_ingredients', '') or '無'))}</td>"
                "</tr>"
            )

        st.markdown(
            "<table class='mini-table'>"
            "<thead><tr><th>食譜</th><th>原始排名</th><th>保存加權後排名</th><th>原始分數</th><th>最終分數</th><th>保存加權</th><th>優先食材</th></tr></thead>"
            f"<tbody>{''.join(rows)}</tbody></table>",
            unsafe_allow_html=True,
        )

        if enhanced_usage > baseline_usage:
            st.success("評估結果：加入保存優先級後，推薦清單更常使用高優先食材，有助於降低食材浪費。")
        elif enhanced_missing <= baseline_missing:
            st.success("評估結果：加入保存優先級後，推薦清單沒有增加準備難度，仍維持可料理性。")
        else:
            st.info("評估結果：本次條件下保存優先級改變有限，可調整食材保存資訊觀察排序變化。")


def render_recipe_card(rank, row):
    with st.container(border=True):
        title_col, action_col, feedback_col, score_col = st.columns([3.2, 1, 1.3, 1])
        with title_col:
            render_ranked_title(rank, row["name"])
        if row["name"] in st.session_state.favorite_recipes:
            action_col.button("已收藏", key=f"recipe_fav_{rank}_{row['name']}", disabled=True)
        elif action_col.button("收藏", key=f"recipe_fav_{rank}_{row['name']}"):
            add_favorite("recipe", row["name"])
            st.rerun()
        liked = row["name"] in st.session_state.recipe_feedback["liked"]
        disliked = row["name"] in st.session_state.recipe_feedback["disliked"]
        like_col, dislike_col = feedback_col.columns(2)
        if like_col.button("喜歡", key=f"recipe_like_{rank}_{row['name']}", disabled=liked):
            record_feedback("recipe", row["name"], "like")
            st.rerun()
        if dislike_col.button("不喜歡", key=f"recipe_dislike_{rank}_{row['name']}", disabled=disliked):
            record_feedback("recipe", row["name"], "dislike")
            st.rerun()
        score_col.metric("推薦分數", f"{row['final_score']}")
        if row.get("preference_adjustment", 0) != 0:
            score_col.caption(f"偏好調整 {row['preference_adjustment']:+.1f}")
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
    review_analysis = analyze_reviews(load_reviews("reviews.csv"))

    st.sidebar.header("外食條件")
    st.sidebar.caption("先選使用情境，系統會自動帶入常用條件；需要更細再展開進階條件。")

    restaurant_demo_case = st.sidebar.selectbox("展示案例", list(RESTAURANT_DEMO_CASES.keys()))
    restaurant_demo = RESTAURANT_DEMO_CASES[restaurant_demo_case]
    smart_mode_options = list(RESTAURANT_SMART_MODES.keys())
    smart_mode = st.sidebar.selectbox(
        "智慧模式",
        smart_mode_options,
        index=index_of(smart_mode_options, restaurant_demo["smart_mode"]),
        key=f"restaurant_smart_mode_{restaurant_demo_case}",
    )
    restaurant_profile = {
        **RESTAURANT_SMART_MODES[smart_mode],
        **restaurant_demo.get("overrides", {}),
    }
    restaurant_context_key = f"{restaurant_demo_case}_{smart_mode}"
    st.sidebar.info(restaurant_profile["description"])

    budget = st.sidebar.slider(
        "預算上限",
        50,
        300,
        int(restaurant_profile["budget"]),
        step=5,
        key=f"restaurant_budget_{restaurant_context_key}",
    )
    max_distance = st.sidebar.slider(
        "可接受距離（分鐘）",
        1,
        20,
        int(restaurant_profile["distance"]),
        key=f"restaurant_distance_{restaurant_context_key}",
    )
    category_list = ["不限"] + sorted(df["category"].unique().tolist())
    category = st.sidebar.selectbox(
        "餐點類型",
        category_list,
        index=index_of(category_list, restaurant_profile["category"]),
        key=f"restaurant_category_{restaurant_context_key}",
    )
    mood_options = ["省錢", "疲累", "開心", "心情不好", "選擇困難"]
    mood = st.sidebar.selectbox(
        "目前心情",
        mood_options,
        index=index_of(mood_options, restaurant_profile["mood"]),
        key=f"restaurant_mood_{restaurant_context_key}",
    )
    detected_meal_time = detect_meal_time()

    with st.sidebar.expander("進階條件", expanded=False):
        meal_time_mode_options = ["自動判斷", "手動選擇"]
        meal_time_mode = st.radio(
            "用餐時段來源",
            meal_time_mode_options,
            horizontal=True,
            index=index_of(meal_time_mode_options, restaurant_profile["meal_time_mode"]),
            key=f"restaurant_meal_time_mode_{restaurant_context_key}",
        )
        if meal_time_mode == "自動判斷":
            meal_time = detected_meal_time
            st.success(f"自動判斷：{meal_time}")
        else:
            meal_time_options = ["不套用", "早餐", "午餐", "下午茶", "晚餐", "宵夜"]
            meal_time = st.selectbox(
                "用餐時段",
                meal_time_options,
                index=index_of(meal_time_options, restaurant_profile["manual_meal_time"], fallback=3),
                key=f"restaurant_meal_time_{restaurant_context_key}",
            )
        weather_mode_options = ["自動偵測", "手動選擇"]
        weather_mode = st.radio(
            "天氣來源",
            weather_mode_options,
            horizontal=True,
            index=index_of(weather_mode_options, restaurant_profile["weather_mode"]),
            key=f"restaurant_weather_mode_{restaurant_context_key}",
        )
        if weather_mode == "自動偵測":
            weather_location = st.text_input(
                "所在地區",
                value="Xitun District, Taichung, Taiwan",
                help="建議輸入行政區，例如 Xitun District, Taichung, Taiwan，避免天氣服務解析到錯誤區域。",
                key=f"restaurant_weather_location_{restaurant_context_key}",
            )
            weather_info = get_cached_weather(weather_location)
            weather = weather_info["weather"]
            if weather_info["ok"]:
                temp_text = "--" if weather_info["temperature_c"] is None else f"{weather_info['temperature_c']:.0f}°C"
                rain_text = f"降雨 {weather_info.get('precipitation_mm', 0):.1f} mm"
                st.success(
                    f"自動判斷：{weather}｜{weather_info['location']}｜{temp_text}｜{rain_text}｜{weather_info['description']}"
                )
            else:
                st.warning("天氣自動偵測失敗，已暫時使用普通天氣。可改用手動選擇。")
                st.caption(f"來源：{weather_info['source']}｜錯誤：{weather_info['error']}")
        else:
            weather_info = {
                "ok": False,
                "location": "手動選擇",
                "weather": "普通",
                "temperature_c": None,
                "precipitation_mm": 0,
                "description": "",
                "source": "manual",
                "error": "",
            }
            weather = st.selectbox("目前天氣", ["普通", "熱", "冷", "雨天"])
        takeout_options = ["不限", "yes", "no"]
        need_takeout = st.selectbox(
            "是否需要外帶",
            takeout_options,
            index=index_of(takeout_options, restaurant_profile["need_takeout"]),
            format_func=format_takeout,
            key=f"restaurant_takeout_{restaurant_context_key}",
        )
        max_spicy_level = st.slider(
            "可接受辣度",
            0,
            5,
            int(restaurant_profile["max_spicy_level"]),
            key=f"restaurant_spicy_{restaurant_context_key}",
        )
        prefer_fast = st.checkbox(
            "希望快速出餐",
            value=bool(restaurant_profile["prefer_fast"]),
            key=f"restaurant_fast_{restaurant_context_key}",
        )
        sort_options = ["綜合推薦", "CP值優先", "距離最近", "評分最高"]
        sort_by = st.selectbox(
            "排序方式",
            sort_options,
            index=index_of(sort_options, restaurant_profile["sort_by"]),
            key=f"restaurant_sort_{restaurant_context_key}",
        )
        min_rating = st.slider(
            "最低評分",
            0.0,
            5.0,
            float(restaurant_profile["min_rating"]),
            step=0.1,
            key=f"restaurant_rating_{restaurant_context_key}",
        )
        top_n = st.slider(
            "顯示推薦筆數",
            3,
            10,
            int(restaurant_profile["top_n"]),
            key=f"restaurant_top_n_{restaurant_context_key}",
        )

    with st.sidebar.expander("評論分析", expanded=False):
        use_review_analysis = st.checkbox(
            "納入評論文字分析",
            value=bool(restaurant_profile["use_review_analysis"]),
            key=f"restaurant_review_enabled_{restaurant_context_key}",
        )
        review_weight = st.slider(
            "評論影響權重",
            0,
            100,
            int(restaurant_profile["review_weight"]),
            step=10,
            key=f"restaurant_review_weight_{restaurant_context_key}",
        )
        max_negative_ratio = st.slider(
            "可接受負評比例",
            0,
            100,
            int(restaurant_profile["max_negative_ratio"]),
            step=5,
            key=f"restaurant_negative_{restaurant_context_key}",
        )
        hide_high_risk = st.checkbox(
            "隱藏高風險評論餐廳",
            value=bool(restaurant_profile["hide_high_risk"]),
            key=f"restaurant_hide_risk_{restaurant_context_key}",
        )

    with st.sidebar.expander("定位與距離", expanded=True):
        location_mode = st.radio("定位方式", ["瀏覽器定位", "手動選擇據點"], horizontal=True)
        user_location = None
        if location_mode == "瀏覽器定位":
            if get_geolocation is None:
                st.warning("目前環境尚未安裝瀏覽器定位套件，已改用手動據點。")
            else:
                browser_location = normalize_browser_location(get_geolocation())
                if browser_location:
                    user_location = browser_location
                    accuracy = user_location.get("accuracy")
                    accuracy_text = "" if accuracy is None else f"｜誤差約 {accuracy:.0f} 公尺"
                    st.success(
                        f"已取得定位：{user_location['latitude']:.5f}, {user_location['longitude']:.5f}{accuracy_text}"
                    )
                else:
                    st.info("請允許瀏覽器定位權限。若沒有跳出權限視窗，可改用手動選擇據點。")

        if user_location is None:
            preset_name = st.selectbox("手動據點", list(LOCATION_PRESETS.keys()))
            user_location = {**LOCATION_PRESETS[preset_name], "source": preset_name, "accuracy": None}
            st.caption(f"目前使用據點：{preset_name}")

    df = apply_user_location_to_restaurants(df, user_location)
    recommendation_df = df
    required_categories = restaurant_profile.get("required_categories", [])
    if required_categories:
        recommendation_df = recommendation_df[recommendation_df["category"].isin(required_categories)]
        st.sidebar.caption(f"展示案例鎖定類型：{'、'.join(required_categories)}")

    candidate_result = recommend_restaurants(
        recommendation_df,
        budget,
        max_distance,
        category,
        weather,
        mood,
        need_takeout,
        max_spicy_level,
        prefer_fast,
        len(df),
        sort_by,
        min_rating,
        meal_time,
    )
    evaluation_baseline = merge_review_analysis(candidate_result, review_analysis)
    evaluation_baseline["final_score"] = evaluation_baseline["score"]
    evaluation_enhanced = apply_review_adjustment(evaluation_baseline, True, review_weight)
    preference_source = merge_review_analysis(recommendation_df, review_analysis)

    result = evaluation_baseline.copy()
    if use_review_analysis:
        result = result[result["negative_ratio"] <= max_negative_ratio]
        if hide_high_risk:
            result = result[result["review_risk"] != "高"]
    result = apply_review_adjustment(result, use_review_analysis, review_weight)
    result = apply_restaurant_intent_adjustment(result, restaurant_demo_case if restaurant_demo_case != "手動自訂" else smart_mode)
    result = apply_restaurant_preference_learning(result, preference_source).head(top_n)

    render_anchor("demo")
    render_demo_flow(mode, restaurant_demo_case, restaurant_demo["description"])

    render_anchor("overview")
    render_section_kicker("外食決策")
    st.markdown(
        '<div class="soft-note">系統會綜合預算、距離、心情、天氣、評分與 CP 值，產生今天最適合的外食選項。</div>',
        unsafe_allow_html=True,
    )
    render_restaurant_decision_summary(result, smart_mode, weather, meal_time, use_review_analysis)
    render_preference_learning_summary("restaurant", preference_source)

    if st.session_state.restaurant_decision is not None:
        current_names = set(result["name"].tolist())
        if st.session_state.restaurant_decision["name"] not in current_names:
            st.session_state.restaurant_decision = None

    st.info(f"目前情緒策略：{get_mood_strategy(mood)}")
    if weather_mode == "自動偵測":
        st.caption(
            f"自動天氣：{weather}｜地點：{weather_info['location']}｜來源：{weather_info['source']}"
        )
    if meal_time_mode == "自動判斷":
        st.caption(f"自動時段：{meal_time}｜{get_meal_time_strategy(meal_time)}")
    elif meal_time != "不套用":
        st.caption(f"手動時段：{meal_time}｜{get_meal_time_strategy(meal_time)}")
    if user_location:
        st.caption(
            f"距離計算基準：{user_location['source']}｜"
            f"{user_location['latitude']:.5f}, {user_location['longitude']:.5f}"
        )
    st.caption(
        f"排序方式：{sort_by}｜最低評分：{min_rating:.1f}｜顯示 {top_n} 筆｜"
        f"評論分析：{'啟用' if use_review_analysis else '未啟用'}"
    )

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

    render_anchor("dashboard")
    render_restaurant_decision_dashboard(result, df, review_analysis, use_review_analysis)

    render_anchor("evaluation")
    render_restaurant_model_evaluation(evaluation_baseline, evaluation_enhanced, top_n, use_review_analysis)

    render_anchor("reviews")
    render_review_analysis_panel(result)

    render_anchor("model")
    render_restaurant_model_explainer(
        result,
        budget,
        max_distance,
        category,
        weather,
        mood,
        need_takeout,
        max_spicy_level,
        prefer_fast,
        meal_time,
        use_review_analysis,
        review_weight,
    )
    render_restaurant_sensitivity_analysis(result)

    render_anchor("summary")
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
    render_anchor("list")
    render_section_kicker("推薦清單")
    st.subheader(f"外食決策建議前 {top_n} 名")
    if result.empty:
        st.warning("目前條件太嚴格，沒有找到符合的餐廳。可以降低最低評分、放寬距離或調整餐點類型。")
        render_restaurant_empty_guidance(
            candidate_result,
            evaluation_baseline,
            {
                "min_rating": min_rating,
                "use_review_analysis": use_review_analysis,
                "hide_high_risk": hide_high_risk,
                "top_n": top_n,
            },
        )
    for rank, (_, row) in enumerate(result.iterrows(), start=1):
        render_restaurant_card(rank, row)

    st.divider()
    render_anchor("map")
    render_restaurant_map(result, user_location)

    render_anchor("data")
    with st.expander("查看完整餐廳資料表", expanded=False):
        st.dataframe(df, width="stretch")

else:
    recipes = load_recipes("recipes.csv")

    st.sidebar.header("內食條件")
    st.sidebar.caption("先選料理情境，再輸入冰箱食材；系統會把可料理性與食材保存優先級一起納入推薦。")
    recipe_demo_case = st.sidebar.selectbox("展示案例", list(RECIPE_DEMO_CASES.keys()))
    recipe_demo = RECIPE_DEMO_CASES[recipe_demo_case]
    recipe_smart_options = list(RECIPE_SMART_MODES.keys())
    recipe_smart_mode = st.sidebar.selectbox(
        "內食智慧模式",
        recipe_smart_options,
        index=index_of(recipe_smart_options, recipe_demo["smart_mode"]),
        key=f"recipe_smart_mode_{recipe_demo_case}",
    )
    recipe_profile = {
        **RECIPE_SMART_MODES[recipe_smart_mode],
        **recipe_demo.get("overrides", {}),
    }
    recipe_context_key = f"{recipe_demo_case}_{recipe_smart_mode}"
    st.sidebar.info(recipe_profile["description"])

    ingredient_options = collect_ingredient_options(recipes)
    default_ingredients = [
        item for item in recipe_profile["default_ingredients"]
        if item in ingredient_options
    ]
    selected_ingredients = st.sidebar.multiselect(
        "冰箱常見食材",
        ingredient_options,
        default=default_ingredients,
        key=f"recipe_ingredients_{recipe_context_key}",
    )
    custom_ingredients = st.sidebar.text_area(
        "其他食材",
        value=recipe_demo.get("custom_ingredients", ""),
        help="可用逗號、頓號或空白分隔，例如：豆腐, 番茄",
        key=f"recipe_custom_ingredients_{recipe_context_key}",
    )
    ingredient_text = ",".join(selected_ingredients + [custom_ingredients])
    current_ingredients = sorted(parse_ingredients(ingredient_text))
    priority_profiles = render_ingredient_priority_inputs(current_ingredients)

    with st.sidebar.expander("進階條件", expanded=False):
        max_time = st.slider(
            "可接受烹飪時間（分鐘）",
            5,
            60,
            int(recipe_profile["max_time"]),
            step=5,
            key=f"recipe_time_{recipe_context_key}",
        )
        difficulty_options = ["不限", "簡單", "中等", "困難"]
        difficulty_preference = st.selectbox(
            "料理難度",
            difficulty_options,
            index=index_of(difficulty_options, recipe_profile["difficulty"]),
            key=f"recipe_difficulty_{recipe_context_key}",
        )
        max_calories = st.slider(
            "熱量上限（kcal）",
            150,
            900,
            int(recipe_profile["max_calories"]),
            step=50,
            key=f"recipe_calories_{recipe_context_key}",
        )
        max_missing = st.slider(
            "最多可缺少食材數",
            0,
            5,
            int(recipe_profile["max_missing"]),
            key=f"recipe_missing_{recipe_context_key}",
        )
        only_cookable = st.checkbox(
            "只顯示現有食材足夠的食譜",
            value=bool(recipe_profile["only_cookable"]),
            key=f"recipe_only_cookable_{recipe_context_key}",
        )
        top_n = st.slider(
            "顯示推薦筆數",
            3,
            10,
            int(recipe_profile["top_n"]),
            key=f"recipe_top_n_{recipe_context_key}",
        )

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
    result = apply_ingredient_priority_to_recipes(candidate_result, priority_profiles)
    result = apply_recipe_preference_learning(result, recipes).head(top_n)
    evaluation_baseline = candidate_result.copy()
    evaluation_enhanced = apply_ingredient_priority_to_recipes(candidate_result, priority_profiles)

    if st.session_state.recipe_decision is not None:
        current_recipe_names = set(result["name"].tolist())
        if st.session_state.recipe_decision["name"] not in current_recipe_names:
            st.session_state.recipe_decision = None

    render_anchor("demo")
    render_demo_flow(mode, recipe_demo_case, recipe_demo["description"])

    render_anchor("overview")
    render_section_kicker("內食決策")
    st.markdown(
        '<div class="soft-note">系統會依照冰箱食材、料理時間、熱量與食材保存狀態，優先推薦更適合先做的食譜。</div>',
        unsafe_allow_html=True,
    )
    render_recipe_decision_summary(result, recipe_smart_mode, current_ingredients)
    render_preference_learning_summary("recipe", recipes)

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

    render_anchor("dashboard")
    render_recipe_decision_dashboard(result, recipes, current_ingredients, priority_profiles)

    render_anchor("evaluation")
    render_recipe_model_evaluation(evaluation_baseline, evaluation_enhanced, top_n, priority_profiles)

    render_anchor("priority")
    render_ingredient_priority_summary(priority_profiles)

    st.divider()
    render_anchor("actions")
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

    render_anchor("list")
    render_section_kicker("推薦清單")
    st.subheader(f"內食食譜決策建議前 {top_n} 名")
    display_ingredients = "、".join(sorted(parse_ingredients(ingredient_text))) or "尚未輸入"
    st.caption(f"目前食材：{display_ingredients}")

    if result.empty:
        st.warning("目前條件太嚴格，沒有找到符合的食譜。可以提高熱量上限、增加可缺少食材數，或取消只顯示現有食材足夠。")
        render_recipe_empty_guidance(
            candidate_result,
            {
                "only_cookable": only_cookable,
                "max_calories": max_calories,
                "max_missing": max_missing,
            },
        )
    for rank, (_, row) in enumerate(result.iterrows(), start=1):
        render_recipe_card(rank, row)

    render_anchor("data")
    with st.expander("查看完整食譜資料表", expanded=False):
        st.dataframe(recipes, width="stretch")
