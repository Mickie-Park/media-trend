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

# GitHub API 연동 설정 (media-trend)
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

    /* 사이드바 st.expander 스타일 */
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

    /* 사이드바 인라인 코드(code) 배경 및 글자색 보정 */
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
""", unsafe_allow_html=True)

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
    })
    
    if len(logs) > 1500:
        logs = logs[-1500:]
        
    with open(LOG_DB_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=4)

    if GITHUB_TOKEN:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{LOG_FILE_PATH}"
        headers = get_github_headers()
        try:
            res = requests.get(url, headers=headers)
            sha = None
            if res.status_code == 200:
                sha = res.json().get("sha")
            raw_c = json.dumps(logs, ensure_ascii=False, indent=4)
            b64_c = base64.b64encode(raw_c.encode("utf-8")).decode("utf-8")
            payload = {
                "message": f"Audit Log: {action} by {username} [skip ci]",
                "content": b64_c
            }
            if sha:
                payload["sha"] = sha
            requests.put(url, headers=headers, json=payload)
        except Exception:
            pass

def load_activity_logs():
    logs = load_raw_activity_logs()
    if logs:
        df_l = pd.DataFrame(logs)
        if not df_l.empty:
            df_l = df_l.rename(columns={
                "timestamp": "일시",
                "username": "아이디",
                "name": "이름",
                "action": "활동 구분",
                "details": "상세 내역"
            })
            return df_l.sort_values(by="일시", ascending=False)
    return pd.DataFrame(columns=["일시", "아이디", "이름", "활동 구분", "상세 내역"])

users_db = load_users()

# 세션 상태 초기화
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["username"] = None
    st.session_state["role"] = None
    st.session_state["user_name"] = None
    st.session_state["login_time"] = None
    st.session_state["admin_view"] = False

# URL 파라미터 자동 로그인 체크 (정상 승인 회원인 경우에만)
auth_token = st.query_params.get("user", None)
if auth_token and not st.session_state["logged_in"]:
    users_current = load_users()
    if auth_token in users_current and is_user_approved(users_current[auth_token].get("approved", False)):
        st.session_state["logged_in"] = True
        st.session_state["username"] = auth_token
        st.session_state["role"] = users_current[auth_token].get("role", "member")
        st.session_state["user_name"] = users_current[auth_token].get("name", auth_token)
        st.session_state["login_time"] = get_now_kst()

# =========================================================================
# 4. [로그인 화면 및 권한 게이트] 미로그인 시 본문 100% 원천 차단
# =========================================================================
if not st.session_state["logged_in"]:
    st.markdown("""
    <div style="padding: 20px 0 16px 0; border-bottom: 2px solid #1E3A8A; margin-bottom: 18px;">
        <span style="font-size: 0.70rem; font-weight: 700; letter-spacing: 0.08em; color: #B45309; background: #FEF3C7; padding: 3px 8px; border-radius: 4px; border: 1px solid #FDE68A;">INTERNAL ACCESS ONLY</span>
        <h1 style="font-size: 1.50rem; font-weight: 700; color: #0F172A; margin: 8px 0 4px 0; letter-spacing: -0.02em;">월간 미디어·광고 인텔리전스 리포트</h1>
        <p style="font-size: 0.85rem; color: #64748B; margin: 0;">사내 인가된 임직원 전용 시스템입니다. 등록된 계정으로 로그인해 주세요.</p>
    </div>
    """, unsafe_allow_html=True)
    
    login_tab, signup_tab = st.tabs(["로그인", "회원가입 신청"])
    
    with login_tab:
        with st.form("login_form"):
            login_id = st.text_input("아이디").strip()
            login_pw = st.text_input("비밀번호", type="password")
            submit_login = st.form_submit_button("로그인", type="primary")
            
            if submit_login:
                users_current = load_users()
                if login_id in users_current:
                    user_info = users_current[login_id]
                    if user_info["password"] == hash_password(login_pw):
                        if is_user_approved(user_info.get("approved", False)):
                            st.session_state["logged_in"] = True
                            st.session_state["username"] = login_id
                            st.session_state["role"] = user_info.get("role", "member")
                            st.session_state["user_name"] = user_info.get("name", login_id)
                            st.session_state["login_time"] = get_now_kst()
                            st.query_params["user"] = login_id
                            log_activity(login_id, st.session_state["user_name"], "로그인", "시스템 로그인 성공")
                            st.rerun()
                        else:
                            st.warning("관리자 승인 대기 중입니다. 관리자의 승인 완료 후 이용하실 수 있습니다.")
                    else:
                        st.error("비밀번호가 올바르지 않습니다.")
                else:
                    st.error("등록되지 않은 사용자 아이디입니다.")

    with signup_tab:
        with st.form("signup_form"):
            new_id = st.text_input("희망 아이디 (영문/숫자)").strip()
            new_name = st.text_input("이름 (실명 입력)")
            new_pw = st.text_input("비밀번호", type="password")
            new_pw_confirm = st.text_input("비밀번호 확인", type="password")
            submit_signup = st.form_submit_button("가입 신청하기")
            
            if submit_signup:
                users_current = load_users()
                if not new_id or not new_name or not new_pw:
                    st.error("모든 항목을 입력해 주세요.")
                elif new_id in users_current:
                    st.error("이미 사용 중인 아이디입니다. 다른 아이디를 입력해 주세요.")
                elif new_pw != new_pw_confirm:
                    st.error("비밀번호 확인이 일치하지 않습니다.")
                else:
                    users_current[new_id] = {
                        "name": new_name,
                        "password": hash_password(new_pw),
                        "role": "member",
                        "approved": False
                    }
                    save_users(users_current)
                    log_activity(new_id, new_name, "회원가입 신청", f"아이디 '{new_id}' 가입 신청")
                    send_telegram_alert(new_name, new_id)
                    st.success("회원가입 신청이 완료되었습니다. 관리자 승인 후 로그인하실 수 있습니다.")
    
    st.stop()

# =========================================================================
# 5. [인증 완료 사용자 전용] 데이터 로드 및 사이드바 제어판
# =========================================================================

@st.cache_data(show_spinner=False)
def load_all_data():
    raw_files = glob.glob("**/*.[xX][lL][sS][xX]", recursive=True)
    monthly_report_files = []
    for f in raw_files:
        filename = os.path.basename(f)
        if filename.startswith("~$") or "sales_master" in filename:
            continue
        if "업계동향" in filename or "data" in f.lower():
            monthly_report_files.append(f)
            
    def get_file_ym_score(filepath):
        m = re.search(r'(\d{4})(\d{2})', filepath)
        return int(m.group(1) + m.group(2)) if m else 0
        
    monthly_report_files = sorted(list(set(monthly_report_files)), key=get_file_ym_score, reverse=True)
    
    issues_list = []
    pt_list = []

    def clean_str(val):
        if pd.isna(val): return ""
        v = str(val).strip()
        if v.lower() in ["nan", "none", "-"]: return ""
        return v

    for f in monthly_report_files:
        m = re.search(r'(\d{4})(\d{2})', f)
        ym = f"{m.group(1)}-{m.group(2)}" if m else "기타"
        year_str = m.group(1) if m else "기타"
        
        try:
            xls = pd.ExcelFile(f)
            df = pd.read_excel(f, sheet_name=xls.sheet_names[0])
            
            # --- [이슈 파싱 로직 개선: 작은따옴표('), 별표(*), 기타 불릿 기호 완벽 지원] ---
            current_issue = ""
            for r_idx in range(len(df)):
                row_vals = [clean_str(df.iloc[r_idx, c]) for c in range(min(3, len(df.columns)))]
                text = " ".join([v for v in row_vals if v]).strip()
                
                if not text:
                    continue
                    
                # PT 테이블 시작 지점에 도달하면 이슈 영역 종료
                if "광고회사 PT" in text or ("PT일자" in text and "광고주" in text):
                    break

                # 엑셀의 문자열 강제 접두사인 작은따옴표(') 및 큰따옴표(") 제거
                clean_text = text.lstrip("'\":").strip()
                if not clean_text:
                    continue

                # 헤드라인 감지: *, ★, ■, ▶, ◆, ● 등
                is_headline = False
                headline_text = ""
                for sym in ["*", "★", "■", "▶", "◆", "●"]:
                    if clean_text.startswith(sym):
                        is_headline = True
                        headline_text = clean_text.lstrip(sym).strip()
                        break
                        
                if not is_headline:
                    # 숫자 넘버링 헤드라인 감지 (예: 1. 2024년 정책 동향...)
                    num_match = re.match(r'^(\d+[\.\)]\s*)(.+)', clean_text)
                    if num_match and len(clean_text) > 5 and not any(k in clean_text for k in ["PT일자", "빌링", "광고주", "단위"]):
                        is_headline = True
                        headline_text = num_match.group(2).strip()

                if is_headline and headline_text:
                    current_issue = headline_text
                    issues_list.append({"연월": ym, "헤드라인": current_issue, "상세": ""})
                elif current_issue:
                    # 서브 불릿 감지: -, ·, •, ㅇ, *, ↳ 등
                    is_sub = False
                    sub_text = ""
                    for sub_sym in ["-", "·", "•", "ㅇ", "*", "↳"]:
                        if clean_text.startswith(sub_sym):
                            is_sub = True
                            sub_text = clean_text.lstrip(sub_sym).strip()
                            break
                    if is_sub and sub_text:
                        issues_list.append({"연월": ym, "헤드라인": current_issue, "상세": sub_text})
            
            # --- [경쟁 PT 파싱 로직] ---
            for p_idx in range(len(df)):
                row_cells = [clean_str(x) for x in df.iloc[p_idx].tolist()]
                row_text_no_space = "".join(row_cells).replace(" ", "")
                
                if "PT일자" in row_text_no_space and "광고주" in row_text_no_space:
                    col_map = {
                        "date": 0, "client": 1, "product": 2, "billing": 3,
                        "participants": 4, "incumbent": 6, "winner": 7, "memo": 8
                    }
                    
                    for c_i, c_val in enumerate(row_cells):
                        c_clean = c_val.replace(" ", "").replace("\n", "")
                        if "일자" in c_clean: col_map["date"] = c_i
                        elif "광고주" in c_clean: col_map["client"] = c_i
                        elif "품목" in c_clean or "과제" in c_clean: col_map["product"] = c_i
                        elif "빌링" in c_clean or "규모" in c_clean: col_map["billing"] = c_i
                        elif "참여사" in c_clean or "참여" in c_clean: col_map["participants"] = c_i
                        elif "기존사" in c_clean or "기존" in c_clean: col_map["incumbent"] = c_i
                        elif "선정사" in c_clean or "결과" in c_clean: col_map["winner"] = c_i
                        elif "비고" in c_clean or "메모" in c_clean: col_map["memo"] = c_i

                    for r_i in range(p_idx + 1, len(df)):
                        sub_row = df.iloc[r_i].tolist()
                        row_full_str = " ".join([clean_str(x) for x in sub_row])
                        row_full_nospace = row_full_str.replace(" ", "")
                        
                        if any(stop_kw in row_full_nospace for stop_kw in ["전파", "지상파", "종편", "방송사매출", "매출_", "공중파"]):
                            break
                        if "PT일자" in row_full_nospace and "광고주" in row_full_nospace:
                            break
                        
                        client_val = clean_str(sub_row[col_map["client"]]) if col_map["client"] < len(sub_row) else ""
                        date_cell = sub_row[col_map["date"]] if col_map["date"] < len(sub_row) else ""
                        
                        if not client_val or client_val in ["광고주", "합계", "소계", "Total", "SUM"]:
                            continue
                        if any(junk_kw in client_val for junk_kw in ["광고회사", "종합편", "단위", "합산", "계수", "WPP Media", "Group M"]):
                            continue

                        date_str = ""
                        if pd.notna(date_cell):
                            if isinstance(date_cell, (datetime, pd.Timestamp)):
                                date_str = date_cell.strftime("%Y-%m-%d")
                            else:
                                date_str = clean_str(date_cell)
                                if len(date_str) >= 10 and date_str[:10].replace("-", "").isdigit():
                                    date_str = date_str[:10]

                        if not date_str or date_str.isdigit() or any(k in date_str for k in ["SUM", "단위", "WPP"]):
                            continue

                        excluded_agencies = ["TBWA", "SM C&C", "HS AD", "차이커뮤니케이션", "제일기획", "이노션", "대홍기획", "Dentsu", "덴츠"]
                        if any(ag in date_str for ag in excluded_agencies) or any(ag in client_val for ag in excluded_agencies):
                            continue

                        pt_year = year_str
                        ymatch = re.search(r'(\d{4})', date_str)
                        if ymatch:
                            pt_year = ymatch.group(1)

                        billing_raw = clean_str(sub_row[col_map["billing"]]) if col_map["billing"] < len(sub_row) else ""
                        billing_val = 0.0
                        b_match = re.search(r'(\d+)', billing_raw)
                        if b_match:
                            try:
                                billing_val = float(b_match.group(1))
                            except:
                                pass

                        product_val = clean_str(sub_row[col_map["product"]]) if col_map["product"] < len(sub_row) else ""
                        participants_val = clean_str(sub_row[col_map["participants"]]) if col_map["participants"] < len(sub_row) else ""
                        incumbent_val = clean_str(sub_row[col_map["incumbent"]]) if col_map["incumbent"] < len(sub_row) else ""
                        winner_val = clean_str(sub_row[col_map["winner"]]) if col_map["winner"] < len(sub_row) else ""
                        memo_val = clean_str(sub_row[col_map["memo"]]) if col_map["memo"] < len(sub_row) else ""

                        pt_list.append({
                            "발행연월": ym,
                            "연도": pt_year,
                            "PT일자": date_str,
                            "광고주": client_val,
                            "품목": product_val,
                            "빌링(억원)": billing_val,
                            "빌링_원문": billing_raw,
                            "기존사": incumbent_val,
                            "참여사": participants_val,
                            "선정사(결과)": winner_val,
                            "메모(비고)": memo_val
                        })
        except Exception as e:
            st.error(f"{f} 파싱 오류: {e}")

    df_agency = pd.DataFrame()
    df_tv = pd.DataFrame()

    if os.path.exists(MASTER_SALES_FILE):
        try:
            df_m = pd.read_excel(MASTER_SALES_FILE)
            df_m.columns = [str(c).strip() for c in df_m.columns]
            
            start_col_name = "Start(억원)" if "Start(억원)" in df_m.columns else "Start"
            close_col_name = "마감(억원)" if "마감(억원)" in df_m.columns else "마감"
            
            df_m["연월"] = df_m["연월"].astype(str).str.strip()
            df_m["연도"] = df_m["연월"].apply(lambda x: x.split("-")[0] if "-" in x else "")
            df_m["월"] = df_m["연월"].apply(lambda x: f"{int(x.split('-')[1])}월" if "-" in x and len(x.split('-')) > 1 and x.split('-')[1].isdigit() else "")

            # A. 대행사 데이터 분리
            df_m_ag = df_m[df_m["분류"] == "대행사"].copy()
            if not df_m_ag.empty:
                ag_records = []
                for _, r in df_m_ag.iterrows():
                    ag_name = str(r["회사/채널명"]).strip()
                    if pd.notna(r.get(start_col_name)) and float(r[start_col_name]) > 0:
                        ag_records.append({
                            "연월": r["연월"], "연도": r["연도"], "월": r["월"],
                            "대행사": ag_name, "구분": "Start", "매출(억원)": float(r[start_col_name])
                        })
                    if pd.notna(r.get(close_col_name)) and float(r[close_col_name]) > 0:
                        ag_records.append({
                            "연월": r["연월"], "연도": r["연도"], "월": r["월"],
                            "대행사": ag_name, "구분": "마감", "매출(억원)": float(r[close_col_name])
                        })
                df_agency = pd.DataFrame(ag_records)

            # B. 방송 매체사 데이터 분리
            df_m_tv = df_m[df_m["분류"].isin(["지상파", "종편/유선", "케이블", "종편"])].copy()
            if not df_m_tv.empty:
                tv_records = []
                for _, r in df_m_tv.iterrows():
                    ch_name = str(r["회사/채널명"]).strip()
                    c_type = "지상파" if r["분류"] == "지상파" else "종편/유선/PP"
                    if pd.notna(r.get(start_col_name)) and float(r[start_col_name]) > 0:
                        tv_records.append({
                            "연월": r["연월"], "연도": r["연도"], "월": r["월"],
                            "채널": ch_name, "채널구분": c_type, "구분": "Start", "매출(억원)": float(r[start_col_name])
                        })
                    if pd.notna(r.get(close_col_name)) and float(r[close_col_name]) > 0:
                        tv_records.append({
                            "연월": r["연월"], "연도": r["연도"], "월": r["월"],
                            "채널": ch_name, "채널구분": c_type, "구분": "마감", "매출(억원)": float(r[close_col_name])
                        })
                df_tv = pd.DataFrame(tv_records)
        except Exception as e:
            st.error(f"sales_master.xlsx 로드 오류: {e}")

    return pd.DataFrame(issues_list), df_tv, pd.DataFrame(pt_list), df_agency, monthly_report_files

df_issues, df_tv, df_pt, df_agency, loaded_files = load_all_data()

def normalize_match_key(text):
    if not text:
        return ""
    return re.sub(r'[\s\(\)\[\]_\-.,·/]', '', str(text)).lower()

if not df_pt.empty:
    df_pt["_dedup_key"] = (
        df_pt["PT일자"].astype(str).str.strip() + "||" +
        df_pt["광고주"].apply(normalize_match_key) + "||" +
        df_pt["품목"].apply(normalize_match_key)
    )
    df_pt_unique = df_pt.drop_duplicates(subset=["_dedup_key"], keep="first").drop(columns=["_dedup_key"])
else:
    df_pt_unique = pd.DataFrame()

def get_stay_duration_str():
    if st.session_state.get("login_time"):
        delta = get_now_kst() - st.session_state["login_time"]
        minutes = int(delta.total_seconds() // 60)
        seconds = int(delta.total_seconds() % 60)
        return f"{minutes}분 {seconds}초"
    return "집계 불가"

# 사이드바 메인 엠블럼 헤더
st.sidebar.markdown("""
<div style="background: linear-gradient(180deg, #13213B 0%, #0F1A2E 100%); border: 1px solid #1E2E4A; border-top: 3px solid #3B82F6; border-radius: 6px; padding: 14px 14px 12px 14px; margin-bottom: 12px; box-shadow: 0 2px 6px rgba(0,0,0,0.2);">
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
        <span style="font-size: 0.60rem; font-weight: 700; letter-spacing: 0.08em; color: #F59E0B; background: rgba(245, 158, 11, 0.12); padding: 2px 6px; border-radius: 3px; border: 1px solid rgba(245, 158, 11, 0.25);">STRATEGIC SUITE</span>
        <span style="display: inline-flex; align-items: center; gap: 4px; font-size: 0.65rem; color: #10B981; font-weight: 600;">
            <span style="display: inline-block; width: 5px; height: 5px; background-color: #10B981; border-radius: 50%;"></span>Live
        </span>
    </div>
    <div style="font-size: 1.02rem; font-weight: 800; color: #FFFFFF; line-height: 1.35; letter-spacing: -0.02em; margin-bottom: 4px;">
        월간 미디어·광고<br>업계 동향 대시보드
    </div>
    <div style="font-size: 0.70rem; color: #94A3B8; line-height: 1.35;">
        마스터 데이터 연동 인텔리전스
    </div>
</div>
""", unsafe_allow_html=True)

# 사이드바 사용자 프로필
st.sidebar.markdown(f"""
<div style="background-color: #13213B; border: 1px solid #243656; border-radius: 5px; padding: 12px; margin-bottom: 12px;">
    <div style="font-size: 0.68rem; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.06em; font-weight: 700;">USER PROFILE</div>
    <div style="font-size: 0.95rem; font-weight: 700; color: #FFFFFF; margin-top: 3px;">{st.session_state['user_name']}</div>
    <div style="font-size: 0.78rem; color: #60A5FA; margin-top: 2px;">Role: {st.session_state['role']}</div>
    <div style="font-size: 0.72rem; color: #94A3B8; margin-top: 5px; border-top: 1px solid #1E2E4A; padding-top: 5px;">체류 시간: {get_stay_duration_str()}</div>
</div>
""", unsafe_allow_html=True)

# 로그아웃 버튼
if st.sidebar.button("로그아웃", type="primary", use_container_width=True):
    log_activity(
        st.session_state["username"], 
        st.session_state["user_name"], 
        "로그아웃", 
        f"총 체류 시간: {get_stay_duration_str()}"
    )
    st.session_state["logged_in"] = False
    st.session_state["username"] = None
    st.session_state["role"] = None
    st.session_state["user_name"] = None
    st.session_state["login_time"] = None
    st.session_state["admin_view"] = False
    st.query_params.clear()
    st.rerun()

# 내 정보 관리
with st.sidebar.expander("내 정보 관리", expanded=False):
    with st.form("edit_profile_form"):
        curr_user_id = st.session_state["username"]
        users_current = load_users()
        my_info = users_current.get(curr_user_id, {})
        
        st.caption(f"아이디: **{curr_user_id}**")
        edit_name = st.text_input("이름(실명)", value=my_info.get("name", ""))
        curr_pw_input = st.text_input("현재 비밀번호 확인", type="password")
        new_pw_input = st.text_input("새 비밀번호 (변경 시)", type="password")
        new_pw_confirm = st.text_input("새 비밀번호 확인", type="password")
        
        save_profile_btn = st.form_submit_button("정보 저장")
        
        if save_profile_btn:
            if not curr_pw_input:
                st.error("현재 비밀번호를 입력해야 수정할 수 있습니다.")
            elif hash_password(curr_pw_input) != my_info.get("password"):
                st.error("현재 비밀번호가 일치하지 않습니다.")
            else:
                if new_pw_input:
                    if new_pw_input != new_pw_confirm:
                        st.error("새 비밀번호 확인이 일치하지 않습니다.")
                    else:
                        my_info["password"] = hash_password(new_pw_input)
                        my_info["name"] = edit_name
                        users_current[curr_user_id] = my_info
                        save_users(users_current)
                        st.session_state["user_name"] = edit_name
                        log_activity(curr_user_id, edit_name, "정보수정", "비밀번호 및 이름 변경")
                        st.rerun()
                else:
                    my_info["name"] = edit_name
                    users_current[curr_user_id] = my_info
                    save_users(users_current)
                    st.session_state["user_name"] = edit_name
                    log_activity(curr_user_id, edit_name, "정보수정", "이름 변경")
                    st.rerun()

st.sidebar.markdown("---")

api_key = st.secrets.get("GEMINI_API_KEY", None)
if not api_key:
    api_key = st.sidebar.text_input("Gemini API Key (선택)", type="password", help="API 키를 입력하면 AI 탭이 활성화됩니다.")
else:
    st.sidebar.caption("Gemini AI 연동 활성화됨")

# 관리자 콘솔 제어부
if st.session_state["role"] == "admin":
    st.sidebar.markdown("---")
    st.sidebar.markdown("<div style='font-size:0.72rem; color:#94A3B8; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:8px; font-weight:700;'>ADMIN CONSOLE</div>", unsafe_allow_html=True)
    
    if not st.session_state.get("admin_view", False):
        if st.sidebar.button("회원 관리 콘솔", type="primary", use_container_width
