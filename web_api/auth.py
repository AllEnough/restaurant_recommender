from __future__ import annotations

import base64
import hashlib
import os
import re
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field


ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = Path(os.getenv("APP_DB_PATH", ROOT / "data" / "app.db"))
SESSION_COOKIE = "food_decision_session"
SESSION_DAYS = 7
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

router = APIRouter(prefix="/api/auth", tags=["auth"])
favorite_router = APIRouter(prefix="/api/favorites", tags=["favorites"])


class RegisterRequest(BaseModel):
    display_name: str = Field(min_length=2, max_length=30)
    email: str = Field(min_length=5, max_length=120)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=120)
    password: str = Field(min_length=8, max_length=128)


class FavoriteRequest(BaseModel):
    kind: str = Field(pattern="^(restaurant|recipe)$")
    item_name: str = Field(min_length=1, max_length=120)


def connect() -> sqlite3.Connection:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_database() -> None:
    with connect() as database:
        database.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                display_name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                kind TEXT NOT NULL CHECK(kind IN ('restaurant', 'recipe')),
                item_name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(user_id, kind, item_name)
            );
            """
        )


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=32)
    return "scrypt$16384$8$1$" + base64.b64encode(salt).decode() + "$" + base64.b64encode(digest).decode()


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, n, r, p, salt_text, digest_text = encoded.split("$")
        if algorithm != "scrypt":
            return False
        salt = base64.b64decode(salt_text)
        expected = base64.b64decode(digest_text)
        actual = hashlib.scrypt(
            password.encode("utf-8"), salt=salt, n=int(n), r=int(r), p=int(p), dklen=len(expected)
        )
        return secrets.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def normalize_email(email: str) -> str:
    value = email.strip().lower()
    if not EMAIL_PATTERN.match(value):
        raise HTTPException(status_code=422, detail="Email 格式不正確")
    return value


def public_user(row: sqlite3.Row) -> dict:
    return {"id": row["id"], "email": row["email"], "display_name": row["display_name"]}


def create_session(database: sqlite3.Connection, user_id: int, response: Response) -> None:
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    now = utc_now()
    expires = now + timedelta(days=SESSION_DAYS)
    database.execute(
        "INSERT INTO sessions(token_hash, user_id, expires_at, created_at) VALUES (?, ?, ?, ?)",
        (token_hash, user_id, expires.isoformat(), now.isoformat()),
    )
    response.set_cookie(
        SESSION_COOKIE,
        raw_token,
        max_age=SESSION_DAYS * 86400,
        httponly=True,
        secure=os.getenv("APP_SECURE_COOKIE", "0") == "1",
        samesite="lax",
        path="/",
    )


def current_user(food_decision_session: str | None = Cookie(default=None)) -> dict:
    if not food_decision_session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="請先登入")
    token_hash = hashlib.sha256(food_decision_session.encode()).hexdigest()
    with connect() as database:
        row = database.execute(
            """
            SELECT users.id, users.email, users.display_name, sessions.expires_at
            FROM sessions JOIN users ON users.id = sessions.user_id
            WHERE sessions.token_hash = ?
            """,
            (token_hash,),
        ).fetchone()
        if not row or datetime.fromisoformat(row["expires_at"]) <= utc_now():
            database.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash,))
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登入已失效")
        return public_user(row)


@router.post("/register", status_code=201)
def register(payload: RegisterRequest, response: Response):
    email = normalize_email(payload.email)
    with connect() as database:
        try:
            cursor = database.execute(
                "INSERT INTO users(email, display_name, password_hash, created_at) VALUES (?, ?, ?, ?)",
                (email, payload.display_name.strip(), hash_password(payload.password), utc_now().isoformat()),
            )
        except sqlite3.IntegrityError as error:
            raise HTTPException(status_code=409, detail="此 Email 已經註冊") from error
        create_session(database, cursor.lastrowid, response)
        row = database.execute("SELECT * FROM users WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return {"user": public_user(row)}


@router.post("/login")
def login(payload: LoginRequest, response: Response):
    email = normalize_email(payload.email)
    with connect() as database:
        row = database.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if not row or not verify_password(payload.password, row["password_hash"]):
            raise HTTPException(status_code=401, detail="Email 或密碼錯誤")
        database.execute("DELETE FROM sessions WHERE user_id = ?", (row["id"],))
        create_session(database, row["id"], response)
        return {"user": public_user(row)}


@router.post("/logout", status_code=204)
def logout(response: Response, food_decision_session: str | None = Cookie(default=None)):
    if food_decision_session:
        token_hash = hashlib.sha256(food_decision_session.encode()).hexdigest()
        with connect() as database:
            database.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash,))
    response.delete_cookie(SESSION_COOKIE, path="/")


@router.get("/me")
def me(user: dict = Depends(current_user)):
    return {"user": user}


@favorite_router.get("")
def list_favorites(user: dict = Depends(current_user)):
    with connect() as database:
        rows = database.execute(
            "SELECT kind, item_name, created_at FROM favorites WHERE user_id = ? ORDER BY created_at DESC",
            (user["id"],),
        ).fetchall()
    return {"favorites": [dict(row) for row in rows]}


@favorite_router.post("", status_code=201)
def add_favorite(payload: FavoriteRequest, user: dict = Depends(current_user)):
    with connect() as database:
        database.execute(
            "INSERT OR IGNORE INTO favorites(user_id, kind, item_name, created_at) VALUES (?, ?, ?, ?)",
            (user["id"], payload.kind, payload.item_name.strip(), utc_now().isoformat()),
        )
    return {"saved": True}


@favorite_router.delete("/{kind}/{item_name}", status_code=204)
def remove_favorite(kind: str, item_name: str, user: dict = Depends(current_user)):
    if kind not in {"restaurant", "recipe"}:
        raise HTTPException(status_code=422, detail="收藏類型不正確")
    with connect() as database:
        database.execute(
            "DELETE FROM favorites WHERE user_id = ? AND kind = ? AND item_name = ?",
            (user["id"], kind, item_name),
        )


init_database()
