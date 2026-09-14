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
os.makedirs(DATA_DIR, exist_ok=True)

# GitHub API 연동 설정 (media-trend)
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", None)
GITHUB_REPO = st.secrets.get("GITHUB_REPO", "Mickie-Park/media-trend")
FILE_PATH = "users.json"

# --- 2. Option C: 하이엔드 컨설팅 리포트 테마 + 사이드바 UI 버그 완전 박멸 CSS ---
st.markdown("""
<style>
    /* 1. Inter + Pretendard 글로벌 금융/컨설팅 서체 (콤팩트 스케일) */
    @import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap");
    @import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css");
    
    html, body, [class*="css"], .stMarkdown, .stText, .stTextInput, .stSelectbox {
        font-family: "Inter", "Pretendard Variable", Pretendard, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        font-feature-settings: "cv02", "cv03", "cv04", "cv11", "tnum" !important;
        letter-spacing: -0.015em;
        font-size: 0.93rem;
    }

    /* 2. 메인 캔버스: 우아하고 눈이 편안한 웜 오프화이트 */
    .stApp {
        background-color: #FAF9F6;
        color: #1E293B;
    }

    /* 3. 사이드바 베이스: 딥 옥스퍼드 미드나이트 */
    [data-testid="stSidebar"] {
        background-color: #0C1A30 !important;
        border-right: 1px solid #1E2E4A !important;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] h4, [data-testid="stSidebar"] p, [data-testid="stSidebar"] label {
        color: #F8FAFC !important;
    }
    [data-testid="stSidebar"] hr {
        border-color: #1E2E4A !important;
    }
    [data-testid="stSidebar"] .stCaption {
        color: #94A3B8 !important;
        font-size: 0.76rem !important;
    }

    /* ========================================================= */
    /* 4. [완전 해결] 사이드바 로그아웃 및 일반 버튼 텍스트 복원 */
    /* ========================================================= */
    [data-testid="stSidebar"] .stButton > button,
    [data-testid="stSidebar"] [data-testid="baseButton-secondary"],
    [data-testid="stSidebar"] button[kind="secondary"] {
        background-color: #16243E !important;
        border: 1px solid #3B82F6 !important;
        border-radius: 5px !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3) !important;
    }
    
    /* 흰색 배경 및 흰색 글씨 겹침 현상 원천 차단 */
    [data-testid="stSidebar"] .stButton > button *,
    [data-testid="stSidebar"] [data-testid="baseButton-secondary"] *,
    [data-testid="stSidebar"] button[kind="secondary"] * {
        color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: 0.84rem !important;
        background: transparent !important;
        opacity: 1 !important;
    }
    
    [data-testid="stSidebar"] .stButton > button:hover,
    [data-testid="stSidebar"] [data-testid="baseButton-secondary"]:hover {
        background-color: #1E3A8A !important;
        border-color: #60A5FA !important;
    }

    /* 사이드바 Primary 버튼 (회원 관리 콘솔 등) */
    [data-testid="stSidebar"] button[kind="primary"] {
        background-color: #2563EB !important;
        border: 1px solid #60A5FA !important;
        border-radius: 5px !important;
    }
    [data-testid="stSidebar"] button[kind="primary"] * {
        color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: 0.84rem !important;
        background: transparent !important;
    }

    /* ========================================================= */
    /* 5. [완전 해결] 사이드바 파일 업로더(엑셀 추가) 흰 박스 제거 */
    /* ========================================================= */
    [data-testid="stSidebar"] [data-testid="stFileUploader"] {
        background-color: transparent !important;
    }
    
    /* 드롭존 박스 (파란색 점선 프레임) */
    [data-testid="stSidebar"] [data-testid="stFileUploader"] section,
    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
        background-color: #13213B !important;
        border: 1.5px dashed #3B82F6 !important;
        border-radius: 6px !important;
        padding: 12px !important;
    }
    
    /* 드롭존 내부 안내 텍스트 */
    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"] *,
    [data-testid="stSidebar"] [data-testid="stFileUploader"] section span,
    [data-testid="stSidebar"] [data-testid="stFileUploader"] section small {
        color: #94A3B8 !important;
        background: transparent !important;
        font-size: 0.76rem !important;
    }
    
    /* 업로더 내부 [Browse files] 버튼 복원 */
    [data-testid="stSidebar"] [data-testid="stFileUploader"] button {
        background-color: #1E3A8A !important;
        border: 1px solid #3B82F6 !important;
        border-radius: 4px !important;
        padding: 4px 10px !important;
    }
    [data-testid="stSidebar"] [data-testid="stFileUploader"] button * {
        color: #FFFFFF !important;
        font-weight: 600 !important;
        font-size: 0.78rem !important;
        background: transparent !important;
    }
    [data-testid="stSidebar"] [data-testid="stFileUploader"] button:hover {
        background-color: #2563EB !important;
    }

    /* 사이드바 내부 아코디언 및 입력창 */
    [data-testid="stSidebar"] [data-testid="stExpander"] {
        background-color: #13213B !important;
        border: 1px solid #243656 !important;
        border-radius: 5px !important;
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] * {
        color: #F8FAFC !important;
    }
    [data-testid="stSidebar"] input {
        background-color: #0C1A30 !important;
        border: 1px solid #2D4165 !important;
        color: #FFFFFF !important;
        border-radius: 4px !important;
        font-size: 0.84rem !important;
    }

    /* ========================================================= */
    /* 6. 메인 본문 지표 카드 및 탭 (컨설팅 리포트 콤팩트 스타일) */
    /* ========================================================= */
    [data-testid="stMetric"] {
        background-color: #FFFFFF;
        padding: 14px 18px;
        border-radius: 5px;
        border: 1px solid #E2E8F0;
        border-left: 3.5px solid #1E3A8A;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.74rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748B !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.45rem !important;
        font-weight: 700 !important;
        color: #0F172A !important;
        letter-spacing: -0.02em;
    }

    /* 탭 스타일 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        border-bottom: 2px solid #E2E8F0;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        height: 42px;
        font-size: 0.88rem;
        font-weight: 600;
        color: #64748B;
        border-radius: 0;
        padding: 0 14px;
        background-color: transparent !important;
    }
    .stTabs [aria-selected="true"] {
        color: #1E3A8A !important;
        border-bottom: 2px solid #1E3A8A !important;
        background-color: transparent !important;
    }

    /* 메인 화면 일반 버튼 */
    .stApp > div:not([data-testid="stSidebar"]) button[kind="primary"] {
        background-color: #1E3A8A !important;
        border-color: #1E3A8A !important;
        color: #FFFFFF !important;
        border-radius: 4px !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
    }
    .stApp > div:not([data-testid="stSidebar"]) button[kind="secondary"] {
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        color: #334155 !important;
        border-radius: 4px !important;
        font-size: 0.85rem !important;
    }

    /* 본문 아코디언 및 인풋 */
    .stApp > div:not([data-testid="stSidebar"]) [data-testid="stExpander"] {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0 !important;
        border-radius: 5px !important;
        margin-bottom: 10px;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);
    }
    div[data-baseweb="select"] > div, .stApp > div:not([data-testid="stSidebar"]) .stTextInput input {
        border-color: #CBD5E1 !important;
        border-radius: 4px !important;
        background-color: #FFFFFF !important;
        font-size: 0.86rem !important;
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

# 활동 로그 기록 함수
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

# --- 세션 상태 초기화 및 새로고침(F5) 유지 처리 ---
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

# --- 3. 엑셀 데이터 파싱 함수 ---
@st.cache_data
def load_all_data():
    raw_files = glob.glob("**/*.[xX][lL][sS][xX]", recursive=True)
    all_files = []
    for f in raw_files:
        filename = os.path.basename(f)
        if filename.startswith("~$"):
            continue
        if "업계동향" in filename or "data" in f.lower():
            all_files.append(f)
            
    all_files = sorted(list(set(all_files)))
    
    issues_list = []
    tv_sales_list = []
    pt_list = []
    agency_sales_list = []
    
    KNOWN_MEDIA_DICT = {
        "KBS": "KBS",
        "MBC": "MBC",
        "SBS": "SBS",
        "CJ ENM": "CJ ENM",
        "CJ E&M": "CJ ENM",
        "CJENM": "CJ ENM",
        "CJE&M": "CJ ENM",
        "JTBC": "JTBC",
        "TV CHOSUN": "TV조선",
        "TV조선": "TV조선",
        "CHANNEL A": "채널A",
        "채널A": "채널A",
        "CHANNELA": "채널A",
        "MBN": "MBN",
        "YTN": "YTN",
        "연합뉴스": "연합뉴스TV",
        "연합뉴스TV": "연합뉴스TV",
        "SPOTV": "SPOTV",
        "SBS PLUS": "SBS Plus",
        "SBS FUNT": "SBS FunE",
        "KBS N": "KBS N",
        "MBC PLUS": "MBC Plus",
        "E채널": "E채널",
        "TVN": "tvN",
        "OCN": "OCN"
    }

    for f in all_files:
        m = re.search(r'(\d{4})(\d{2})', f)
        ym = f"{m.group(1)}-{m.group(2)}" if m else "기타"
        year_str = m.group(1) if m else "기타"
        month_str = m.group(2) if m else "기타"
        
        try:
            xls = pd.ExcelFile(f)
            df = pd.read_excel(f, sheet_name=xls.sheet_names[0])
            
            # A. 주요 Issue 요약
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
            
            # B. 광고회사 PT 현황
            pt_start_row, pt_end_row = -1, -1
            for i in range(len(df)):
                row_str = " ".join([str(x) for x in df.iloc[i].dropna().tolist()])
                if "광고회사 PT" in row_str and "종합편" in row_str:
                    pt_start_row = i + 2
                elif "광고회사 전파광고" in row_str and pt_start_row != -1:
                    pt_end_row = i
                    break
            
            if pt_start_row != -1 and pt_end_row != -1:
                for r in range(pt_start_row, pt_end_row):
                    row_vals = df.iloc[r].tolist()
                    pt_date = row_vals[0]
                    client = row_vals[1]
                    product = row_vals[2]
                    billing = row_vals[3]
                    participants = row_vals[4] if len(row_vals) > 4 else ""
                    incumbent = row_vals[5] if len(row_vals) > 5 else ""
                    winner = row_vals[6] if len(row_vals) > 6 else ""
                    memo = row_vals[7] if len(row_vals) > 7 else ""
                    
                    if pd.notna(client) and str(client).strip() != "광고주":
                        client_str = str(client).strip()
                        date_raw_str = str(pt_date).strip() if pd.notna(pt_date) else ""

                        excluded_agencies = [
                            "TBWA", "SM C&C", "HS AD", "차이커뮤니케이션", 
                            "제일기획", "이노션", "대홍기획", "Dentsu", "덴츠"
                        ]
                        if any(ag in date_raw_str for ag in excluded_agencies) or any(ag in client_str for ag in excluded_agencies):
                            continue

                        if "광고회사" in client_str or "종합편" in client_str:
                            continue

                        date_str = pt_date.strftime("%Y-%m-%d") if isinstance(pt_date, pd.Timestamp) else date_raw_str
                        
                        pt_year = year_str
                        ymatch = re.search(r'(\d{4})', date_str)
                        if ymatch:
                            pt_year = ymatch.group(1)

                        billing_val = 0.0
                        b_match = re.search(r'(\d+)', str(billing))
                        if b_match:
                            try:
                                billing_val = float(b_match.group(1))
                            except:
                                pass
                            
                        pt_list.append({
                            "발행연월": ym,
                            "연도": pt_year,
                            "PT일자": date_str,
                            "광고주": client_str,
                            "품목": str(product).strip() if pd.notna(product) else "",
                            "빌링(억원)": billing_val,
                            "빌링_원문": str(billing).strip() if pd.notna(billing) else "",
                            "참여사": str(participants).strip() if pd.notna(participants) else "",
                            "기존사": str(incumbent).strip() if pd.notna(incumbent) else "",
                            "선정사": str(winner).strip() if pd.notna(winner) else "",
                            "메모": str(memo).strip() if pd.notna(memo) else ""
                        })

            # C. 대행사 전파광고 매출
            for i in range(len(df)):
                row_str = " ".join([str(x) for x in df.iloc[i].dropna().tolist()])
                if "광고회사 전파광고" in row_str or "대행사 전파광고" in row_str:
                    for offset in range(2, 45):
                        if i + offset >= len(df): break
                        agency_row = df.iloc[i + offset].tolist()
                        row_full_text = " ".join([str(x) for x in agency_row if pd.notna(x)])
                        
                        if any(stop_kw in row_full_text for stop_kw in ["지상파 매출", "지상파 광고", "종합/유선채널", "유선채널", "방송사 매출"]):
                            break

                        name_candidate = ""
                        for val_cell in agency_row[:3]:
                            if pd.notna(val_cell):
                                c_str = str(val_cell).strip()
                                if c_str and not re.match(r'^\d+(\.\d+)?$', c_str):
                                    if not any(ign in c_str for ign in ["대행사", "광고회사", "회사명", "구분", "순위", "합계", "Total", "소계", "전파광고", "매출"]):
                                        name_candidate = c_str
                                        break
                        
                        if not name_candidate:
                            continue

                        if any(b_name in name_candidate for b_name in ["KBS", "MBC", "SBS", "JTBC", "TV Chosun", "TV조선", "채널A", "Channel A", "MBN", "CJ ENM", "CJ E&M", "SPOTV"]):
                            continue
                        
                        sales_val = None
                        for c_item in agency_row:
                            if pd.notna(c_item):
                                clean_num = str(c_item).replace(',', '').replace(' ', '').strip()
                                try:
                                    f_num = float(clean_num)
                                    if f_num > 0 and f_num != float(name_candidate if name_candidate.isdigit() else -1):
                                        sales_val = f_num
                                        break
                                except:
                                    pass
                        
                        if sales_val is not None:
                            agency_sales_list.append({
                                "연월": ym,
                                "연도": year_str,
                                "월": f"{int(month_str)}월" if month_str.isdigit() else month_str,
                                "대행사": name_candidate,
                                "매출(억원)": sales_val
                            })

            # D. 방송/미디어 매체사 매출
            for i in range(len(df)):
                row_vals = [str(x).strip() for x in df.iloc[i].dropna().tolist()]
                row_text = " ".join(row_vals).upper()

                is_terrestrial = any(k in row_text for k in ["지상파 매출", "지상파 광고", "지상파방송"])
                is_cable = any(k in row_text for k in ["종합/유선채널", "유선채널", "종합편성", "케이블", "CJ ENM", "CJ E&M", "주요 PP"])

                if is_terrestrial or is_cable:
                    max_offset = 15 if is_terrestrial else 30
                    cat_name = "지상파" if is_terrestrial else "종편/유선/PP"

                    for offset in range(1, max_offset):
                        if i + offset >= len(df): break
                        sub_row = df.iloc[i + offset].tolist()
                        
                        sub_row_str = " ".join([str(x) for x in sub_row if pd.notna(x)])
                        if any(ign in sub_row_str for ign in ["합계", "소계", "Total", "TOTAL", "단위:", "전년동기", "증감률"]):
                            continue

                        matched_ch = None
                        sales_val = None

                        for item in sub_row:
                            if pd.notna(item):
                                it_str = str(item).strip()
                                it_upper = it_str.upper().replace(" ", "")
                                
                                if not matched_ch:
                                    for k_name, std_name in KNOWN_MEDIA_DICT.items():
                                        k_clean = k_name.upper().replace(" ", "")
                                        if k_clean in it_upper:
                                            if "TOTAL" not in it_upper and "합계" not in it_upper:
                                                matched_ch = std_name
                                                break
                        
                        if matched_ch:
                            for item in sub_row:
                                if pd.notna(item):
                                    it_clean = str(item).replace(',', '').replace(' ', '').strip()
                                    try:
                                        val = float(it_clean)
                                        if val > 0 and val != float(re.sub(r'[^0-9]', '', matched_ch) or -1):
                                            sales_val = val
                                            break
                                    except:
                                        pass

                        if matched_ch and sales_val is not None:
                            tv_sales_list.append({
                                "연월": ym,
                                "연도": year_str,
                                "월": f"{int(month_str)}월" if month_str.isdigit() else month_str,
                                "채널": matched_ch,
                                "매출(억원)": sales_val,
                                "구분": cat_name
                            })
        except Exception as e:
            st.error(f"{f} 파싱 오류: {e}")
            
    return pd.DataFrame(issues_list), pd.DataFrame(tv_sales_list), pd.DataFrame(pt_list), pd.DataFrame(agency_sales_list), all_files

# --- 4. 로그인 및 회원가입 화면 (컨설팅 게이트웨이 스타일) ---
if not st.session_state["logged_in"]:
    st.markdown("""
    <div style="padding: 22px 0 20px 0; border-bottom: 2px solid #1E3A8A; margin-bottom: 22px;">
        <span style="font-size: 0.7rem; font-weight: 700; letter-spacing: 0.08em; color: #B45309; background: #FEF3C7; padding: 4px 9px; border-radius: 4px; border: 1px solid #FDE68A;">INTERNAL ACCESS ONLY</span>
        <h1 style="font-size: 1.55rem; font-weight: 700; color: #0F172A; margin: 10px 0 5px 0; letter-spacing: -0.02em;">월간 미디어·광고 인텔리전스 리포트</h1>
        <p style="font-size: 0.86rem; color: #64748B; margin: 0;">인가된 사내 사용자를 위한 전략 리서치 포털입니다. 등록된 계정으로 로그인해 주세요.</p>
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
                            st.warning("관리자 승인 대기 중입니다. 승인 완료 후 이용하실 수 있습니다.")
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
                    st.success("회원가입 신청이 완료되었습니다. 관리자 승인 후 로그인하실 수 있습니다.")
    st.stop()

# --- 5. 로그인 성공 후 공통 제어판 ---
df_issues, df_tv, df_pt, df_agency, loaded_files = load_all_data()
df_pt_unique = df_pt.drop_duplicates(subset=["PT일자", "광고주", "품목"]) if not df_pt.empty else pd.DataFrame()

def get_stay_duration_str():
    if st.session_state.get("login_time"):
        delta = get_now_kst() - st.session_state["login_time"]
        minutes = int(delta.total_seconds() // 60)
        seconds = int(delta.total_seconds() % 60)
        return f"{minutes}분 {seconds}초"
    return "집계 불가"

# 사이드바 사용자 정보 카드
st.sidebar.markdown(f"""
<div style="background-color: #13213B; border: 1px solid #243656; border-radius: 5px; padding: 12px; margin-bottom: 12px;">
    <div style="font-size: 0.68rem; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.06em; font-weight: 700;">USER PROFILE</div>
    <div style="font-size: 0.98rem; font-weight: 700; color: #FFFFFF; margin-top: 3px;">{st.session_state['user_name']}</div>
    <div style="font-size: 0.78rem; color: #60A5FA; margin-top: 2px;">Role: {st.session_state['role']}</div>
    <div style="font-size: 0.72rem; color: #94A3B8; margin-top: 5px; border-top: 1px solid #1E2E4A; padding-top: 5px;">체류 시간: {get_stay_duration_str()}</div>
</div>
""", unsafe_allow_html=True)

# 로그아웃 버튼 (선명한 고대비)
if st.sidebar.button("로그아웃", use_container_width=True):
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

# 마스터 전용 사이드바 메뉴
if st.session_state["role"] == "admin":
    st.sidebar.markdown("---")
    st.sidebar.markdown("<div style='font-size:0.72rem; color:#94A3B8; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:8px; font-weight:700;'>ADMIN CONSOLE</div>", unsafe_allow_html=True)
    
    if not st.session_state.get("admin_view", False):
        if st.sidebar.button("회원 관리 콘솔", type="primary", use_container_width=True):
            st.session_state["admin_view"] = True
            st.rerun()
    else:
        if st.sidebar.button("메인 대시보드 복귀", type="secondary", use_container_width=True):
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

    # 엑셀 업로더 (고대비 보정 완료)
    new_file = st.sidebar.file_uploader("월간 엑셀 추가 (.xlsx)", type=["xlsx"])
    if new_file is not None:
        save_path = os.path.join(DATA_DIR, new_file.name)
        with open(save_path, "wb") as f:
            f.write(new_file.getbuffer())
        st.sidebar.success(f"{new_file.name} 저장 완료")
        log_activity(st.session_state["username"], st.session_state["user_name"], "엑셀 업로드", f"파일: {new_file.name}")
        st.cache_data.clear()
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption(f"적재 완료 파일: **{len(loaded_files)}건**")

# =========================================================================
# 6. [관리자 전용 페이지] 회원 관리 및 활동 로그 (admin_view == True 일 때)
# =========================================================================
if st.session_state["role"] == "admin" and st.session_state.get("admin_view", False):
    c_head1, c_head2 = st.columns([4, 1])
    with c_head1:
        st.markdown("""
        <div style="padding: 4px 0 14px 0; border-bottom: 2px solid #1E3A8A; margin-bottom: 18px;">
            <span style="font-size: 0.7rem; font-weight: 700; letter-spacing: 0.08em; color: #B45309; background: #FEF3C7; padding: 3px 8px; border-radius: 4px; border: 1px solid #FDE68A;">EXECUTIVE ADMINISTRATION</span>
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
# 7. [메인 대시보드 화면] - Inter 콤팩트 타이포그래피 헤더
# =========================================================================
st.markdown("""
<div style="padding: 2px 0 18px 0; border-bottom: 2px solid #1E3A8A; margin-bottom: 20px;">
    <div style="display: flex; align-items: center; justify-content: space-between;">
        <div>
            <span style="font-size: 0.68rem; font-weight: 700; letter-spacing: 0.08em; color: #B45309; background: #FEF3C7; padding: 3px 8px; border-radius: 4px; border: 1px solid #FDE68A;">STRATEGIC INTELLIGENCE REPORT</span>
            <h1 style="font-size: 1.55rem; font-weight: 700; color: #0F172A; margin: 8px 0 4px 0; letter-spacing: -0.02em;">월간 미디어 · 광고 업계 동향 대시보드</h1>
            <p style="font-size: 0.84rem; color: #64748B; margin: 0;">2021년 9월 이후 축적된 월간 동향 보고서 통합 분석 인텔리전스</p>
        </div>
        <div style="display: inline-flex; align-items: center; gap: 6px; background: #FFFFFF; border: 1px solid #E2E8F0; padding: 5px 12px; border-radius: 20px; font-size: 0.74rem; color: #475569; box-shadow: 0 1px 2px rgba(0,0,0,0.03);">
            <span style="display: inline-block; width: 6px; height: 6px; background-color: #10B981; border-radius: 50%;"></span>
            GitHub 동기화 활성
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# 통합 검색 영역
st.markdown("#### 전 카테고리 통합 검색")
global_query = st.text_input(
    "키워드를 입력하면 모든 엑셀 데이터(이슈, PT, 대행사/매체사 매출)에서 실시간으로 찾아냅니다.",
    placeholder="예: OTT, 현대, 제일기획, 카카오, 디즈니 등 입력 후 Enter"
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
            df_pt_unique["선정사"].str.contains(global_query, case=False, na=False) |
            df_pt_unique["참여사"].str.contains(global_query, case=False, na=False) |
            df_pt_unique["기존사"].str.contains(global_query, case=False, na=False) |
            df_pt_unique["메모"].str.contains(global_query, case=False, na=False)
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
                matched_pt[["발행연월", "PT일자", "광고주", "품목", "빌링_원문", "참여사", "선정사", "메모"]].rename(columns={"빌링_원문": "빌링(억원)"}),
                hide_index=True,
                use_container_width=True
            )

    if len(matched_agency) > 0 or len(matched_tv) > 0:
        with st.expander(f"대행사 / 매체사 관련 검색 결과 ({len(matched_agency) + len(matched_tv)}건)", expanded=False):
            if len(matched_agency) > 0:
                st.caption("대행사 매출 데이터")
                st.dataframe(matched_agency[["연월", "대행사", "매출(억원)"]], hide_index=True, use_container_width=True)
            if len(matched_tv) > 0:
                st.caption("방송 매체사 매출 데이터")
                st.dataframe(matched_tv[["연월", "구분", "채널", "매출(억원)"]], hide_index=True, use_container_width=True)

    if tot_cnt == 0:
        st.warning(f"'{global_query}'에 대한 검색 결과가 없습니다.")
    
    st.markdown("---")

# 4개 메인 탭 영역
tab1, tab2, tab3, tab4 = st.tabs([
    "광고회사 PT 수주 현황", 
    "대행사/매체사 매출 동향", 
    "월별 핵심 이슈 브리핑", 
    "AI 동향 분석가"
])

# 탭 1: PT 수주 현황
with tab1:
    st.markdown("#### 광고회사 경쟁 PT 모니터링 및 수주 분석")
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

        st.markdown("<br>", unsafe_allow_html=True)
        f_col1, f_col2, f_col3 = st.columns([2, 2, 2])
        with f_col1:
            search_query = st.text_input("광고주 또는 품목 검색", placeholder="예: 라이나, 카카오, 샴푸")
        with f_col2:
            max_b_val = int(df_pt_unique['빌링(억원)'].max()) if df_pt_unique['빌링(억원)'].max() > 0 else 100
            min_b = st.slider("최소 빌링 (억원)", 0, max_b_val, 0)
        with f_col3:
            winner_search = st.text_input("선정사(승자) 검색", placeholder="예: 제일, 이노션, 차이")

        if search_query:
            view_pt = view_pt[view_pt["광고주"].str.contains(search_query, na=False) | view_pt["품목"].str.contains(search_query, na=False)]
        if min_b > 0:
            view_pt = view_pt[view_pt["빌링(억원)"] >= min_b]
        if winner_search:
            view_pt = view_pt[view_pt["선정사"].str.contains(winner_search, na=False)]

        st.dataframe(
            view_pt[["PT일자", "광고주", "품목", "빌링_원문", "참여사", "기존사", "선정사", "메모"]].rename(columns={"빌링_원문": "빌링(억원)"}),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("PT 데이터가 없습니다.")

# 탭 2: 매출 동향
with tab2:
    st.markdown("#### 광고대행사 및 방송 매체사 매출 추이 & YoY 분석")
    
    view_mode = st.radio(
        "보기 방식",
        ["그래프 보기", "상세 매출표 보기", "둘 다 보기"],
        horizontal=True
    )
    st.markdown("---")
    
    col_l, col_r = st.columns(2)
    
    # [좌측] 대행사 영역
    with col_l:
        st.markdown("##### 주요 광고대행사 전파광고 매출")
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
                df_view_ag = df_single_ag[df_single_ag["연도"] == selected_ag_year]
            else:
                df_view_ag = df_single_ag

            if view_mode in ["그래프 보기", "둘 다 보기"]:
                fig_ag = px.bar(
                    df_view_ag, 
                    x="연월", 
                    y="매출(억원)", 
                    text_auto=True,
                    title=f"[{selected_single_agency}] 매출 추이 ({selected_ag_year})",
                    color_discrete_sequence=["#1E3A8A"]
                )
                fig_ag.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_family="Inter, Pretendard",
                    margin=dict(t=40, l=10, r=10, b=10)
                )
                st.plotly_chart(fig_ag, use_container_width=True)

            if view_mode in ["상세 매출표 보기", "둘 다 보기"]:
                pivot_ag = df_view_ag.pivot_table(
                    index="대행사", 
                    columns="연월", 
                    values="매출(억원)", 
                    aggfunc="sum",
                    fill_value=0
                )
                st.dataframe(pivot_ag, use_container_width=True)

            with st.expander(f"{selected_single_agency} YoY 비교 분석", expanded=False):
                if len(agency_years) >= 2:
                    yoy_base_year = st.selectbox("기준 연도(당해)", agency_years, index=0, key="yoy_ag_base")
                    prev_year = str(int(yoy_base_year) - 1)
                    
                    df_curr = df_single_ag[df_single_ag["연도"] == yoy_base_year][["월", "매출(억원)"]].rename(columns={"매출(억원)": f"{yoy_base_year}년"})
                    df_prev = df_single_ag[df_single_ag["연도"] == prev_year][["월", "매출(억원)"]].rename(columns={"매출(억원)": f"{prev_year}년"})
                    
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
                            title=f"{prev_year}년 vs {yoy_base_year}년 월별 매출 비교"
                        )
                        fig_yoy_ag.update_layout(
                            plot_bgcolor="rgba(0,0,0,0)",
                            paper_bgcolor="rgba(0,0,0,0)",
                            font_family="Inter, Pretendard",
                            margin=dict(t=40, l=10, r=10, b=10)
                        )
                        st.plotly_chart(fig_yoy_ag, use_container_width=True)
                        st.dataframe(df_yoy_ag, hide_index=True, use_container_width=True)
                    else:
                        st.info(f"{prev_year}년 또는 {yoy_base_year}년 데이터가 부족합니다.")
                else:
                    st.caption("축적된 연도 데이터가 2개 이상일 때 YoY 분석이 가능합니다.")
        else:
            st.info("대행사 매출 집계 중")

    # [우측] 방송 매체사 영역
    with col_r:
        st.markdown("##### 방송 매체사 광고 매출")
        if not df_tv.empty:
            tv_source = df_tv[df_tv["채널"] != "Total (광고매출 only)"]
            all_channels = sorted(tv_source["채널"].unique().tolist())
            tv_years = sorted(list(set([str(y) for y in tv_source["연도"].dropna() if str(y).isdigit()])), reverse=True)
            
            c_tv1, c_tv2 = st.columns([1.2, 1])
            with c_tv1:
                selected_single_tv = st.selectbox("방송 채널 선택", all_channels, key="sel_single_tv")
            with c_tv2:
                selected_tv_year = st.selectbox("조회 연도", ["전체 연도"] + tv_years, key="sel_tv_year")

            df_single_tv = tv_source[tv_source["채널"] == selected_single_tv]
            
            if selected_tv_year != "전체 연도":
                df_view_tv = df_single_tv[df_single_tv["연도"] == selected_tv_year]
            else:
                df_view_tv = df_single_tv

            if view_mode in ["그래프 보기", "둘 다 보기"]:
                fig_tv = px.line(
                    df_view_tv, 
                    x="연월", 
                    y="매출(억원)", 
                    markers=True,
                    title=f"[{selected_single_tv}] 매출 추이 ({selected_tv_year})",
                    color_discrete_sequence=["#1E3A8A"]
                )
                fig_tv.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_family="Inter, Pretendard",
                    margin=dict(t=40, l=10, r=10, b=10)
                )
                st.plotly_chart(fig_tv, use_container_width=True)

            if view_mode in ["상세 매출표 보기", "둘 다 보기"]:
                pivot_tv = df_view_tv.pivot_table(
                    index="채널", 
                    columns="연월", 
                    values="매출(억원)", 
                    aggfunc="sum",
                    fill_value=0
                )
                st.dataframe(pivot_tv, use_container_width=True)

            with st.expander(f"{selected_single_tv} YoY 비교 분석", expanded=False):
                if len(tv_years) >= 2:
                    yoy_tv_base = st.selectbox("기준 연도(당해)", tv_years, index=0, key="yoy_tv_base")
                    prev_tv_year = str(int(yoy_tv_base) - 1)
                    
                    df_curr_tv = df_single_tv[df_single_tv["연도"] == yoy_tv_base][["월", "매출(억원)"]].rename(columns={"매출(억원)": f"{yoy_tv_base}년"})
                    df_prev_tv = df_single_tv[df_single_tv["연도"] == prev_tv_year][["월", "매출(억원)"]].rename(columns={"매출(억원)": f"{prev_tv_year}년"})
                    
                    if not df_curr_tv.empty and not df_prev_tv.empty:
                        df_yoy_tv = pd.merge(df_prev_tv, df_curr_tv, on="월", how="outer").fillna(0)
                        
                        def month_sort_key(m):
                            digits = re.findall(r'\d+', str(m))
                            return int(digits[0]) if digits else 99
                        df_yoy_tv["월순서"] = df_yoy_tv["월"].apply(month_sort_key)
                        df_yoy_tv = df_yoy_tv.sort_values(by="월순서").drop(columns=["월순서"])
                        
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
                            title=f"{prev_tv_year}년 vs {yoy_tv_base}년 월별 매출 비교"
                        )
                        fig_yoy_tv.update_layout(
                            plot_bgcolor="rgba(0,0,0,0)",
                            paper_bgcolor="rgba(0,0,0,0)",
                            font_family="Inter, Pretendard",
                            margin=dict(t=40, l=10, r=10, b=10)
                        )
                        st.plotly_chart(fig_yoy_tv, use_container_width=True)
                        st.dataframe(df_yoy_tv, hide_index=True, use_container_width=True)
                    else:
                        st.info(f"{prev_tv_year}년 또는 {yoy_tv_base}년 데이터가 부족합니다.")
                else:
                    st.caption("축적된 연도 데이터가 2개 이상일 때 YoY 분석이 가능합니다.")
        else:
            st.info("방송사 매출 집계 중")

# 탭 3: 이슈 브리핑
with tab3:
    st.markdown("#### 월별 업계 주요 이슈 및 정책 동향")
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
with tab4:
    st.markdown("#### AI 기반 인텔리전스 분석 어시스턴트")
    if not api_key:
        st.warning("사이드바에 'Gemini API Key'를 설정하시면 실시간 AI 질의응답이 활성화됩니다.")
    else:
        try:
            genai.configure(api_key=api_key)
            target_model = "gemini-3.6-flash"
            model = genai.GenerativeModel(target_model)
            st.caption(f"연결 모델: `{target_model}`")
            
            user_question = st.text_input("질문을 입력하세요", placeholder="예: 최근 주요 광고주 PT 동향을 요약해줘")
            
            if st.button("AI 분석 요청", type="primary") and user_question:
                with st.spinner("동향 데이터를 기반으로 분석을 생성 중입니다..."):
                    context_issues = df_issues.head(40).to_string(index=False)
                    context_pt = df_pt_unique.head(30).to_string(index=False)
                    
                    prompt = f"""
당신은 대한민국 미디어·방송·광고 업계 전문 분석가입니다.
아래 제공된 [월별 업계 이슈 데이터]와 [광고회사 PT 현황 데이터]를 기반으로 질문에 명확하고 간결하게 답변해 주세요.

[월별 업계 이슈 데이터]
{context_issues}

[최근 주요 PT 현황]
{context_pt}

[질문]
{user_question}

지침:
1. 제공된 데이터의 구체적 사실(기업명, 수치 등)을 기반으로 작성하세요.
2. 가독성을 위해 불릿 포인트로 정리하세요.
3. 데이터에 없는 내용은 추측하지 마세요.
"""
                    response = model.generate_content(prompt)
                    
                    log_activity(
                        st.session_state["username"], 
                        st.session_state["user_name"], 
                        "AI 질의", 
                        f"질문: {user_question[:40]}..."
                    )
                    
                    st.markdown("##### 인텔리전스 분석 리포트")
                    st.markdown(response.text)
        except Exception as e:
            err_msg = str(e)
            if "429" in err_msg:
                st.error("일시적으로 API 호출 한도에 도달했습니다. 잠시 후 다시 시도해 주세요.")
            else:
                st.error(f"AI 호출 오류: {err_msg}")
