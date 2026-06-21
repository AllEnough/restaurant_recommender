from __future__ import annotations

from pathlib import Path
from typing import Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from core.weather_service import fetch_current_weather
from web_api.auth import favorite_router, router as auth_router
from web_api.emotion import router as emotion_router
from web_api.services import (
    recipe_options,
    recommend_recipe_payload,
    recommend_restaurant_payload,
    restaurant_options,
)


app = FastAPI(title="智慧飲食決策系統 API", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(favorite_router)
app.include_router(emotion_router)


class RestaurantRequest(BaseModel):
    scenario: str = "大學生省錢午餐"
    smart_mode: str = "省錢外食"
    budget: int = Field(default=150, ge=50, le=500)
    max_distance: int = Field(default=10, ge=1, le=60)
    category: str = "不限"
    weather: str = "普通"
    mood: str = "省錢"
    meal_time: str = "午餐"
    need_takeout: Literal["不限", "yes", "no"] = "不限"
    max_spicy_level: int = Field(default=2, ge=0, le=5)
    prefer_fast: bool = False
    sort_by: str = "綜合推薦"
    min_rating: float = Field(default=0, ge=0, le=5)
    top_n: int = Field(default=5, ge=1, le=10)
    use_review_analysis: bool = True
    review_weight: int = Field(default=60, ge=0, le=100)
    max_negative_ratio: int = Field(default=60, ge=0, le=100)
    hide_high_risk: bool = False
    latitude: float | None = None
    longitude: float | None = None


class IngredientState(BaseModel):
    name: str = Field(min_length=1, max_length=40)
    days_stored: int = Field(default=1, ge=0, le=365)
    shelf_life: int = Field(default=7, ge=1, le=365)
    price: float = Field(default=40, ge=0, le=5000)
    perishability: Literal["低", "中", "高"] = "中"


class RecipeRequest(BaseModel):
    scenario: str = "清冰箱減浪費"
    smart_mode: str = "清冰箱模式"
    ingredients: list[IngredientState]
    max_time: int = Field(default=40, ge=5, le=180)
    difficulty: str = "不限"
    max_calories: int = Field(default=750, ge=100, le=2000)
    max_missing: int = Field(default=2, ge=0, le=10)
    only_cookable: bool = False
    top_n: int = Field(default=5, ge=1, le=10)


@app.get("/api/health")
def health():
    return {"status": "ok", "version": app.version}


@app.get("/api/options")
def options():
    return {"restaurants": restaurant_options(), "recipes": recipe_options()}


@app.get("/api/weather")
def weather(location: str = "Xitun District, Taichung, Taiwan"):
    return fetch_current_weather(location)


@app.post("/api/recommend/restaurants")
def restaurant_recommendations(payload: RestaurantRequest):
    return recommend_restaurant_payload(payload)


@app.post("/api/recommend/recipes")
def recipe_recommendations(payload: RecipeRequest):
    return recommend_recipe_payload(payload)


FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="frontend-assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_frontend(full_path: str):
        requested_file = FRONTEND_DIST / full_path
        if full_path and requested_file.is_file():
            return FileResponse(requested_file)
        return FileResponse(FRONTEND_DIST / "index.html")
