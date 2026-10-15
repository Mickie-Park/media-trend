import os
import glob
import re
import json
import hashlib
import base64
import requests
from datetime import datetime, timezone, timedelta
import pandas as pd
import streamlit as st
import plotly.express as px
import google.generativeai as genai

# --- 1. 기본 설정 및 데이터 디렉토리 ---
st.set_page_config(page_title="월간 업계 동향 통합 인텔리전스", layout="wide", page_icon="🏛️")

DATA_DIR = "./data"
USER_DB_FILE = "users.json"
LOG_DB_FILE = "activity_logs.json"
MASTER_SALES_FILE = "sales_master.xlsx"
os.makedirs(DATA_DIR, exist_ok=True)

# GitHub API 연동 설정
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", None)
GITHUB_REPO = st.secrets.get("GITHUB_REPO", "Mickie-Park/media-trend")
FILE_PATH = "users.json"
LOG_FILE_PATH = "activity_logs.json"

# 텔레그램 알림 설정
TELEGRAM_BOT_TOKEN = st.secrets.get("TELEGRAM_BOT_TOKEN", None)
TELEGRAM_CHAT_ID = st.secrets.get("TELEGRAM_CHAT_ID", None)

def send_telegram_alert(name, user_id):
    """신규 회원가입 승인 요청 시 관리자 텔레그램으로 실시간 푸시 전송"""
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        now_str = get_now_kst().strftime("%Y-%m-%d %H:%M:%S")
        msg = (
            f"🔔 [월간 미디어 동향] 신규 회원가입 승인 요청\n"
            f"• 이름: {name}\n"
            f"• 아이디: {user_id}\n"
            f"• 신청일시: {now_str}\n\n"
            f"👉 관리자 콘솔에서 가입 승인을 진행해 주세요."
        )
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg}, timeout=5)
        except Exception:
            pass

# --- 2. CSS 스타일링 ---
st.markdown(
    """
    <style>
    @import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap");
    @import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css");

    html, body, [class*="css"], .stMarkdown, .stText, .stTextInput, .stSelectbox {
        font-family: "Inter", "Pretendard Variable", Pretendard, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        font-feature-settings: "cv02", "cv03", "cv04", "cv11", "tnum" !important;
        letter-spacing: -0.015em;
        font-size: 0.90rem !important;
    }

    .stApp {
        background-color: #FFFFFF !important;
        color: #1E293B !important;
    }

    [data-testid="stVerticalBlockBorderWrapper"],
    [data-testid="stVerticalBlockBorderWrapper"] > div {
        background-color: #FFFFFF !important;
        border-color: #E2E8F0 !important;
        border-radius: 8px !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04) !important;
    }

    .block-container {
        padding-top: 1.8rem !important;
        padding-bottom: 3rem !important;
    }

    div[data-testid="stRadio"] > div[role="radiogroup"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: wrap !important;
        gap: 12px !important;
        padding: 4px 0 14px 0 !important;
        align-items: center !important;
    }

    div[data-testid="stRadio"] div[role="radiogroup"] label {
        display: inline-flex !important;
        align-items: center !important;
        gap: 8px !important;
        cursor: pointer !important;
        margin: 0 !important;
        padding: 7px 18px !important;
        border-radius: 24px !important;
        background-color: #F8FAFC !important;
        border: 1.5px solid #CBD5E1 !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04) !important;
        transition: all 0.18s ease-in-out !important;
    }

    div[data-testid="stRadio"] div[role="radiogroup"] label:hover {
        background-color: #F1F5F9 !important;
        border-color: #94A3B8 !important;
    }

    div[data-testid="stRadio"] div[role="radiogroup"] label [data-testid="stMarkdownContainer"] p {
        color: #475569 !important;
        font-weight: 600 !important;
        font-size: 0.86rem !important;
        margin: 0 !important;
    }

    div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) {
        background-color: #EFF6FF !important;
        border: 1.5px solid #1E3A8A !important;
        box-shadow: 0 2px 6px rgba(30, 58, 138, 0.14) !important;
    }

    div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) [data-testid="stMarkdownContainer"] p {
        color: #1E3A8A !important;
        font-weight: 700 !important;
    }

    .stApp div[data-testid="stTextInput"] input {
        background-color: #FFFFFF !important;
        border: 1.5px solid #93C5FD !important;
        border-radius: 6px !important;
        font-size: 0.88rem !important;
        min-height: 42px !important;
        padding-left: 14px !important;
        color: #0F172A !important;
        box-shadow: 0 1px 2px rgba(59, 130, 246, 0.05) !important;
        transition: all 0.2s ease !important;
    }

    .stApp div[data-testid="stTextInput"] input:focus {
        border: 2px solid #2563EB !important;
        box-shadow: 0 0 0 3.5px rgba(37, 99, 235, 0.15) !important;
        outline: none !important;
    }

    .ai-report-box h1 {
        font-size: 1.25rem !important;
        font-weight: 800 !important;
        color: #0F172A !important;
        margin-top: 1.2rem !important;
        margin-bottom: 0.6rem !important;
        border-bottom: 1.5px solid #E2E8F0 !important;
        padding-bottom: 0.3rem !important;
    }
    .ai-report-box h2 {
        font-size: 1.10rem !important;
        font-weight: 700 !important;
        color: #1E293B !important;
        margin-top: 1.0rem !important;
        margin-bottom: 0.4rem !important;
    }
    .ai-report-box h3 {
        font-size: 0.98rem !important;
        font-weight: 700 !important;
        color: #1E3A8A !important;
        margin-top: 0.8rem !important;
        margin-bottom: 0.3rem !important;
    }
    .ai-report-box p, .ai-report-box li {
        font-size: 0.88rem !important;
        line-height: 1.60 !important;
        color: #334155 !important;
    }
    .ai-report-box strong {
        color: #0F172A !important;
        font-weight: 700 !important;
    }

    [data-testid="stMetric"] {
        background-color: #F8FAFC !important;
        padding: 14px 18px !important;
        border-radius: 6px !important;
        border: 1px solid #E2E8F0 !important;
        border-left: 3.5px solid #1E3A8A !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02) !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.74rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: #64748B !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.40rem !important;
        font-weight: 700 !important;
        color: #0F172A !important;
        letter-spacing: -0.02em;
    }

    [data-testid="stSidebar"] {
        background-color: #0C1A30 !important;
        border-right: 1px solid #1E2E4A !important;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] h4, [data-testid="stSidebar"] p, [data-testid="stSidebar"] label {
        color: #F8FAFC !important;
        font-size: 0.85rem !important;
    }
    [data-testid="stSidebar"] hr {
        border-color: #1E2E4A !important;
    }
    [data-testid="stSidebar"] .stCaption {
        color: #94A3B8 !important;
        font-size: 0.76rem !important;
    }

    [data-testid="stSidebar"] button,
    [data-testid="stSidebar"] .stButton button,
    [data-testid="stSidebar"] [data-testid="baseButton-primary"],
    [data-testid="stSidebar"] [data-testid="baseButton-secondary"],
    [data-testid="stSidebar"] [data-testid="stBaseButton-secondary"],
    [data-testid="stSidebar"] [data-testid="stBaseButton-primary"] {
        background-color: #1E3A8A !important;
        border: 1px solid #3B82F6 !important;
        border-radius: 5px !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.25) !important;
        height: 38px !important;
    }

    [data-testid="stSidebar"] button div,
    [data-testid="stSidebar"] button p,
    [data-testid="stSidebar"] button span,
    [data-testid="stSidebar"] button [data-testid="stMarkdownContainer"] p {
        color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: 0.84rem !important;
        background: transparent !important;
        opacity: 1 !important;
        visibility: visible !important;
    }

    [data-testid="stSidebar"] button:hover {
        background-color: #2563EB !important;
        border-color: #60A5FA !important;
    }

    [data-testid="stSidebar"] [data-testid="stFileUploader"] {
        background-color: transparent !important;
    }
    [data-testid="stSidebar"] [data-testid="stFileUploader"] section {
        background-color: #13213B !important;
        border: 1.5px dashed #3B82F6 !important;
        border-radius: 6px !important;
        padding: 12px !important;
    }
    [data-testid="stSidebar"] [data-testid="stFileUploader"] button,
    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button,
    [data-testid="stSidebar"] [data-testid="stFileUploader"] [data-testid="stBaseButton-secondary"] {
        background-color: #1E3A8A !important;
        border: 1px solid #3B82F6 !important;
        color: #FFFFFF !important;
        height: 32px !important;
    }
    [data-testid="stSidebar"] [data-testid="stFileUploader"] button * {
        color: #FFFFFF !important;
        font-weight: 600 !important;
        font-size: 0.78rem !important;
        background: transparent !important;
    }
    [data-testid="stSidebar"] small, [data-testid="stSidebar"] span {
        color: #94A3B8 !important;
        font-size: 0.76rem !important;
        background: transparent !important;
    }

    [data-testid="stSidebar"] [data-testid="stExpander"] {
        background-color: #13213B !important;
        border: 1px solid #243656 !important;
        border-radius: 6px !important;
        overflow: hidden !important;
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] summary {
        background-color: #13213B !important;
        color: #F8FAFC !important;
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] summary:hover {
        background-color: #1A2C4E !important;
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] summary svg {
        fill: #93C5FD !important;
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] [data-testid="stExpanderDetails"] {
        background-color: #0E1A2E !important;
        border-top: 1px solid #243656 !important;
        padding: 12px !important;
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] * {
        color: #F8FAFC !important;
        font-size: 0.84rem !important;
    }

    [data-testid="stSidebar"] code {
        background-color: #1E2E4A !important;
        color: #93C5FD !important;
        border: 1px solid #2D4165 !important;
        border-radius: 4px !important;
        padding: 1px 5px !important;
    }

    [data-testid="stSidebar"] input {
        background-color: #0C1A30 !important;
        border: 1px solid #2D4165 !important;
        color: #FFFFFF !important;
        border-radius: 4px !important;
        font-size: 0.84rem !important;
        height: 34px !important;
    }

    div[data-baseweb="select"] > div {
        border-color: #CBD5E1 !important;
        border-radius: 4px !important;
        background-color: #FFFFFF !important;
        font-size: 0.88rem !important;
        min-height: 38px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

def get_github_headers():
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

def get_now_kst():
    kst = timezone(timedelta(hours=9))
    return datetime.now(kst)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def is_user_approved(val):
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.strip().lower() in ["true", "1", "t", "y", "yes"]
    if isinstance(val, (int, float)):
        return val == 1
    return False

# 회원 DB 로드
def load_users():
    default_admin = {
        "admin": {
            "name": "마스터 관리자",
            "password": hash_password("admin1234"),
            "role": "admin",
            "approved": True
        }
    }
    
    if not GITHUB_TOKEN:
        if os.path.exists(USER_DB_FILE):
            try:
                with open(USER_DB_FILE, "r", encoding="utf-8") as f:
                    u = json.load(f)
                    if u: return u
            except Exception:
                pass
        save_users(default_admin)
        return default_admin
            
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{FILE_PATH}"
    try:
        res = requests.get(url, headers=get_github_headers())
        if res.status_code == 200:
            content = res.json().get("content", "")
            decoded = base64.b64decode(content).decode("utf-8")
            users = json.loads(decoded)
            if users:
                with open(USER_DB_FILE, "w", encoding="utf-8") as f:
                    json.dump(users, f, ensure_ascii=False, indent=4)
                return users
    except Exception:
        pass

    save_users(default_admin)
    return default_admin

# 회원 DB 저장
def save_users(users_dict):
    with open(USER_DB_FILE, "w", encoding="utf-8") as f:
        json.dump(users_dict, f, ensure_ascii=False, indent=4)
        
    if not GITHUB_TOKEN:
        return False

    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{FILE_PATH}"
    headers = get_github_headers()
    try:
        res = requests.get(url, headers=headers)
        sha = None
        if res.status_code == 200:
            sha = res.json().get("sha")
            
        raw_content = json.dumps(users_dict, ensure_ascii=False, indent=4)
        b64_content = base64.b64encode(raw_content.encode("utf-8")).decode("utf-8")
        
        payload = {
            "message": "Update users database via Streamlit",
            "content": b64_content
        }
        if sha:
            payload["sha"] = sha
            
        put_res = requests.put(url, headers=headers, json=payload)
        return put_res.status_code in [200, 201]
    except Exception:
        return False

# 활동 로그 GitHub 기반 로드
def load_raw_activity_logs():
    if GITHUB_TOKEN:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{LOG_FILE_PATH}"
        try:
            res = requests.get(url, headers=get_github_headers())
            if res.status_code == 200:
                content = res.json().get("content", "")
                decoded = base64.b64decode(content).decode("utf-8")
                logs = json.loads(decoded)
                with open(LOG_DB_FILE, "w", encoding="utf-8") as f:
                    json.dump(logs, f, ensure_ascii=False, indent=4)
                return logs
        except Exception:
            pass

    if os.path.exists(LOG_DB_FILE):
        try:
            with open(LOG_DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

# 활동 로그 GitHub 기반 영구 저장
def log_activity(username, user_name, action, details=""):
    now = get_now_kst()
    timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")
    
    logs = load_raw_activity_logs()
    logs.append({
        "timestamp": timestamp_str,
        "username": str(username) if username else "unknown",
        "name": str(user_name) if user_name else "unknown",
        "action": str(action),
        "details": str(details)
