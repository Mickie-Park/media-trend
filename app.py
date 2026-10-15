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
st.markdown("""
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
        font-size: 1.2
