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

    [data-testid="stSidebar"] [data-testid="stExpander"] {
        background-color: #13213B !important;
        border: 1px solid #243656 !important;
        border-radius: 5px !important;
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] * {
        color: #F8FAFC !important;
        font-size: 0.84rem !important;
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

def save_users(users_dict):
    with open(USER_DB_FILE, "w", encoding="utf-8") as f:
        json.dump(users_dict, f, ensure_ascii=False, indent=4)
        
    if not GITHUB_TOKEN:
        st.error("❌ Secrets에 GITHUB_TOKEN이 설정되지 않았습니다.")
        return False

    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{FILE_PATH}"
    headers = get_github_headers()
    try:
        res = requests.get(url, headers=headers)
        sha = None
        if res.status_code == 200:
            sha = res.json().get("sha")
        elif res.status_code != 404:
            st.error(f"❌ GitHub 파일 조회 실패 (상태코드 {res.status_code}): {res.text}")
            return False
            
        raw_content = json.dumps(users_dict, ensure_ascii=False, indent=4)
        b64_content = base64.b64encode(raw_content.encode("utf-8")).decode("utf-8")
        
        payload = {
            "message": "Update users database via Streamlit",
            "content": b64_content
        }
        if sha:
            payload["sha"] = sha
            
        put_res = requests.put(url, headers=headers, json=payload)
        if put_res.status_code in [200, 201]:
            st.toast("✅ GitHub 저장 완료!", icon="💾")
            return True
        else:
            st.error(f"❌ GitHub 저장 거절됨 [코드 {put_res.status_code}]: {put_res.json().get('message', put_res.text)}")
            return False
    except Exception as e:
        st.error(f"❌ GitHub 통신 예외 발생: {e}")
        return False

def log_activity(username, user_name, action, details=""):
    now = get_now_kst()
    timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")
    
    logs = []
    if os.path.exists(LOG_DB_FILE):
        try:
            with open(LOG_DB_FILE, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except Exception:
            logs = []
            
    logs.append({
        "timestamp": timestamp_str,
        "username": username,
        "name": user_name,
        "action": action,
        "details": details
    })
    
    if len(logs) > 1000:
        logs = logs[-1000:]
        
    try:
        with open(LOG_DB_FILE, "w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False, indent=4)
    except Exception:
        pass

def load_activity_logs():
    if not os.path.exists(LOG_DB_FILE):
        return pd.DataFrame(columns=["일시", "아이디", "이름", "활동 구분", "상세 내역"])
    try:
        with open(LOG_DB_FILE, "r", encoding="utf-8") as f:
            logs = json.load(f)
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
    except Exception:
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

auth_token = st.query_params.get("user", None)
if auth_token and not st.session_state["logged_in"]:
    users_current = load_users()
    if auth_token in users_current and is_user_approved(users_current[auth_token].get("approved", False)):
        st.session_state["logged_in"] = True
        st.session_state["username"] = auth_token
        st.session_state["role"] = users_current[auth_token].get("role", "member")
        st.session_state["user_name"] = users_current[auth_token].get("name", auth_token)
        st.session_state["login_time"] = get_now_kst()

# --- 3. [데이터 로드: sales_master.xlsx 기반 단일 진실 공급원 체계] ---
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
            
            current_issue = ""
            for idx, val in df['Unnamed: 0'].dropna().items():
                text = str(val).strip()
                if "광고회사 PT" in text:
                    break
                if text.startswith("★"):
                    current_issue = text.replace("★", "").strip()
                    issues_list.append({"연월": ym, "헤드라인": current_issue, "상세": ""})
                elif current_issue and text.startswith("-"):
                    issues_list.append({"연월": ym, "헤드라인": current_issue, "상세": text[1:].strip()})
            
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

# --- 5. 로그인 성공 후 사이드바 제어판 ---
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

# 사이드바 사용자 정보 카드
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

# 관리자 콘솔
if st.session_state["role"] == "admin":
    st.sidebar.markdown("---")
    st.sidebar.markdown("<div style='font-size:0.72rem; color:#94A3B8; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:8px; font-weight:700;'>ADMIN CONSOLE</div>", unsafe_allow_html=True)
    
    if not st.session_state.get("admin_view", False):
        if st.sidebar.button("회원 관리 콘솔", type="primary", use_container_width=True):
            st.session_state["admin_view"] = True
            st.rerun()
    else:
        if st.sidebar.button("메인 대시보드 복귀", type="primary", use_container_width=True):
            st.session_state["admin_view"] = False
            st.rerun()
            
    current_users_sb = load_users()
    pending_sb = {uid: info for uid, info in current_users_sb.items() if not is_user_approved(info.get("approved", False))}
    with st.sidebar.expander(f"빠른 회원 승인 ({len(pending_sb)}건 대기)", expanded=bool(pending_sb)):
        if pending_sb:
            for uid, info in pending_sb.items():
                st.write(f"**{info.get('name', uid)}** (`{uid}`)")
                sc_btn1, sc_btn2 = st.columns(2)
                if sc_btn1.button("승인", key=f"sb_app_{uid}", type="primary"):
                    current_users_sb[uid]["approved"] = True
                    save_users(current_users_sb)
                    log_activity(st.session_state["username"], st.session_state["user_name"], "회원 승인", f"승인: {uid}")
                    st.rerun()
                if sc_btn2.button("반려", key=f"sb_del_{uid}"):
                    del current_users_sb[uid]
                    save_users(current_users_sb)
                    log_activity(st.session_state["username"], st.session_state["user_name"], "회원 반려", f"반려: {uid}")
                    st.rerun()
        else:
            st.caption("현재 승인 대기자가 없습니다.")

    new_file = st.sidebar.file_uploader("엑셀 파일 업데이트 (.xlsx)", type=["xlsx"], help="sales_master.xlsx 또는 월간 엑셀을 업로드합니다.")
    if new_file is not None:
        if new_file.name == "sales_master.xlsx":
            save_path = "sales_master.xlsx"
        else:
            save_path = os.path.join(DATA_DIR, new_file.name)
        with open(save_path, "wb") as f:
            f.write(new_file.getbuffer())
        st.sidebar.success(f"{new_file.name} 저장 완료")
        log_activity(st.session_state["username"], st.session_state["user_name"], "엑셀 업로드", f"파일: {new_file.name}")
        st.cache_data.clear()
        st.rerun()

st.sidebar.markdown("---")
if os.path.exists(MASTER_SALES_FILE):
    st.sidebar.caption("✅ **sales_master.xlsx** 마스터 연동 중")
else:
    st.sidebar.warning("⚠️ sales_master.xlsx 미연동 상태")

# =========================================================================
# 6. [관리자 전용 페이지] 회원 관리 및 활동 로그
# =========================================================================
if st.session_state["role"] == "admin" and st.session_state.get("admin_view", False):
    c_head1, c_head2 = st.columns([4, 1])
    with c_head1:
        st.markdown("""
        <div style="padding: 4px 0 14px 0; border-bottom: 2px solid #1E3A8A; margin-bottom: 18px;">
            <span style="font-size: 0.70rem; font-weight: 700; letter-spacing: 0.08em; color: #B45309; background: #FEF3C7; padding: 3px 8px; border-radius: 4px; border: 1px solid #FDE68A;">EXECUTIVE ADMINISTRATION</span>
            <h2 style="font-size: 1.45rem; font-weight: 700; color: #0F172A; margin: 8px 0 4px 0; letter-spacing: -0.02em;">회원 인가 및 보안 감사 콘솔</h2>
            <p style="font-size: 0.85rem; color: #64748B; margin: 0;">가입 계정 인가 상태 및 사용자 활동 감사 내역을 정밀 모니터링합니다.</p>
        </div>
        """, unsafe_allow_html=True)
    with c_head2:
        st.write("")
        if st.button("대시보드로 돌아가기", type="primary", use_container_width=True):
            st.session_state["admin_view"] = False
            st.rerun()

    admin_tab1, admin_tab2 = st.tabs(["가입 회원 리스트 및 승인", "회원 방문 및 활동 로그"])
    
    with admin_tab1:
        all_users = load_users()
        pending_users_dict = {uid: info for uid, info in all_users.items() if not is_user_approved(info.get("approved", False))}
        
        u_m1, u_m2, u_m3 = st.columns(3)
        u_m1.metric("총 등록 계정", f"{len(all_users)}명")
        u_m2.metric("정상 인가 회원", f"{len(all_users) - len(pending_users_dict)}명")
        u_m3.metric("승인 대기 중", f"{len(pending_users_dict)}명")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### 승인 대기 신청 목록")
        if pending_users_dict:
            for uid, info in list(pending_users_dict.items()):
                with st.container():
                    p_col1, p_col2, p_col3 = st.columns([3, 1, 1])
                    with p_col1:
                        st.markdown(f"이름: **{info.get('name', uid)}** &nbsp;|&nbsp; 아이디: `{uid}` &nbsp;|&nbsp; 권한: `{info.get('role', 'member')}`")
                    with p_col2:
                        if st.button("승인하기", key=f"p_app_btn_{uid}", type="primary", use_container_width=True):
                            all_users[uid]["approved"] = True
                            save_users(all_users)
                            log_activity(st.session_state["username"], st.session_state["user_name"], "회원 승인", f"승인: {uid}")
                            st.rerun()
                    with p_col3:
                        if st.button("반려/삭제", key=f"p_del_btn_{uid}", use_container_width=True):
                            del all_users[uid]
                            save_users(all_users)
                            log_activity(st.session_state["username"], st.session_state["user_name"], "회원 반려", f"반려: {uid}")
                            st.rerun()
                    st.write("")
        else:
            st.info("현재 대기 중인 가입 신청이 없습니다.")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### 전체 계정 관리 대장")
        h_col1, h_col2, h_col3, h_col4, h_col5 = st.columns([1.5, 1.5, 1.5, 1.5, 2])
        h_col1.markdown("**아이디**")
        h_col2.markdown("**이름**")
        h_col3.markdown("**권한**")
        h_col4.markdown("**상태**")
        h_col5.markdown("**관리 조작**")
        st.markdown("<hr style='margin: 0.4rem 0; border-color: #E2E8F0;'>", unsafe_allow_html=True)

        for u_id, info in list(all_users.items()):
            r_col1, r_col2, r_col3, r_col4, r_col5 = st.columns([1.5, 1.5, 1.5, 1.5, 2])
            is_app = is_user_approved(info.get("approved", False))
            
            r_col1.write(f"`{u_id}`")
            r_col2.write(info.get("name", u_id))
            r_col3.write("관리자(admin)" if info.get("role") == "admin" else "일반회원(member)")
            r_col4.write("정상 인가" if is_app else "대기중")
            
            with r_col5:
                btn_c1, btn_c2 = st.columns(2)
                if not is_app:
                    if btn_c1.button("승인", key=f"grid_app_{u_id}", type="primary"):
                        all_users[u_id]["approved"] = True
                        save_users(all_users)
                        log_activity(st.session_state["username"], st.session_state["user_name"], "회원 승인", f"승인: {u_id}")
                        st.rerun()
                else:
                    if u_id != "admin" and u_id != st.session_state["username"]:
                        if btn_c1.button("대기전환", key=f"grid_unapp_{u_id}"):
                            all_users[u_id]["approved"] = False
                            save_users(all_users)
                            log_activity(st.session_state["username"], st.session_state["user_name"], "승인 취소", f"대기 전환: {u_id}")
                            st.rerun()
                            
                if u_id != "admin" and u_id != st.session_state["username"]:
                    if btn_c2.button("삭제", key=f"grid_del_{u_id}"):
                        del all_users[u_id]
                        save_users(all_users)
                        log_activity(st.session_state["username"], st.session_state["user_name"], "회원 삭제", f"삭제: {u_id}")
                        st.rerun()

    with admin_tab2:
        st.markdown("#### 시스템 접속 및 활동 감사 로그")
        df_logs = load_activity_logs()
        
        if not df_logs.empty:
            l_col1, l_col2, l_col3 = st.columns([2, 2, 2])
            with l_col1:
                user_list_for_log = ["전체 회원"] + sorted(df_logs["아이디"].unique().tolist())
                selected_log_user = st.selectbox("회원별 필터링", user_list_for_log)
            with l_col2:
                action_types = ["전체 활동"] + sorted(df_logs["활동 구분"].unique().tolist())
                selected_action = st.selectbox("활동 유형별 필터링", action_types)
            with l_col3:
                st.write("")
                st.write("")
                if st.button("감사 로그 전체 초기화", type="secondary"):
                    if os.path.exists(LOG_DB_FILE):
                        os.remove(LOG_DB_FILE)
                    st.rerun()

            view_logs = df_logs.copy()
            if selected_log_user != "전체 회원":
                view_logs = view_logs[view_logs["아이디"] == selected_log_user]
            if selected_action != "전체 활동":
                view_logs = view_logs[view_logs["활동 구분"] == selected_action]

            st.caption(f"조회 로그: **{len(view_logs)}건** / 전체 로그: **{len(df_logs)}건**")
            st.dataframe(view_logs, use_container_width=True, hide_index=True)
        else:
            st.info("기록된 활동 감사 로그가 없습니다.")

    st.stop()

# =========================================================================
# 7. [메인 화면] 메인 캔버스
# =========================================================================
search_container = st.container(border=True)
with search_container:
    st.markdown("""
    <h3 style="margin: 0 0 4px 0; font-size: 1.10rem; font-weight: 700; color: #0F172A;">🔍 전 카테고리 통합 실시간 검색</h3>
    <p style="margin: 0 0 12px 0; font-size: 0.82rem; color: #64748B;">키워드를 입력하면 모든 데이터(주요 이슈, 경쟁 PT, 대행사 및 매체사 매출)에서 즉시 찾아냅니다.</p>
    """, unsafe_allow_html=True)
    
    global_query = st.text_input(
        "통합 검색어 입력",
        placeholder="예: OTT, 현대, 제일기획, 카카오, 디즈니 등 입력 후 Enter",
        label_visibility="collapsed"
    ).strip()

    if global_query:
        matched_issues = pd.DataFrame()
        if not df_issues.empty:
            cond_issue = (
                df_issues["헤드라인"].str.contains(global_query, case=False, na=False) |
                df_issues["상세"].str.contains(global_query, case=False, na=False)
            )
            matched_issues = df_issues[cond_issue]
            
        matched_pt = pd.DataFrame()
        if not df_pt_unique.empty:
            cond_pt = (
                df_pt_unique["광고주"].str.contains(global_query, case=False, na=False) |
                df_pt_unique["품목"].str.contains(global_query, case=False, na=False) |
                df_pt_unique["기존사"].str.contains(global_query, case=False, na=False) |
                df_pt_unique["참여사"].str.contains(global_query, case=False, na=False) |
                df_pt_unique["선정사(결과)"].str.contains(global_query, case=False, na=False) |
                df_pt_unique["메모(비고)"].str.contains(global_query, case=False, na=False)
            )
            matched_pt = df_pt_unique[cond_pt]
            
        matched_agency = pd.DataFrame()
        if not df_agency.empty:
            matched_agency = df_agency[df_agency["대행사"].str.contains(global_query, case=False, na=False)]
            
        matched_tv = pd.DataFrame()
        if not df_tv.empty:
            matched_tv = df_tv[df_tv["채널"].str.contains(global_query, case=False, na=False)]

        tot_cnt = len(matched_issues) + len(matched_pt) + len(matched_agency) + len(matched_tv)
        st.info(f"검색 결과: 총 **{tot_cnt}건** 발견")
        
        sc1, sc2, sc3, sc4 = st.columns(4)
        sc1.metric("주요 이슈", f"{len(matched_issues)}건")
        sc2.metric("경쟁 PT 현황", f"{len(matched_pt)}건")
        sc3.metric("대행사 매출 데이터", f"{len(matched_agency)}건")
        sc4.metric("방송 매체사 데이터", f"{len(matched_tv)}건")
        
        if len(matched_issues) > 0:
            with st.expander(f"주요 이슈 검색 결과 ({len(matched_issues)}건)", expanded=True):
                for _, row in matched_issues.iterrows():
                    headline_text = f"**[{row['연월']}]** {row['헤드라인']}"
                    if row['상세']:
                        st.markdown(f"- {headline_text}<br>&nbsp;&nbsp;&nbsp;&nbsp;↳ *{row['상세']}*", unsafe_allow_html=True)
                    else:
                        st.markdown(f"- {headline_text}")

        if len(matched_pt) > 0:
            with st.expander(f"PT 수주 현황 검색 결과 ({len(matched_pt)}건)", expanded=True):
                st.dataframe(
                    matched_pt[["발행연월", "PT일자", "광고주", "품목", "빌링_원문", "기존사", "참여사", "선정사(결과)", "메모(비고)"]].rename(columns={"빌링_원문": "빌링(억원)"}),
                    hide_index=True,
                    use_container_width=True
                )

        if len(matched_agency) > 0 or len(matched_tv) > 0:
            with st.expander(f"대행사 / 매체사 관련 검색 결과 ({len(matched_agency) + len(matched_tv)}건)", expanded=False):
                if len(matched_agency) > 0:
                    st.caption("대행사 매출 데이터")
                    st.dataframe(matched_agency[["연월", "대행사", "매출(억원)", "구분"]], hide_index=True, use_container_width=True)
                if len(matched_tv) > 0:
                    st.caption("방송 매체사 매출 데이터")
                    st.dataframe(matched_tv[["연월", "채널구분", "채널", "매출(억원)", "구분"]], hide_index=True, use_container_width=True)

        if tot_cnt == 0:
            st.warning(f"'{global_query}'에 대한 검색 결과가 없습니다.")

# 카테고리 선택
categories = [
    "광고회사 PT 수주 현황", 
    "대행사/매체사 매출 동향", 
    "월별 핵심 이슈 브리핑", 
    "AI 동향 분석가"
]

selected_category = st.radio(
    "카테고리 선택", 
    options=categories, 
    horizontal=True, 
    label_visibility="collapsed"
)

# 메인 바디 컨테이너
body_container = st.container(border=True)
with body_container:
    # 탭 1: PT 수주 현황
    if selected_category == "광고회사 PT 수주 현황":
        st.markdown("<h3 style='font-size: 1.20rem; font-weight: 700; color: #0F172A; margin-bottom: 2px;'>광고회사 경쟁 PT 모니터링 및 수주 분석</h3>", unsafe_allow_html=True)
        st.caption("경쟁 PT 동향, 빌링 규모, 대행사별 수주 실적을 정밀 분석합니다.")
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        
        if not df_pt_unique.empty:
            available_years = sorted(list(set([str(y) for y in df_pt_unique["연도"].dropna() if str(y).isdigit()])), reverse=True)
            selected_pt_year = st.selectbox("PT 연도 선택", ["전체 연도"] + available_years)

            view_pt = df_pt_unique.copy()
            if selected_pt_year != "전체 연도":
                view_pt = view_pt[view_pt["연도"] == selected_pt_year]

            m1, m2, m3 = st.columns(3)
            m1.metric(f"PT 모니터링 건수 ({selected_pt_year})", f"{len(view_pt)}건")
            m2.metric("집계된 빌링 규모", f"{int(view_pt['빌링(억원)'].sum()):,}억원")
            avg_b = view_pt[view_pt['빌링(억원)'] > 0]['빌링(억원)'].mean()
            m3.metric("평균 프로젝트 빌링", f"{avg_b:.1f}억원" if pd.notna(avg_b) else "집계중")

            st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
            f_col1, f_col2, f_col3 = st.columns([2, 2, 2])
            with f_col1:
                search_query = st.text_input("광고주 또는 품목 검색", placeholder="예: 라이나, 카카오, 샴푸")
            with f_col2:
                max_b_val = int(df_pt_unique['빌링(억원)'].max()) if df_pt_unique['빌링(억원)'].max() > 0 else 100
                min_b = st.slider("최소 빌링 (억원)", 0, max_b_val, 0)
            with f_col3:
                winner_search = st.text_input("선정사(결과) 검색", placeholder="예: 제일, 이노션, 차이")

            if search_query:
                view_pt = view_pt[view_pt["광고주"].str.contains(search_query, na=False) | view_pt["품목"].str.contains(search_query, na=False)]
            if min_b > 0:
                view_pt = view_pt[view_pt["빌링(억원)"] >= min_b]
            if winner_search:
                view_pt = view_pt[view_pt["선정사(결과)"].str.contains(winner_search, na=False)]

            st.dataframe(
                view_pt[["PT일자", "광고주", "품목", "빌링_원문", "기존사", "참여사", "선정사(결과)", "메모(비고)"]].rename(columns={"빌링_원문": "빌링(억원)"}),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("PT 데이터가 없습니다.")

    # 탭 2: 매출 동향
    elif selected_category == "대행사/매체사 매출 동향":
        st.markdown("<h3 style='font-size: 1.20rem; font-weight: 700; color: #0F172A; margin-bottom: 2px;'>광고대행사 및 방송 매체사 매출 추이 & YoY 분석</h3>", unsafe_allow_html=True)
        st.caption("sales_master.xlsx 마스터 시트와 100% 동기화된 정밀 매출(Start vs 마감) 통계입니다.")
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        
        view_mode = st.radio(
            "보기 방식",
            ["그래프 보기", "상세 매출표 보기", "둘 다 보기"],
            horizontal=True
        )
        st.markdown("---")
        
        col_l, col_r = st.columns(2)
        
        # [좌측] 대행사 영역
        with col_l:
            st.markdown("##### 주요 광고대행사 전파광고 매출 (Start vs 마감)")
            if not df_agency.empty:
                all_agencies = sorted(df_agency["대행사"].unique().tolist())
                agency_years = sorted(list(set([str(y) for y in df_agency["연도"].dropna() if str(y).isdigit()])), reverse=True)
                
                c_ag1, c_ag2 = st.columns([1.2, 1])
                with c_ag1:
                    selected_single_agency = st.selectbox("대행사 선택", all_agencies, key="sel_single_agency")
                with c_ag2:
                    selected_ag_year = st.selectbox("조회 연도", ["전체 연도"] + agency_years, key="sel_ag_year")

                df_single_ag = df_agency[df_agency["대행사"] == selected_single_agency]
                
                if selected_ag_year != "전체 연도":
                    df_view_ag = df_single_ag[df_single_ag["연도"] == selected_ag_year].sort_values(by="연월")
                else:
                    df_view_ag = df_single_ag.sort_values(by="연월")

                if view_mode in ["그래프 보기", "둘 다 보기"]:
                    fig_ag = px.bar(
                        df_view_ag, 
                        x="연월", 
                        y="매출(억원)", 
                        color="구분",
                        barmode="group",
                        text_auto=".1f",
                        title=f"[{selected_single_agency}] 매출 추이 - Start vs 마감 ({selected_ag_year})",
                        color_discrete_map={"Start": "#60A5FA", "마감": "#1E3A8A"}
                    )
                    fig_ag.update_layout(
                        plot_bgcolor="#FFFFFF",
                        paper_bgcolor="#FFFFFF",
                        font_family="Inter, Pretendard",
                        font_size=12,
                        margin=dict(t=35, l=10, r=10, b=10),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )
                    st.plotly_chart(fig_ag, use_container_width=True)

                if view_mode in ["상세 매출표 보기", "둘 다 보기"]:
                    pivot_ag = df_view_ag.pivot_table(
                        index=["대행사", "구분"], 
                        columns="연월", 
                        values="매출(억원)", 
                        aggfunc="sum",
                        fill_value=0
                    )
                    st.dataframe(pivot_ag, use_container_width=True)

                with st.expander(f"{selected_single_agency} YoY 비교 분석 (마감액 기준)", expanded=False):
                    df_ag_close = df_single_ag[df_single_ag["구분"] == "마감"]
                    if df_ag_close.empty:
                        df_ag_close = df_single_ag

                    close_years = sorted(list(set([str(y) for y in df_ag_close["연도"].dropna() if str(y).isdigit()])), reverse=True)
                    if len(close_years) >= 2:
                        yoy_base_year = st.selectbox("기준 연도(당해)", close_years, index=0, key="yoy_ag_base")
                        prev_year = str(int(yoy_base_year) - 1)
                        
                        df_curr = df_ag_close[df_ag_close["연도"] == yoy_base_year][["월", "매출(억원)"]].rename(columns={"매출(억원)": f"{yoy_base_year}년"})
                        df_prev = df_ag_close[df_ag_close["연도"] == prev_year][["월", "매출(억원)"]].rename(columns={"매출(억원)": f"{prev_year}년"})
                        
                        if not df_curr.empty and not df_prev.empty:
                            df_yoy_ag = pd.merge(df_prev, df_curr, on="월", how="outer").fillna(0)
                            
                            def month_sort_key(m):
                                digits = re.findall(r'\d+', str(m))
                                return int(digits[0]) if digits else 99
                            df_yoy_ag["월순서"] = df_yoy_ag["월"].apply(month_sort_key)
                            df_yoy_ag = df_yoy_ag.sort_values(by="월순서").drop(columns=["월순서"])
                            
                            df_yoy_ag["증감액(억원)"] = df_yoy_ag[f"{yoy_base_year}년"] - df_yoy_ag[f"{prev_year}년"]
                            df_yoy_ag["YoY 증감률(%)"] = df_yoy_ag.apply(
                                lambda r: f"{((r[f'{yoy_base_year}년'] - r[f'{prev_year}년']) / r[f'{prev_year}년'] * 100):+.1f}%" 
                                if r[f"{prev_year}년"] > 0 else "-", axis=1
                            )
                            
                            fig_yoy_ag = px.bar(
                                df_yoy_ag, 
                                x="월", 
                                y=[f"{prev_year}년", f"{yoy_base_year}년"], 
                                barmode="group",
                                color_discrete_sequence=["#94A3B8", "#1E3A8A"],
                                title=f"{prev_year}년 vs {yoy_base_year}년 월별 마감 매출 비교"
                            )
                            fig_yoy_ag.update_layout(
                                plot_bgcolor="#FFFFFF",
                                paper_bgcolor="#FFFFFF",
                                font_family="Inter, Pretendard",
                                font_size=12,
                                margin=dict(t=35, l=10, r=10, b=10)
                            )
                            st.plotly_chart(fig_yoy_ag, use_container_width=True)
                            st.dataframe(df_yoy_ag, hide_index=True, use_container_width=True)
                        else:
                            st.info(f"{prev_year}년 또는 {yoy_base_year}년 데이터가 부족합니다.")
                    else:
                        st.caption("축적된 연도 데이터가 2개 이상일 때 YoY 분석이 가능합니다.")
            else:
                st.info("sales_master.xlsx 파일의 대행사 매출 데이터를 확인 중입니다.")

        # [우측] 방송 매체사 영역
        with col_r:
            st.markdown("##### 방송 매체사 광고 매출 (Start vs 마감)")
            if not df_tv.empty:
                all_channels = sorted(df_tv["채널"].unique().tolist())
                tv_years = sorted(list(set([str(y) for y in df_tv["연도"].dropna() if str(y).isdigit()])), reverse=True)
                
                c_tv1, c_tv2 = st.columns([1.2, 1])
                with c_tv1:
                    selected_single_tv = st.selectbox("방송 채널 선택", all_channels, key="sel_single_tv")
                with c_tv2:
                    selected_tv_year = st.selectbox("조회 연도", ["전체 연도"] + tv_years, key="sel_tv_year")

                df_single_tv = df_tv[df_tv["채널"] == selected_single_tv]
                
                if selected_tv_year != "전체 연도":
                    df_view_tv = df_single_tv[df_single_tv["연도"] == selected_tv_year].sort_values(by="연월")
                else:
                    df_view_tv = df_single_tv.sort_values(by="연월")

                if view_mode in ["그래프 보기", "둘 다 보기"]:
                    fig_tv = px.bar(
                        df_view_tv, 
                        x="연월", 
                        y="매출(억원)", 
                        color="구분",
                        barmode="group",
                        text_auto=".1f",
                        title=f"[{selected_single_tv}] 매출 추이 - Start vs 마감 ({selected_tv_year})",
                        color_discrete_map={"Start": "#60A5FA", "마감": "#1E3A8A"}
                    )
                    fig_tv.update_layout(
                        plot_bgcolor="#FFFFFF",
                        paper_bgcolor="#FFFFFF",
                        font_family="Inter, Pretendard",
                        font_size=12,
                        margin=dict(t=35, l=10, r=10, b=10),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )
                    st.plotly_chart(fig_tv, use_container_width=True)

                if view_mode in ["상세 매출표 보기", "둘 다 보기"]:
                    pivot_tv = df_view_tv.pivot_table(
                        index=["채널", "구분"], 
                        columns="연월", 
                        values="매출(억원)", 
                        aggfunc="sum",
                        fill_value=0
                    )
                    st.dataframe(pivot_tv, use_container_width=True)

                with st.expander(f"{selected_single_tv} YoY 비교 분석 (마감액 기준)", expanded=False):
                    df_tv_close = df_single_tv[df_single_tv["구분"] == "마감"]
                    if df_tv_close.empty:
                        df_tv_close = df_single_tv

                    tv_close_years = sorted(list(set([str(y) for y in df_tv_close["연도"].dropna() if str(y).isdigit()])), reverse=True)
                    if len(tv_close_years) >= 2:
                        yoy_tv_base = st.selectbox("기준 연도(당해)", tv_close_years, index=0, key="yoy_tv_base")
                        prev_tv_year = str(int(yoy_tv_base) - 1)
                        
                        df_curr_tv = df_tv_close[df_tv_close["연도"] == yoy_tv_base][["월", "매출(억원)"]].rename(columns={"매출(억원)": f"{yoy_tv_base}년"})
                        df_prev_tv = df_tv_close[df_tv_close["연도"] == prev_tv_year][["월", "매출(억원)"]].rename(columns={"매출(억원)": f"{prev_tv_year}년"})
                        
                        if not df_curr_tv.empty and not df_prev_tv.empty:
                            df_yoy_tv = pd.merge(df_prev_tv, df_curr_tv, on="월", how="outer").fillna(0)
                            
                            def month_sort_key(m):
                                digits = re.findall(r'\d+', str(m))
                                return int(digits[0]) if digits else 99
                            df_yoy_tv["월순서"] = df_yoy_tv["월"].apply(month_sort_key)
                            df_yoy_tv = df_yoy_tv.sort_values(by="월순서").drop(columns=["월순서"])
                            
                            # [오타 수정 완료: yoy_base_year -> yoy_tv_base]
                            df_yoy_tv["증감액(억원)"] = df_yoy_tv[f"{yoy_tv_base}년"] - df_yoy_tv[f"{prev_tv_year}년"]
                            df_yoy_tv["YoY 증감률(%)"] = df_yoy_tv.apply(
                                lambda r: f"{((r[f'{yoy_tv_base}년'] - r[f'{prev_tv_year}년']) / r[f'{prev_tv_year}년'] * 100):+.1f}%" 
                                if r[f"{prev_tv_year}년"] > 0 else "-", axis=1
                            )
                            
                            fig_yoy_tv = px.bar(
                                df_yoy_tv, 
                                x="월", 
                                y=[f"{prev_tv_year}년", f"{yoy_tv_base}년"], 
                                barmode="group",
                                color_discrete_sequence=["#94A3B8", "#1E3A8A"],
                                title=f"{prev_tv_year}년 vs {yoy_tv_base}년 월별 마감 매출 비교"
                            )
                            fig_yoy_tv.update_layout(
                                plot_bgcolor="#FFFFFF",
                                paper_bgcolor="#FFFFFF",
                                font_family="Inter, Pretendard",
                                font_size=12,
                                margin=dict(t=35, l=10, r=10, b=10)
                            )
                            st.plotly_chart(fig_yoy_tv, use_container_width=True)
                            st.dataframe(df_yoy_tv, hide_index=True, use_container_width=True)
                        else:
                            st.info(f"{prev_tv_year}년 또는 {yoy_tv_base}년 데이터가 부족합니다.")
                    else:
                        st.caption("축적된 연도 데이터가 2개 이상일 때 YoY 분석이 가능합니다.")
            else:
                st.info("sales_master.xlsx 파일의 방송사 매출 데이터를 확인 중입니다.")

    # 탭 3: 이슈 브리핑
    elif selected_category == "월별 핵심 이슈 브리핑":
        st.markdown("<h3 style='font-size: 1.20rem; font-weight: 700; color: #0F172A; margin-bottom: 2px;'>월별 업계 주요 이슈 및 정책 동향</h3>", unsafe_allow_html=True)
        st.caption("방송통신 및 광고 업계의 월별 핵심 뉴스 및 정책 이슈를 모니터링합니다.")
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        
        if not df_issues.empty:
            selected_ym = st.selectbox("조회 연월", options=sorted(df_issues["연월"].unique(), reverse=True))
            ym_issues = df_issues[df_issues["연월"] == selected_ym]
            for hl in ym_issues["헤드라인"].unique():
                with st.expander(f"{hl}", expanded=True):
                    details = ym_issues[(ym_issues["헤드라인"] == hl) & (ym_issues["상세"] != "")]["상세"].tolist()
                    for d in details:
                        st.write(f"• {d}")
        else:
            st.info("이슈 데이터가 없습니다.")

    # 탭 4: AI 동향 분석가
    elif selected_category == "AI 동향 분석가":
        st.markdown("<h3 style='font-size: 1.20rem; font-weight: 700; color: #0F172A; margin-bottom: 2px;'>AI 기반 인텔리전스 분석 어시스턴트</h3>", unsafe_allow_html=True)
        st.caption("마스터 시트와 전수 모니터링 데이터를 통합 분석합니다.")
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        
        if not api_key:
            st.warning("사이드바에 'Gemini API Key'를 설정하시면 실시간 AI 질의응답이 활성화됩니다.")
        else:
            try:
                genai.configure(api_key=api_key)
                target_model = "gemini-3.6-flash"
                model = genai.GenerativeModel(target_model)
                st.caption(f"연결 모델: `{target_model}` | 통합 분석 데이터셋: PT {len(df_pt_unique):,}건, 대행사매출 {len(df_agency):,}건, 매체사매출 {len(df_tv):,}건, 이슈 {len(df_issues):,}건")
                
                user_question = st.text_input("질문을 입력하세요", placeholder="예: 제일기획이 선정한 광고주 목록 및 2026년 방송사별 매출 추이를 종합 분석해줘")
                
                if st.button("AI 분석 요청", type="primary") and user_question:
                    with st.spinner("전체 데이터베이스를 전수 스캔하여 심층 리포트를 작성 중입니다..."):
                        pt_full_csv = df_pt_unique[["PT일자", "광고주", "품목", "빌링(억원)", "기존사", "참여사", "선정사(결과)", "메모(비고)"]].to_csv(index=False) if not df_pt_unique.empty else "데이터 없음"
                        agency_full_csv = df_agency[["연월", "대행사", "매출(억원)", "구분"]].to_csv(index=False) if not df_agency.empty else "데이터 없음"
                        tv_full_csv = df_tv[["연월", "채널구분", "채널", "매출(억원)", "구분"]].to_csv(index=False) if not df_tv.empty else "데이터 없음"
                        issues_full_csv = df_issues[["연월", "헤드라인", "상세"]].to_string(index=False) if not df_issues.empty else "데이터 없음"

                        prompt = f"""
당신은 대한민국 미디어·방송·광고 업계 전문 수석 전략 컨설턴트입니다.
아래 제공된 [전체 광고회사 PT 수주 현황 데이터]를 비롯한 전 카테고리 빅데이터를 처음부터 끝까지 빠짐없이 전수(Full Dataset) 검토하여 질문에 정확하게 답변해 주세요.

[1. 전체 광고회사 PT 수주 현황 데이터 (전체 {len(df_pt_unique)}건 누락 없음)]
{pt_full_csv}

[2. 대행사 전파광고 매출 데이터 (마스터 시트 기준, Start/마감 구분 포함)]
{agency_full_csv}

[3. 방송 매체사 광고 매출 데이터 (마스터 시트 기준, 지상파/종편유선 Start/마감 포함)]
{tv_full_csv}

[4. 월별 업계 주요 이슈 브리핑 데이터]
{issues_full_csv}

[사용자 질문]
{user_question}

작성 지침:
1. 반드시 제공된 데이터를 전수 검토하여 수치와 회사명을 정확히 대조하여 서술하세요.
2. 수치 분석 시 Start vs 마감의 차이점 및 추이를 분석하고 명확한 비즈니스 인사이트를 도출하세요.
3. 가독성을 위해 불릿 포인트와 볼드(**)를 적극 활용하여 완성도 높은 리포트 형식으로 작성하세요.
4. 데이터에 명시된 사실에만 입각하여 서술하세요.
"""
                        response = model.generate_content(prompt)
                        
                        log_activity(
                            st.session_state["username"], 
                            st.session_state["user_name"], 
                            "AI 질의", 
                            f"질문: {user_question[:40]}..."
                        )
                        
                        st.markdown("##### 🏛️ 인텔리전스 종합 분석 리포트")
                        st.markdown(f'<div class="ai-report-box">{response.text}</div>', unsafe_allow_html=True)
            except Exception as e:
                err_msg = str(e)
                if "429" in err_msg:
                    st.error("일시적으로 API 호출 한도에 도달했습니다. 잠시 후 다시 시도해 주세요.")
                else:
                    st.error(f"AI 호출 오류: {err_msg}")
