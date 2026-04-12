# -*- coding: utf-8 -*-
import streamlit as st
import hashlib
import datetime
import os
import sqlite3
import bcrypt
import json
import pandas as pd
from get_paper_info import get_paper_df, get_pdf_json
from name_change import korean_name_to_english
import base64
import shutil
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
import re
import textwrap
from dotenv import load_dotenv
# --- 상수 정의 ---
DB_FILE = "paper.db"
upload_folder = "uploaded"
resolve_folder = "resolved"

load_dotenv(override=True)  # modify
PDF_SERVICE_URL = os.getenv("PDF_SERVICE_URL")
if not PDF_SERVICE_URL:
    raise ValueError("❌🔑❌ 'PDF_SERVICE_URL'가 .env 파일에 없습니다.")
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT"))
if not REQUEST_TIMEOUT:
    raise ValueError("❌🔑❌ 'REQUEST_TIMEOUT'가 .env 파일에 없습니다.")
GMAIL_ID = os.getenv("GMAIL_ID")
if not GMAIL_ID:
    raise ValueError("❌🔑❌ 'GMAIL_ID'가 .env 파일에 없습니다.")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
if not GMAIL_APP_PASSWORD:
    raise ValueError("❌🔑❌ 'GMAIL_APP_PASSWORD'가 .env 파일에 없습니다.")

# --- 테마 설정 (Color Palettes - Design Guide 반영) ---
THEMES = {
    "Professional Navy (기본)": {
        "primary": "#2c3e50", "secondary": "#34495e", 
        "gradient_start": "#2c3e50", "gradient_end": "#4ca1af", 
        "bg_color": "#f4f6f9", "header_color": "#2c3e50", "btn_text": "#ffffff"
    },
    "Ocean Blue (신뢰감)": {
        "primary": "#3b82f6", "secondary": "#2563eb", 
        "gradient_start": "#3b82f6", "gradient_end": "#60a5fa", 
        "bg_color": "#eff6ff", "header_color": "#1e3a8a", "btn_text": "#ffffff"
    },
    "Forest Green (자연/건강)": {
        "primary": "#10b981", "secondary": "#059669", 
        "gradient_start": "#10b981", "gradient_end": "#34d399", 
        "bg_color": "#ecfdf5", "header_color": "#064e3b", "btn_text": "#ffffff"
    },
    "Sunset Orange (활기)": {
        "primary": "#f59e0b", "secondary": "#d97706", 
        "gradient_start": "#f59e0b", "gradient_end": "#fbbf24", 
        "bg_color": "#fffbeb", "header_color": "#78350f", "btn_text": "#ffffff"
    },
    "Royal Purple (고급)": {
        "primary": "#8b5cf6", "secondary": "#7c3aed", 
        "gradient_start": "#8b5cf6", "gradient_end": "#a78bfa", 
        "bg_color": "#f5f3ff", "header_color": "#4c1d95", "btn_text": "#ffffff"
    },
    "Minimal Flat (심플)": {
        "primary": "#4b5563", "secondary": "#374151", 
        "gradient_start": "#4b5563", "gradient_end": "#6b7280", 
        "bg_color": "#ffffff", "header_color": "#111827", "btn_text": "#ffffff"
    },
    "Vibrant Pink (트렌디)": {
        "primary": "#ec4899", "secondary": "#db2777", 
        "gradient_start": "#ec4899", "gradient_end": "#f472b6", 
        "bg_color": "#fdf2f8", "header_color": "#831843", "btn_text": "#ffffff"
    },
    "Tech Mono (개발자)": {
        "primary": "#1f2937", "secondary": "#111827", 
        "gradient_start": "#1f2937", "gradient_end": "#374151", 
        "bg_color": "#f3f4f6", "header_color": "#000000", "btn_text": "#ffffff"
    },
    "Warm Earth (따뜻함)": {
        "primary": "#b45309", "secondary": "#92400e", 
        "gradient_start": "#b45309", "gradient_end": "#d97706", 
        "bg_color": "#fff7ed", "header_color": "#431407", "btn_text": "#ffffff"
    }
}

# --- 스타일 적용 함수 ---
def apply_custom_styles(theme_name):
    """선택된 테마에 맞춰 CSS 스타일을 적용합니다."""
    
    if theme_name not in THEMES:
        theme_name = "Professional Navy (기본)"
    
    theme = THEMES[theme_name]
    
    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
        
        html, body, [class*="css"] {{
            font-family: 'Noto Sans KR', sans-serif;
        }}
        
        .stApp {{
            background-color: {theme['bg_color']};
        }}

        /* =================================================================
        [버튼 스타일링 통합]
        stButton (일반), stFormSubmitButton (폼), stLinkButton (링크) 모두 적용
           ================================================================= */
        
        /* 1. 버튼 컨테이너 너비 설정 */
        div[data-testid="stButton"], 
        div[data-testid="stFormSubmitButton"] {{
            width: 100% !important;
        }}
        
        /* 2. 공통 버튼 스타일 (일반, 폼, 링크 버튼) */
        div[data-testid="stButton"] > button,
        div[data-testid="stFormSubmitButton"] > button,
        a[data-testid="stLinkButton"] {{
            width: 100% !important;
            background-color: {theme['primary']} !important;
            color: #ffffff !important;
            border: 1px solid transparent !important;
            border-radius: 8px !important;
            padding: 0.6rem 1.2rem !important;
            font-size: 1rem !important;
            font-weight: 500 !important;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
            margin-bottom: 0.5rem !important;
            transition: all 0.2s ease !important;
            display: block !important;
            text-align: center !important;
            text-decoration: none !important; /* 링크 밑줄 제거 */
            line-height: 1.5 !important;
        }}
        
        /* 호버 효과 */
        div[data-testid="stButton"] > button:hover,
        div[data-testid="stFormSubmitButton"] > button:hover,
        a[data-testid="stLinkButton"]:hover {{
            background-color: {theme['secondary']} !important;
            color: #ffffff !important;
            border-color: transparent !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15) !important;
        }}

        /* 포커스/클릭 */
        div[data-testid="stButton"] > button:focus,
        div[data-testid="stButton"] > button:active,
        div[data-testid="stFormSubmitButton"] > button:focus,
        div[data-testid="stFormSubmitButton"] > button:active,
        a[data-testid="stLinkButton"]:focus,
        a[data-testid="stLinkButton"]:active {{
            border-color: transparent !important;
            color: #ffffff !important;
            box-shadow: none !important;
            outline: none !important;
        }}

        /* 3. Primary 버튼 (검색 등) - 그라데이션 */
        div[data-testid="stButton"] > button[kind="primary"],
        div[data-testid="stButton"] > button[data-testid="baseButton-primary"],
        div[data-testid="stFormSubmitButton"] > button[kind="primary"],
        div[data-testid="stFormSubmitButton"] > button[data-testid="baseButton-primary"] {{
            background: linear-gradient(135deg, {theme['gradient_start']} 0%, {theme['gradient_end']} 100%) !important;
            border: 1px solid transparent !important;
            color: #ffffff !important;
            font-weight: 700 !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2) !important;
        }}
        
        div[data-testid="stButton"] > button[kind="primary"]:hover,
        div[data-testid="stFormSubmitButton"] > button[kind="primary"]:hover {{
            opacity: 0.95 !important;
            color: #ffffff !important;
        }}

        /* [사이드바 메뉴만 빨간 테두리] */
        section[data-testid="stSidebar"] div[data-testid="stButton"] > button[kind="primary"] {{
            border: 3px solid #ff4b4b !important;
        }}
        section[data-testid="stSidebar"] div[data-testid="stButton"] > button[kind="primary"]:hover {{
            border: 3px solid #ff0000 !important;
        }}

        /* 데이터프레임 헤더 및 스크롤바 */
        [data-testid="stDataFrame"] th {{
            background-color: {theme['secondary']} !important;
            color: #ffffff !important;
            font-weight: 800 !important;
            font-size: 1.05rem !important;
            border-bottom: 2px solid {theme['primary']} !important;
            text-align: center !important;
        }}

        ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
        ::-webkit-scrollbar-track {{ background: #f1f1f1; }}
        ::-webkit-scrollbar-thumb {{ background: {theme['secondary']}; border-radius: 6px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: {theme['primary']}; }}

        /* 탭 스타일 */
        .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {{
            background-color: transparent !important;
            border-bottom: 3px solid {theme['primary']} !important;
            color: {theme['primary']} !important;
            font-weight: bold !important;
        }}
        
        /* 기타 UI */
        div[data-baseweb="input"] > div {{ border-radius: 6px; }}
        div[data-baseweb="input"] > div:focus-within {{ border-color: {theme['secondary']}; box-shadow: 0 0 0 2px {theme['secondary']}33; }}
        h1, h2, h3, h4 {{ color: {theme['header_color']}; font-family: 'Noto Sans KR', sans-serif; font-weight: 700; }}
        </style>
    """, unsafe_allow_html=True)

def send_processing_result_email(recipient_email, paper_details):
    """
    SMTP를 사용하여 처리 결과 안내 메일을 발송합니다.
    paper_details: list of dict [{'author': str, 'title': str, 'ori_filename': str}, ...]
    """
    if not recipient_email or "@" not in recipient_email:
        return False, "유효하지 않은 이메일 주소"

    subject = "[논문실적 수집기] 논문 업로드 처리 결과 안내"
    
    # 본문 구성
    body = "안녕하세요.\n요청하신 논문 업로드가 완료되었습니다.\n\n"
    
    for item in paper_details:
        # 제목이 없거나 비어있으면 '제목 없음' 처리
        title = item.get('title')
        if not title:
            title = "(제목 없음)"
            
        body += f"{item['author']} 님 아이디로 로그인하여 나의논문 페이지에서 확인하세요.\n"
        body += f"논문제목: {title}\n"
        body += f"파일명 : {item['ori_filename']}\n"
        body += "\n" + ("-" * 30) + "\n\n"
    
    body += "감사합니다."

    try:
        msg = MIMEMultipart()
        msg['From'] = GMAIL_ID
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(GMAIL_ID, GMAIL_APP_PASSWORD)
            server.send_message(msg)
            
        return True, "전송 성공"
    except Exception as e:
        return False, f"전송 실패: {e}"

# --- 데이터베이스 함수 ---
def init_db():
    """데이터베이스를 초기화하고 필요한 테이블 및 컬럼이 없으면 생성합니다."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # 1. user_info 테이블 생성
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS "user_info" (
            "name" TEXT, "id" TEXT PRIMARY KEY, "kri" TEXT,"email" TEXT, "hname" TEXT,
            "jkind" TEXT, "jrank" TEXT, "duty" TEXT, "dep" TEXT,
            "state" TEXT, "password" TEXT
        )
    """
    )
    c.execute("PRAGMA table_info(user_info)")
    columns = [col[1] for col in c.fetchall()]
    for i in range(1, 5):
        if f"hname{i}" not in columns:
            c.execute(f"ALTER TABLE user_info ADD COLUMN hname{i} TEXT")

    # 2. 비로그인 업로드용 u_info 테이블 생성
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS "u_info" (
            "ORI_FILE_NAME" TEXT,
            "PDF_FILE_NAME" TEXT,
            "AUTHOR" TEXT,
            "ID" TEXT,
            "ROLE" TEXT,
            "EMAIL" TEXT,
            "DONE" TEXT,
            "OLD_FILE_NAME" TEXT,
            "SAVE_DATE" TEXT
        )
    """
    )

    # 3. 시스템 설정(테마 등) 저장을 위한 system_config 테이블
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS "system_config" (
            "key" TEXT PRIMARY KEY,
            "value" TEXT
        )
    """
    )
    
    # 4. c_info 테이블 생성 (없으면)
    c.execute("""
        CREATE TABLE IF NOT EXISTS "c_info" (
            "YEAR" INTEGER,
            "ORI_FILE_NAME" TEXT,
            "PDF_FILE_NAME" TEXT,
            "JSON_FILE_NAME" TEXT,
            "LLM_JSON_FILE_NAME" TEXT,
            "TITLE" TEXT,
            "AUTHOR_LIST" TEXT,
            "AFFILIATION_LIST" TEXT,
            "FIRST_AUTHOR" TEXT,
            "CORRESPONDING_AUTHOR" TEXT,
            "CO_AUTHOR" TEXT,
            "KEYWORDS" TEXT,
            "JOURNAL_NAME" TEXT,
            "PUBLICATION_YEAR" INTEGER,
            "VOLUME" TEXT,
            "ISSUE" TEXT,
            "PAGE" TEXT,
            "DOI" TEXT
        )
    """)

    # 5. a_info 테이블 생성 (없으면)
    c.execute("""
        CREATE TABLE IF NOT EXISTS "a_info" (
            "YEAR" INTEGER,
            "ORI_FILE_NAME" TEXT,
            "PDF_FILE_NAME" TEXT,
            "JSON_FILE_NAME" TEXT,
            "LLM_JSON_FILE_NAME" TEXT,
            "AUTHOR" TEXT,
            "AFFILIATION" TEXT,
            "ROLE" TEXT,
            "직원번호" TEXT,
            "이름" TEXT,
            "소속" TEXT,
            "부서" TEXT
        )
    """)

    # [수정] 이력 관리 컬럼 추가 (a_info, c_info, user_info)
    # user_info는 hr_info 역할도 겸함
    target_tables = ["c_info", "a_info", "user_info"]
    audit_cols = ["REG_DT", "REG_ID", "MOD_DT", "MOD_ID"]
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    for tbl in target_tables:
        c.execute(f"PRAGMA table_info({tbl})")
        existing_cols = [col[1] for col in c.fetchall()]
        
        for col in audit_cols:
            if col not in existing_cols:
                try:
                    c.execute(f"ALTER TABLE {tbl} ADD COLUMN {col} TEXT")
                    # print(f"Added column {col} to table {tbl}")
                except Exception as e:
                    print(f"Error adding column {col} to {tbl}: {e}")
        
        # [수정] 기존 데이터에 대한 Default 값 채우기 (REG_DT가 비어있는 경우)
        try:
            # REG_DT, REG_ID가 NULL이거나 비어있으면 초기값 설정
            # MOD_DT, MOD_ID는 수정 시 업데이트되므로 굳이 초기화 안 해도 되지만, 통일성을 위해 같이 해도 됨.
            # 여기서는 REG 정보만 필수 초기화
            c.execute(f"UPDATE {tbl} SET REG_DT = ? WHERE REG_DT IS NULL OR REG_DT = ''", (current_time,))
            c.execute(f"UPDATE {tbl} SET REG_ID = ? WHERE REG_ID IS NULL OR REG_ID = ''", ("AD00000",))
            c.execute(f"UPDATE {tbl} SET MOD_DT = ? WHERE MOD_DT IS NULL OR MOD_DT = ''", (current_time,))
            c.execute(f"UPDATE {tbl} SET MOD_ID = ? WHERE MOD_ID IS NULL OR MOD_ID = ''", ("AD00000",))
        except Exception as e:
            print(f"Error updating default values for {tbl}: {e}")

    conn.commit()
    conn.close()

#  검색 필터에 사용할 년도, 저널, 부서 목록을 DB에서 가져옵니다
def get_filter_options():
    """검색 필터용 옵션(년도, 저널, 부서)을 DB에서 가져옵니다."""
    conn = sqlite3.connect(DB_FILE)
    options = {"years": [], "journals": [], "depts": []}
    
    try:
        cursor = conn.cursor()
        
        # 1. 년도 리스트 (최신순)
        cursor.execute("SELECT DISTINCT PUBLICATION_YEAR FROM c_info ORDER BY PUBLICATION_YEAR DESC")
        options["years"] = [str(row[0]) for row in cursor.fetchall() if row[0]]
        
        # 2. 저널 리스트 (가나다순)
        cursor.execute("SELECT DISTINCT JOURNAL_NAME FROM c_info ORDER BY JOURNAL_NAME ASC")
        options["journals"] = [row[0] for row in cursor.fetchall() if row[0]]
        
        # 3. 부서 리스트 (관리자용) - [수정] 실제 논문 실적이 있는 부서만 조회
        # user_info(u)와 a_info(a)를 JOIN하여 데이터가 있는 부서만 추출
        query_dept = """
            SELECT DISTINCT u.dep 
            FROM user_info u
            JOIN a_info a ON u.id = a.직원번호
            WHERE u.dep IS NOT NULL AND u.dep != ''
            ORDER BY u.dep ASC
        """
        cursor.execute(query_dept)
        options["depts"] = [row[0] for row in cursor.fetchall() if row[0]]
        
    except Exception as e:
        print(f"필터 옵션 로딩 오류: {e}")
    finally:
        conn.close()
    
    return options

# [추가] 시스템 테마 관련 DB 함수
def get_system_theme():
    """DB에서 전역 테마 설정을 가져옵니다."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("SELECT value FROM system_config WHERE key = 'global_theme'")
        result = c.fetchone()
        if result:
            return result[0]
        return "Professional Navy (기본)" # 기본값
    except Exception:
        return "Professional Navy (기본)"
    finally:
        conn.close()

def set_system_theme(theme_name):
    """DB에 전역 테마 설정을 저장합니다."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        # Upsert (SQLite 지원 버전에 따라 다름, 여기선 REPLACE 사용)
        c.execute("REPLACE INTO system_config (key, value) VALUES ('global_theme', ?)", (theme_name,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Theme save error: {e}")
        return False
    finally:
        conn.close()        

def verify_user(user_id, password):
    """사용자 자격 증명을 데이터베이스와 대조하여 확인합니다."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT password FROM user_info WHERE id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    if result and result[0]:
        stored_hashed_password = result[0].encode("utf-8")
        return bcrypt.checkpw(password.encode("utf-8"), stored_hashed_password)
    return False


def update_password(user_id, new_password):
    """주어진 사용자의 비밀번호를 업데이트합니다."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    hashed_new_password = bcrypt.hashpw(
        new_password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")
    c.execute(
        "UPDATE user_info SET password = ? WHERE id = ?", (hashed_new_password, user_id)
    )
    conn.commit()
    conn.close()


def add_or_update_user(data, is_new_user, user_id="AD00000"):
    """
    새로운 사용자를 추가하거나 기존 사용자를 업데이트합니다.
    [수정] 이력 관리 컬럼(REG_DT, REG_ID, MOD_DT, MOD_ID) 처리 추가
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if is_new_user:
        if not data["password"]:
            conn.close()
            return False, "새 사용자는 비밀번호가 필수입니다."
        data["password"] = bcrypt.hashpw(
            data["password"].encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")
        
        # [수정] 신규 등록 정보 추가
        data["REG_DT"] = current_time
        data["REG_ID"] = user_id
        data["MOD_DT"] = current_time
        data["MOD_ID"] = user_id

        try:
            columns = ", ".join(f'"{k}"' for k in data.keys())
            placeholders = ", ".join("?" * len(data))
            sql = f"INSERT INTO user_info ({columns}) VALUES ({placeholders})"
            c.execute(sql, list(data.values()))
            conn.commit()
            return True, ""
        except sqlite3.IntegrityError:
            return False, f"사용자 ID '{data['id']}'가 이미 존재합니다."
        finally:
            conn.close()
    else:  # 기존 사용자 업데이트
        update_fields = []
        update_values = []
        
        # [수정] 수정 정보 업데이트
        data["MOD_DT"] = current_time
        data["MOD_ID"] = user_id

        for key, value in data.items():
            if key == "id":
                continue
            if key == "password" and not value:
                continue
            # REG 정보는 업데이트하지 않음
            if key in ["REG_DT", "REG_ID"]:
                continue

            if key == "password":
                value = bcrypt.hashpw(value.encode("utf-8"), bcrypt.gensalt()).decode(
                    "utf-8"
                )

            update_fields.append(f'"{key}" = ?')
            update_values.append(value)

        update_values.append(data["id"])  # for WHERE clause
        query = f"UPDATE user_info SET {', '.join(update_fields)} WHERE id = ?"
        c.execute(query, tuple(update_values))
        conn.commit()
        conn.close()
        return True, ""


def get_all_users_data():
    """데이터베이스에서 모든 사용자 데이터를 가져옵니다."""
    conn = sqlite3.connect(DB_FILE)
    users = pd.read_sql(
        "SELECT name, id, kri, email,  hname, jkind, jrank, duty, dep, state, password, hname1, hname2, hname3, hname4 FROM user_info",
        conn,
    )
    conn.close()
    return users


def get_user_by_id(user_id):
    """ID로 단일 사용자 데이터를 가져옵니다."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "SELECT name, id, kri, email,  hname, jkind, jrank, duty, dep, state, password, hname1, hname2, hname3, hname4 FROM user_info WHERE id = ?",
        (user_id,),
    )
    user = c.fetchone()
    conn.close()
    return user

def search_author_by_name(name_variations, korean_name=None):
    """
    제공된 영어 이름 변형 목록 OR 한글 이름을 기반으로 저자 정보를 검색합니다.
    제공된 이름 변형 목록을 기반으로 a_info 테이블에서 저자 정보를 검색하고, 일치하는 c_info 정보를 결합하여 반환합니다."""
    # print('name_variations: ',name_variations)
    # print('korean_name: ',korean_name)
    if not name_variations:
        return pd.DataFrame()

    conn = sqlite3.connect(DB_FILE)
    try:
        cursor = conn.cursor()
        # a_info 테이블 존재 여부 확인
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='a_info';"
        )
        if not cursor.fetchone():
            conn.close()
            return pd.DataFrame()

        # [수정 1] 쿼리 조건 생성 (테이블 별칭 'a' 사용)
        # 대소문자 구분 없는 검색을 위해 LOWER 사용
        query_parts = ["LOWER(a.AUTHOR) LIKE LOWER(?)"] * len(name_variations)
        params = [f"%{var}%" for var in name_variations]

        # [수정 2] JOIN 쿼리 작성
        # a_info(a)와 c_info(c)를 PDF_FILE_NAME 기준으로 결합 (LEFT JOIN)
        # a 테이블에서는 저자, 역할, 소속을 가져오고, c 테이블에서는 해당 논문의 모든 서지정보를 가져옴
        # [수정] 한글 이름 조건 추가
        if korean_name:
            query_parts.append("a.이름 = ?")
            params.append(korean_name)

        if not query_parts:
            conn.close()
            return pd.DataFrame()
                
        full_query = f"""
            SELECT a.AUTHOR, a.ROLE, a.AFFILIATION, a.이름,a.직원번호, c.*
            FROM a_info a
            LEFT JOIN c_info c ON a.PDF_FILE_NAME = c.PDF_FILE_NAME
            WHERE {' OR '.join(query_parts)}
            ORDER BY c.PUBLICATION_YEAR, c.TITLE, a.AUTHOR, a.ROLE
        """

        df = pd.read_sql_query(full_query, conn, params=params)
        
        # [수정 3] 중복 컬럼 처리
        # 조인 시 PDF_FILE_NAME 등의 컬럼이 중복될 수 있으므로 중복된 컬럼 제거
        df = df.loc[:, ~df.columns.duplicated()]
        df = df[['AUTHOR', '이름','직원번호','ROLE',  'AFFILIATION','TITLE','PUBLICATION_YEAR','JOURNAL_NAME','FIRST_AUTHOR','CORRESPONDING_AUTHOR','AUTHOR_LIST','VOLUME','ISSUE','PAGE','DOI','PDF_FILE_NAME']]
        conn.close()
        return df.drop_duplicates() if not df.empty else pd.DataFrame()
        
    except Exception as e:
        st.error(f"검색 중 오류 발생: {e}")
        if conn:
            conn.close()
        return pd.DataFrame()

# [추가] 이름으로 사용자(HR) 정보 검색하는 함수
def search_users_by_name(kname_query, name_query=None):
    """
    이름(한글 이름 또는 영어 이름 변형)으로 user_info 테이블을 검색합니다.
    """
    # print("name_query:",kname_query)
    if not kname_query:
        return []

    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # 딕셔너리처럼 접근하기 위해
    c = conn.cursor()

    query = """
        SELECT name, id, dep, duty, hname1, hname2, hname3, hname4
        FROM user_info 
        WHERE name = ? 
    """
    # [중요] 튜플은 요소가 하나일 때 반드시 뒤에 쉼표(,)가 있어야 합니다.
    params = (kname_query,)
    
    try:
        c.execute(query, params)
        rows = c.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"User search error: {e}")
        return []
    finally:
        conn.close()

# [수정] claim_my_paper 함수 개선 (직원번호 업데이트 포함)
def claim_my_paper(pdf_filename, author, affiliation, user_id, user_name):
    """
    선택된 논문 저자 정보(a_info)에 사용자의 직원번호(ID)와 이름(Name)을 업데이트합니다.
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        # a_info 테이블 업데이트
        # [수정] 이력 관리 로직 추가: MOD_DT, MOD_ID 업데이트
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        query = """
            UPDATE a_info 
            SET 직원번호 = ?, 이름 = ?, MOD_DT = ?, MOD_ID = ?
            WHERE PDF_FILE_NAME = ? AND AUTHOR = ? AND AFFILIATION = ?
        """
        c.execute(query, (user_id, user_name, current_time, user_id, pdf_filename, author, affiliation))
        
        if c.rowcount > 0:
            conn.commit()
            return True, f"'{user_name}({user_id})' 님으로 지정되었습니다."
        else:
            return False, "일치하는 데이터를 찾을 수 없어 업데이트하지 못했습니다."
            
    except Exception as e:
        conn.rollback()
        return False, f"업데이트 중 오류 발생: {e}"
    finally:
        conn.close()

def get_my_papers(user_name, user_id):
    """
    a_info의 '이름'이 user_name과 일치하는 행을 찾고, 
    해당 PDF_FILE_NAME을 기준으로 c_info의 상세 정보를 결합(JOIN)하여 반환합니다.
    """
    conn = sqlite3.connect(DB_FILE)
    try:
        # a_info 테이블 존재 확인
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='a_info';")
        if not cursor.fetchone():
            return pd.DataFrame()

        # [핵심 로직]
        # 1. a_info(a)와 c_info(c)를 PDF_FILE_NAME으로 조인
        # 2. 조건: a.이름 = 로그인한 사용자 이름 AND a.직원번호 = 아이디
        query = """
            SELECT c.*, a.AUTHOR, a.ROLE, a.AFFILIATION, a.이름
            FROM a_info a
            JOIN c_info c ON a.PDF_FILE_NAME = c.PDF_FILE_NAME
            WHERE a.이름 = ?
                AND a.직원번호 = ?
            ORDER BY c.PUBLICATION_YEAR, c.TITLE, a.AUTHOR, a.ROLE
        """
        
        df = pd.read_sql_query(query, conn, params=(user_name,user_id,))
        
        # 중복된 컬럼(PDF_FILE_NAME 등)이 있을 경우 제거
        df = df.loc[:, ~df.columns.duplicated()]
        df = df[['AUTHOR', 'ROLE',  'AFFILIATION','TITLE','PUBLICATION_YEAR','JOURNAL_NAME','FIRST_AUTHOR','CORRESPONDING_AUTHOR','AUTHOR_LIST','VOLUME','ISSUE','PAGE','DOI','PDF_FILE_NAME']]
        df = df.drop_duplicates(subset='TITLE', keep='first')
        return df
    except Exception as e:
        st.error(f"내 논문 조회 중 오류 발생: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def update_or_add_paper_data(df, table_name, key_columns, user_id="AD00000"):
    """
    논문 데이터(a_info, c_info)를 데이터베이스에 업서트(Upsert)합니다.
    [수정] 이력 관리 로직 추가:
    - Insert 시 REG_DT, REG_ID 저장
    - Update 시 MOD_DT, MOD_ID 저장 (REG 정보는 유지)
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    if df.empty:
        conn.close()
        return True

    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        # 1. 기존 데이터에서 REG 정보 조회 (덮어쓰기 방지)
        # 키 컬럼을 기준으로 기존 DB 데이터를 조회
        keys = df[key_columns].drop_duplicates()
        existing_reg_info = {} # {(key1, key2...): {'REG_DT': ..., 'REG_ID': ...}}
        
        # key_columns가 여러 개일 수 있으므로 동적 쿼리 생성
        where_clause = " AND ".join([f"{col} = ?" for col in key_columns])
        select_query = f"SELECT {', '.join(key_columns)}, REG_DT, REG_ID FROM {table_name} WHERE {where_clause}"
        
        for _, row in keys.iterrows():
            params = tuple(row[col] for col in key_columns)
            try:
                cursor.execute(select_query, params)
                res = cursor.fetchone()
                if res:
                    # 키 값을 튜플로 만들어서 딕셔너리 키로 사용
                    key_val = tuple(res[i] for i in range(len(key_columns)))
                    # REG_DT(인덱스 -2), REG_ID(인덱스 -1)
                    existing_reg_info[key_val] = {'REG_DT': res[-2], 'REG_ID': res[-1]}
            except Exception:
                pass # 테이블이 없거나 컬럼이 없을 경우 패스

        # 2. DataFrame에 이력 정보 채우기
        # REG_DT, REG_ID, MOD_DT, MOD_ID 컬럼 확보
        for col in ['REG_DT', 'REG_ID', 'MOD_DT', 'MOD_ID']:
            if col not in df.columns:
                df[col] = None

        # 행별로 순회하며 값 설정 (Apply보다 반복문이 명확함)
        for idx, row in df.iterrows():
            key_val = tuple(row[col] for col in key_columns)
            
            # 기존 데이터가 있으면 REG 정보 복원
            if key_val in existing_reg_info:
                df.at[idx, 'REG_DT'] = existing_reg_info[key_val]['REG_DT']
                df.at[idx, 'REG_ID'] = existing_reg_info[key_val]['REG_ID']
            
            # REG_DT가 없으면(신규) 현재 시간/ID 입력
            if pd.isna(df.at[idx, 'REG_DT']) or df.at[idx, 'REG_DT'] == '':
                df.at[idx, 'REG_DT'] = current_time
                df.at[idx, 'REG_ID'] = user_id
            
            # MOD_DT, MOD_ID는 무조건 갱신
            df.at[idx, 'MOD_DT'] = current_time
            df.at[idx, 'MOD_ID'] = user_id

        # 3. 기존 Upsert 로직 진행 (Delete -> Insert)
        # 빈 테이블 생성용 (컬럼 정보 얻기)
        df.head(0).to_sql(table_name, conn, if_exists="append", index=False)
        existing_columns = [
            desc[0]
            for desc in cursor.execute(f'SELECT * FROM "{table_name}"').description
        ]
        df_to_append = df.reindex(columns=existing_columns).fillna(value=pd.NA)

        # 기존 데이터 삭제
        for _, key_row in keys.iterrows():
            conditions = " AND ".join([f'"{col}" = ?' for col in key_columns])
            values = tuple(key_row[col] for col in key_columns)
            sql_delete = f'DELETE FROM "{table_name}" WHERE {conditions}'
            cursor.execute(sql_delete, values)

        # 데이터 삽입
        df_to_append.to_sql(table_name, conn, if_exists="append", index=False)
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        st.error(f"'{table_name}' 업데이트 중 오류 발생: {e}")
        return False
    finally:
        conn.close()

def create_sidebar():
    """로그인한 사용자를 위한 사이드바를 생성합니다."""
    with st.sidebar:
        st.title("📄 논문실적 수집기")
        st.markdown(
            f"""
            <div style="font-size: 0.85em; color: #888; margin-bottom: 20px;">
                전남대학교병원 의생명연구원<br>
                문의: turbok2@gmail.com (v{version})
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        def reset_my_info_state():
            st.session_state.pop("eng_name_inputs", None)
            st.session_state.pop("eng_name_active", None)
            st.session_state.pop("author_search_results", None)
            st.session_state.pop("search_clicked", None)
            # [추가] 영어 이름 자동 동기화 실행 플래그 초기화 (메뉴 진입 시 다시 실행되도록)
            st.session_state.pop("hname_auto_synced", None)

        current_page = st.session_state.page

        # --- 메뉴 버튼 생성 헬퍼 함수 ---
        def menu_btn(label, page_name, icon=""):
            if current_page == page_name:
                btn_type = "primary"
                display_label = f"➤  {label}" 
            else:
                btn_type = "secondary"
                display_label = f"{icon}  {label}"
            
            if st.button(display_label, key=f"menu_{page_name}", type=btn_type):
                reset_my_info_state()
                st.session_state.page = page_name
                st.rerun()

        # [1] 상단 메인 메뉴
        menu_btn("논문 업로드", "upload", "📤")
            
        if st.session_state.username == "AD00000":
            menu_btn("접수처리 (관리자)", "receipts", "📥")

        label_papers = "전체 논문 (관리자)" if st.session_state.username == "AD00000" else "나의 논문"
        icon_papers = "🗂️" if st.session_state.username == "AD00000" else "📚"
        menu_btn(label_papers, "my_papers", icon_papers)

        menu_btn("내정보", "my_info", "👤")

        if st.session_state.username == "AD00000":
            menu_btn("사용자 관리", "user_management", "⚙️")

        st.markdown("<div style='margin: 30px 0; border-top: 1px solid #ddd;'></div>", unsafe_allow_html=True)
        
        st.markdown(
            f"<div style='text-align:center; color:#555; margin-bottom:10px;'>환영합니다, <strong>{st.session_state.username}</strong> 님!</div>",
            unsafe_allow_html=True,
        )

        # [2] 하단 메뉴
        col_set, col_out = st.columns(2)
        
        with col_set:
            if current_page == "settings":
                set_type = "primary"
                set_label = "➤  설정"
            else:
                set_type = "secondary"
                set_label = "⚙️  설정"
                
            if st.button(set_label, key="menu_settings", type=set_type):
                reset_my_info_state()
                st.session_state.page = "settings"
                st.rerun()
        
        with col_out:
            if st.button("로그아웃", key="menu_logout", type="secondary"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

def show_login_page():
    """로그인 및 게스트 업로드 페이지를 표시합니다."""
    
    theme_name = st.session_state.get("current_theme", "Professional Navy (기본)")
    if theme_name not in THEMES: theme_name = "Professional Navy (기본)"
    theme_color = THEMES[theme_name]["primary"]

    # 상단 로고/타이틀 영역
    st.markdown(
        f"""
        <div style="text-align: center; margin-top: 40px; margin-bottom: 30px;">
            <h1 style="color: {theme_color}; font-size: 2.5rem; margin-bottom: 10px;">📄 논문실적 수집기</h1>
            <p style="color: #666; font-size: 1.1rem; font-weight: 300;">
                연구 실적을 체계적으로 관리하고 분석하는 통합 플랫폼
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    if "login_view_mode" not in st.session_state:
        st.session_state.login_view_mode = "login"
    if "upload_row_count" not in st.session_state:
        st.session_state.upload_row_count = 3
    if "u_reset_counter" not in st.session_state:
        st.session_state.u_reset_counter = 0

    # =========================================================================
    # [화면 1] 로그인 모드
    # =========================================================================
    if st.session_state.login_view_mode == "login":
        
        # [수정 1] 너비 조정 (기존 [1, 1.8, 1] -> [1, 10, 1]로 변경하여 약 2배 넓게)
        col_spacer1, col_main, col_spacer2 = st.columns([1, 10, 1])
        
        with col_main:
            # [수정 2] 흰색 박스(<div class="login-container">) 제거
            # [수정 3] 텍스트 변경: '연구원 로그인' -> '로그인'
            st.subheader("🔐 로그인")
            
            user_id_input = st.text_input("사용자 ID", key="login_id", placeholder="아이디를 입력하세요")
            password_input = st.text_input("비밀번호", type="password", key="login_password", placeholder="비밀번호를 입력하세요")

            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("로그인", key="login_button"):
                if verify_user(user_id_input, password_input):
                    st.session_state.logged_in = True
                    st.session_state.username = user_id_input
                    st.session_state.page = "upload"
                    st.rerun()
                else:
                    st.error("아이디 또는 비밀번호가 일치하지 않습니다.")

            # 구분선 및 안내 문구
            st.markdown(
                """
                <div style="text-align: center; margin-top: 40px; margin-bottom: 20px; color: #888;">
                    혹은 계정이 없으신가요?
                </div>
                """, unsafe_allow_html=True
            )
            
            # [수정 2] 흰색 박스(<div class="guest-container">) 제거
            st.markdown("##### 🚀 비회원 논문 접수")
            st.caption("로그인 없이 파일을 제출하면 이메일로 분석 결과를 보내드립니다.")
            
            if st.button("논문 파일 업로드 바로가기", key="go_to_upload"):
                st.session_state.login_view_mode = "upload"
                st.rerun()

            # 하단 푸터
            st.markdown(
                """
                <div style="text-align: center; margin-top: 50px; font-size: 0.8em; color: #ccc;">
                    전남대학교병원 의생명연구원 | 시스템 문의: 062-220-5717
                </div>
                """,
                unsafe_allow_html=True
            )

    # =========================================================================
    # [화면 2] 비로그인 업로드 모드 (기존 유지)
    # =========================================================================
    else: 
        st.markdown(f"<h3 style='color:{theme_color};'>📤 비회원 논문 접수</h3>", unsafe_allow_html=True)
        st.markdown("---")
        
        if st.button("◀ 로그인 화면으로 돌아가기", key="back_to_login"):
            st.session_state.login_view_mode = "login"
            st.rerun()

        st.info("💡 **안내:** 성명과 이메일을 정확히 입력해주세요. PDF 파일을 업로드하면 시스템이 자동으로 서지정보를 추출하여 분석합니다.")

        current_counter = st.session_state.u_reset_counter
        u_author_key = f"u_author_input_{current_counter}"
        u_pid_key = f"u_pid_input_{current_counter}"
        u_email_key = f"u_email_input_{current_counter}"
        
        with st.container(border=True):
            st.markdown("#### 1. 제출자 정보")
            col_u1, col_u2, col_u3 = st.columns(3)
            with col_u1:
                u_author = st.text_input("저자 성명 (한글)", key=u_author_key, placeholder="예: 홍길동")
            with col_u2:
                u_pid = st.text_input("직원번호", key=u_pid_key, placeholder="AA00000")
            with col_u3:
                u_email = st.text_input("회신 받을 이메일", key=u_email_key, placeholder="example@email.com")

        st.markdown("<br>", unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown("#### 2. 파일 업로드")
            for i in range(st.session_state.upload_row_count):
                file_key = f"u_file_{i}_{current_counter}"
                role_key = f"u_role_{i}_{current_counter}"

                if file_key in st.session_state and st.session_state[file_key] is None:
                    st.session_state[role_key] = "선택하세요"

                col_file, col_role = st.columns([0.7, 0.3])
                with col_file:
                    st.file_uploader(f"논문 PDF 파일 #{i+1}", type=["pdf"], key=file_key, label_visibility="collapsed")
                with col_role:
                    st.selectbox(
                        f"본인의 역할 #{i+1}", 
                        ["선택하세요", "FIRST_AUTHOR", "CORRESPONDING_AUTHOR", "CO_AUTHOR","FIRST&CORRESPONDING_AUTHOR","SINGLE_AUTHOR"], 
                        key=role_key,
                        label_visibility="collapsed"
                    )
                st.markdown("<hr style='margin: 5px 0; border-top: 1px dashed #eee;'>", unsafe_allow_html=True)
            
            if st.button("➕ 입력란 추가", key="add_row_btn"):
                st.session_state.upload_row_count += 1
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        col_submit, col_reset = st.columns([0.7, 0.3])

        with col_submit:
            is_submitted = False
            if st.button("🚀 제출 및 저장하기", key="u_submit_all_btn"):
                is_submitted = True

        with col_reset:
            if st.button("🔄 초기화", key="u_reset_btn"):
                st.session_state.u_reset_counter += 1
                st.session_state.upload_row_count = 3
                st.rerun()

        if is_submitted:
            if not u_author:
                st.error("⚠️ 저자 성명을 입력해주세요.")
            else:
                valid_uploads = []
                role_missing = False

                for i in range(st.session_state.upload_row_count):
                    file_key = f"u_file_{i}_{current_counter}"
                    role_key = f"u_role_{i}_{current_counter}"
                    uploaded_file = st.session_state.get(file_key)
                    role_val = st.session_state.get(role_key)

                    if uploaded_file:
                        if role_val == "선택하세요":
                            st.error(f"#{i+1}번 파일의 저자 역할을 선택해주세요.")
                            role_missing = True
                        else:
                            valid_uploads.append((uploaded_file, role_val))
                
                if not role_missing:
                    if not valid_uploads:
                        st.warning("⚠️ 업로드된 파일이 없습니다.")
                    else:
                        try:
                            if not os.path.exists(upload_folder):
                                os.makedirs(upload_folder)

                            conn = sqlite3.connect(DB_FILE)
                            cur = conn.cursor()
                            success_logs = []
                            duplicate_logs = []
                            
                            for u_file, u_role in valid_uploads:
                                file_bytes = u_file.getvalue()
                                file_hash = calculate_hash(file_bytes)
                                pdf_file_name = f"{file_hash}.pdf"
                                save_path = os.path.join(upload_folder, pdf_file_name)
                                # print(f"Saving file: {save_path}")
                                ori_file_name = u_file.name

                                file_exists = os.path.exists(save_path)
                                cur.execute("SELECT PDF_FILE_NAME FROM u_info WHERE PDF_FILE_NAME = ?", (pdf_file_name,))
                                db_exists = cur.fetchone() is not None

                                if file_exists or db_exists:
                                    reason = []
                                    if file_exists: reason.append("서버 파일 중복")
                                    if db_exists: reason.append("DB 데이터 중복")
                                    duplicate_logs.append(f"{ori_file_name}")
                                else:
                                    with open(save_path, "wb") as f:
                                        f.write(file_bytes)
                                    save_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    cur.execute(
                                        "INSERT INTO u_info (ORI_FILE_NAME, PDF_FILE_NAME, AUTHOR,ID, ROLE, EMAIL, DONE, OLD_FILE_NAME, SAVE_DATE) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                        (ori_file_name, pdf_file_name, u_author, u_pid, u_role, u_email, 0, '', save_date)
                                    )
                                    success_logs.append(f"{ori_file_name} ({u_role})")

                            conn.commit()
                            conn.close()
                            
                            if success_logs:
                                st.success(f"✅ 총 {len(success_logs)}건이 성공적으로 접수되었습니다!")
                                if u_email:
                                    st.info(f"📧 분석 결과는 **{u_email}**로 발송됩니다.")
                            
                            if duplicate_logs:
                                st.warning(f"⛔ 중복 제외된 파일: {', '.join(duplicate_logs)}")
                            
                        except Exception as e:
                            st.error(f"저장 중 오류 발생: {e}")

# [STEP 6-1] 파일 이름 저장
def generate_output_filename(filename, suffix, model_name):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_model_name = model_name.replace(":", "_").replace(".", "_")
    base = filename.replace(".json", "").replace(" ", "_")[:200]
    return f"{timestamp}_{safe_model_name}_{base}_{suffix}"

# [STEP 6-2] JSON 파일 저장
def save_output_file(result, filename, model_name, OUTPUT_FOLDER):
    try:
        output_filename = generate_output_filename(filename, "output.json", model_name)
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
            
        # [추가] resolved 폴더에 저장할 경우, 동일한 해시의 구버전 파일 자동 삭제
        if OUTPUT_FOLDER == resolve_folder:
            base_hash = filename.replace(".json", "").replace(" ", "_")[:200]
            cleanup_resolved_files(target_hash=base_hash)
            
        return output_path, None

    except Exception as e:
        print(f"[❌❌] JSON_FAILED : {filename}\nError : {e}")
        return None, filename

# 3. 해시 계산 함수 (SHA-256)
def calculate_hash(file_bytes):
    sha256_hash = hashlib.sha256()
    sha256_hash.update(file_bytes)
    return sha256_hash.hexdigest()

# -------------------------------------------------------------------------
# [추가] 1. 파일 삭제 헬퍼 함수
# -------------------------------------------------------------------------
def delete_paper_files(pdf_filename):
    """
    업로드 및 분석 결과 폴더에서 특정 논문과 관련된 모든 파일을 안정적으로 삭제합니다.
    """
    if not pdf_filename:
        return
        
    file_hash = os.path.splitext(pdf_filename)[0]
    
    # 1. uploaded 폴더 내 파일 (PDF 및 JSON) 삭제
    if os.path.exists(upload_folder):
        for filename in os.listdir(upload_folder):
            if file_hash in filename:
                try:
                    os.remove(os.path.join(upload_folder, filename))
                except Exception as e:
                    print(f"Failed to delete from uploaded: {filename}, Error: {e}")
                    
    # 2. resolved 폴더 내 파일 (결과 JSON 등) 삭제
    if os.path.exists(resolve_folder):
        for filename in os.listdir(resolve_folder):
            if file_hash in filename:
                try:
                    os.remove(os.path.join(resolve_folder, filename))
                except Exception as e:
                    print(f"Failed to delete from resolved: {filename}, Error: {e}")

# -------------------------------------------------------------------------
# [추가] 4. resolved 폴더 내 이전 분석 파일(중복 해시) 정리 함수
# -------------------------------------------------------------------------
def cleanup_resolved_files(target_hash=None):
    """
    resolved 폴더 내의 파일들을 확인하여, 동일한 해시를 가진 파일이 여러 개일 경우
    가장 최신(이름의 타임스탬프 기준) 파일만 남기고 삭제합니다.
    target_hash가 주어지면 해당 해시에 대해서만 처리하고, 없으면 전체 폴더를 정리합니다.
    """
    if not os.path.exists(resolve_folder):
        return 0
        
    deleted_count = 0
    hash_groups = {}
    
    # 파일명 예시: 20260412_015154_gpt-4o..._b519d6b7..._output.json
    # 타임스탬프: (\d{8}_\d{6}), 중간 모델명, 해시: ([a-fA-F0-9]+), 확장자: _output.json
    pattern = re.compile(r'^(\d{8}_\d{6})_.*_([a-fA-F0-9]+)_output\.json$')
    
    for filename in os.listdir(resolve_folder):
        match = pattern.match(filename)
        if match:
            timestamp = match.group(1)
            file_hash = match.group(2)
            
            # 특정 해시만 타겟팅한 경우 필터링
            if target_hash and file_hash != target_hash:
                continue
                
            if file_hash not in hash_groups:
                hash_groups[file_hash] = []
            hash_groups[file_hash].append((timestamp, filename))
            
    for file_hash, files in hash_groups.items():
        if len(files) > 1:
            # 타임스탬프 기준 내림차순 정렬 (최신 시간이 0번 인덱스로 옴)
            files.sort(key=lambda x: x[0], reverse=True)
            
            # 첫 번째(최신) 파일을 제외한 나머지 삭제
            for _, fname in files[1:]:
                try:
                    os.remove(os.path.join(resolve_folder, fname))
                    deleted_count += 1
                except Exception as e:
                    print(f"Failed to delete old resolved file: {fname}, Error: {e}")
                    
    return deleted_count

# -------------------------------------------------------------------------
# [추가] 2. 논문 제목 정규화 함수
# -------------------------------------------------------------------------
def normalize_title(title):
    """영문, 숫자, 한글이 아닌 모든 문자를 제거하고 소문자로 변환합니다."""
    if pd.isna(title) or not title:
        return ""
    return re.sub(r'[^a-zA-Z0-9가-힣]', '', str(title).lower())

# -------------------------------------------------------------------------
# [추가] 3. 논문 제목 중복 확인 함수
# -------------------------------------------------------------------------
def check_title_duplicate_in_db(new_title, exclude_pdf_filename=None):
    """
    DB의 c_info 테이블에서 정규화된 제목이 같은 논문이 있는지 확인합니다.
    있다면 중복된 기존 논문의 PDF_FILE_NAME을 반환합니다.
    """
    norm_new_title = normalize_title(new_title)
    if not norm_new_title:
        return None

    conn = sqlite3.connect(DB_FILE)
    try:
        query = "SELECT TITLE, PDF_FILE_NAME FROM c_info"
        df = pd.read_sql_query(query, conn)
        
        for _, row in df.iterrows():
            db_title = row['TITLE']
            db_pdf = row['PDF_FILE_NAME']
            
            # 자기 자신(현재 분석 중인 파일)은 비교에서 제외
            if exclude_pdf_filename and db_pdf == exclude_pdf_filename:
                continue
                
            norm_db_title = normalize_title(db_title)
            if norm_new_title == norm_db_title:
                return db_pdf  # 중복 발견 시 기존 파일명 반환
                
        return None
    except Exception as e:
        print(f"Title check error: {e}")
        return None
    finally:
        conn.close()

# -------------------------------------------------------------------------
# [추가] 1. PDF 원문 보기 버튼 생성 헬퍼 함수
# -------------------------------------------------------------------------
def display_pdf_viewer_button(pdf_filename):
    """PDF 파일을 새 탭에서 열 수 있는 버튼을 렌더링합니다."""
    if not pdf_filename:
        st.warning("PDF 파일 정보가 없습니다.")
        return
        
    theme_name = st.session_state.get("current_theme", "Professional Navy (기본)")
    theme = THEMES.get(theme_name, THEMES["Professional Navy (기본)"])
    
    src = os.path.join(upload_folder, pdf_filename)
    if os.path.exists(src):
        if not os.path.exists("static"): 
            os.makedirs("static")
        dst = os.path.join("static", pdf_filename)
        if not os.path.exists(dst): 
            shutil.copy(src, dst)
        pdf_url = f"app/static/{pdf_filename}"
        
        st.markdown(f"""
            <div style="text-align: center; height: 100%; display: flex; flex-direction: column; justify-content: center;">
            <a href="{pdf_url}" target="_blank" style="
                display: inline-block; padding: 0.6em 1.2em;
                width: 100%; text-align: center;
                color: {theme['btn_text']}; 
                background: linear-gradient(135deg, {theme['gradient_start']} 0%, {theme['gradient_end']} 100%);
                border-radius: 8px; text-decoration: none; font-weight: bold;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                margin-bottom: 0;
            ">📄 PDF 원문 보기 (새 탭)</a>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.error("⚠️ 원본 PDF 파일이 서버에 없습니다.")

# -------------------------------------------------------------------------
# [추가] 2. PDF 파일 변경 신청 헬퍼 함수
# -------------------------------------------------------------------------
def request_pdf_change(new_pdf_filename, ori_file_name, old_pdf_filename, user_id):
    """일반 사용자의 기존 논문 변경 요청을 u_info에 기록합니다."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    try:
        save_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user_info = get_user_by_id(user_id)
        u_author = user_info[0] if user_info else ""
        
        cur.execute(
            """
            INSERT INTO u_info 
            (ORI_FILE_NAME, PDF_FILE_NAME, AUTHOR, ROLE, EMAIL, DONE, SAVE_DATE, ID, OLD_FILE_NAME) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (ori_file_name, new_pdf_filename, u_author, "PDF_CHANGE_REQUEST", "", 0, save_date, user_id, old_pdf_filename)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Change request error: {e}")
        return False
    finally:
        conn.close()

# 4. 파일 저장 로직
def save_paper(uploaded_file, upload_folder):
    # 파일 내용을 바이트로 읽음
    file_bytes = uploaded_file.getvalue()

    # 해시 계산 (이것이 물리적 파일명이 됨)
    file_hash = calculate_hash(file_bytes)
    physical_filename = f"{file_hash}.pdf"
    save_path = os.path.join(upload_folder, physical_filename)

    try:
        # A. 물리적 파일 저장 (이미 존재하면 건너뜀)
        if not os.path.exists(save_path):
            with open(save_path, "wb") as f:
                f.write(file_bytes)
            # 새로운 파일: 경로, 중복아님(False)
            return save_path, False
        else:
            # 중복 파일: 경로, 중복임(True)
            return save_path, True

    except Exception as e:
        st.error(f"에러 발생: {e}")
        return False

# [추가] 중복된 파일의 DB 정보를 가져오는 함수
def get_duplicate_paper_info(pdf_filename):
    conn = sqlite3.connect(DB_FILE)
    try:
        # c_info 테이블에서 파일명이 일치하는 정보 조회
        # (테이블 구조에 따라 컬럼명이 다를 수 있으나, 코드 흐름상 PDF_FILE_NAME을 키로 사용한다고 가정)
        query = f"SELECT * FROM c_info WHERE PDF_FILE_NAME = ?"
        df = pd.read_sql_query(query, conn, params=(pdf_filename,))
        return df
    except Exception as e:
        return pd.DataFrame()  # 에러 시 빈 데이터프레임 반환
    finally:
        conn.close()

def show_main_app_page():
    """논문 업로드 및 처리를 위한 메인 애플리케이션 페이지를 표시합니다."""
    
    if "file_uploader_key" not in st.session_state:
        st.session_state.file_uploader_key = 0

    def reset_upload_page():
        is_admin_mode = "admin_pdf_file" in st.session_state
        
        # [수정] 파일 유지 플래그(keep_temp_file) 확인 추가
        if not is_admin_mode and not st.session_state.get("show_save_success") and not st.session_state.get("keep_temp_file"):
            if not st.session_state.get("is_duplicate"): # 기존 존재하는 파일(해시중복)이 아닌 신규 파일만 삭제
                temp_pdf = st.session_state.get("temp_file_path")
                if temp_pdf:
                    delete_paper_files(os.path.basename(temp_pdf))

        if "admin_pdf_file" in st.session_state:
            del st.session_state["admin_pdf_file"]
        
        keys_to_reset = [
            "last_uploaded_file_id", "temp_file_path", "uploaded_file_name", 
            "is_duplicate", "last_json_path", "last_uploaded_pdf_path",
            "json_data", "a_paper_info", "c_paper_info",
            "a_paper_info_original", "c_paper_info_original",
            "extraction_done", "editing", "show_save_success", "dup_confirm_state",
            "title_dup_pdf", "title_dup_confirm_state", "keep_temp_file" # <--- [추가]
        ]
        for key in keys_to_reset:
            if key in st.session_state:
                del st.session_state[key]
        
        st.session_state.file_uploader_key += 1
        st.rerun()

    st.subheader("논문 업로드")

    is_admin_mode = "admin_pdf_file" in st.session_state
    
    if is_admin_mode:
        st.info(f"📢 **[접수처리 모드]** 파일 분석 중: {st.session_state.admin_ori_file}")
        if st.button("접수처리 모드 종료 (초기화)"):
            reset_upload_page()
        file_path = st.session_state.get("temp_file_path")
    else:
        uploaded_file = st.file_uploader(
            "PDF 파일을 드래그 앤 드롭하거나 클릭하여 업로드하세요.", 
            type=["pdf"],
            key=f"pdf_uploader_{st.session_state.file_uploader_key}"
        )

        if uploaded_file:
            if uploaded_file.file_id != st.session_state.get("last_uploaded_file_id"):
                st.session_state.show_save_success = False
                st.session_state.editing = False
                st.session_state.extraction_done = False
                st.session_state.dup_confirm_state = "CHECKING"

                os.makedirs(upload_folder, exist_ok=True)
                file_path, is_duplicate = save_paper(uploaded_file, upload_folder)
                
                st.session_state.temp_file_path = file_path
                st.session_state.last_uploaded_file_id = uploaded_file.file_id
                st.session_state.uploaded_file_name = uploaded_file.name
                st.session_state.is_duplicate = is_duplicate

            file_path = st.session_state.get("temp_file_path")

    if "extraction_done" not in st.session_state: st.session_state.extraction_done = False
    if "editing" not in st.session_state: st.session_state.editing = False
    if "show_save_success" not in st.session_state: st.session_state.show_save_success = False
    if "dup_confirm_state" not in st.session_state: st.session_state.dup_confirm_state = "CHECKING"

    # [1] 해시 중복 검사 및 처리
    if st.session_state.get("temp_file_path"):
        file_path = st.session_state.temp_file_path
        
        if not is_admin_mode and st.session_state.get("is_duplicate") and st.session_state.dup_confirm_state != "PROCEED":
            # [1] 해시 중복 검사 및 처리
            is_admin_user = (st.session_state.username == "AD00000")
            
            if not is_admin_mode and st.session_state.get("is_duplicate") and st.session_state.dup_confirm_state != "PROCEED":
                with st.container(border=True):
                    st.error("🚨 **이미 서버에 존재하는 논문 파일입니다.**")
                    
                    # [수정] 안내 문구 옆에 PDF 원문 보기 버튼 배치
                    pdf_filename = os.path.basename(st.session_state.temp_file_path)
                    col_info, col_pdf_btn = st.columns([0.7, 0.3])
                    with col_info:
                        st.info("기존 DB에 등록된 정보는 아래와 같습니다.")
                    with col_pdf_btn:
                        display_pdf_viewer_button(pdf_filename)
                        
                    existing_df = get_duplicate_paper_info(pdf_filename)
                    if not existing_df.empty:
                        st.dataframe(existing_df.T, use_container_width=True)
                    else:
                        st.warning("파일은 존재하나 DB에서 메타데이터를 찾을 수 없습니다.")
                    st.write("---")
                    
                    # [수정] 강제 업데이트 대신 변경 신청 방식 적용 (관리자는 덮어쓰기 허용)
                    if is_admin_user:
                        st.write("**[관리자 권한] 기존 데이터를 무시하고 추출을 계속 진행하시겠습니까?**")
                        col_y, col_n = st.columns(2)
                        if col_y.button("✅ 예 (계속 진행)", use_container_width=True):
                            st.session_state.dup_confirm_state = "PROCEED"
                            st.rerun()
                        if col_n.button("❌ 아니오 (업로드 취소)", use_container_width=True):
                            reset_upload_page()
                    else:
                        st.write("**본인이 작성한 논문 정보로 업데이트하려면 변경 신청을 진행해주세요.**")
                        col_y, col_n = st.columns(2)
                        if col_y.button("📤 PDF파일 변경 신청", use_container_width=True):
                            user_id = st.session_state.username
                            ori_fname = st.session_state.uploaded_file_name
                            if request_pdf_change(pdf_filename, ori_fname, pdf_filename, user_id):
                                st.session_state.keep_temp_file = True  # <--- [핵심 추가] 파일 삭제 방지
                                st.toast("✅ 변경 요청이 접수처리(관리자) 메뉴로 전달되었습니다.", icon="✅")
                                import time
                                time.sleep(1.5) # 토스트 메시지 확인을 위한 짧은 대기
                                reset_upload_page()
                            else:
                                st.error("요청 중 오류가 발생했습니다.")
                        if col_n.button("❌ 아니오 (업로드 취소)", use_container_width=True):
                            reset_upload_page()
                    st.stop()

        # [2] PDF 분석 및 JSON 저장
        if not st.session_state.get("last_json_path") or \
            os.path.basename(file_path).split(".")[0] not in st.session_state.get("last_json_path", ""):

            with st.spinner("PDF 분석 중..."):
                json_data, error = get_pdf_json(file_path, PDF_SERVICE_URL, REQUEST_TIMEOUT)

            st.session_state.last_uploaded_pdf_path = file_path

            if json_data:
                json_filename = f"{os.path.splitext(os.path.basename(file_path))[0]}.json"
                json_path = os.path.join(upload_folder, json_filename)
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=4)
                st.session_state.last_json_path = json_path

                if st.session_state.get("is_duplicate"):
                    st.success("기존 파일을 사용하여 분석을 완료했습니다.")
                else:
                    st.success(f"PDF 분석 결과가 '{json_filename}'에 저장되었습니다.")
            else:
                st.error(f"PDF 분석 실패: {error}")

    # [3] 서지정보 추출 버튼
    if st.session_state.get("last_json_path"):
        col_extract, col_reset1 = st.columns([0.7, 0.3])
        
        with col_extract:
            if st.button("서지정보 추출", key="extract_btn"):
                with st.spinner("논문 서지정보 추출 중..."):
                    json_data, a_info, c_info, fail_count, model_name = get_paper_df(st.session_state.last_json_path)
                json_name = os.path.basename(st.session_state.last_json_path)
                output_path = save_output_file(json_data, json_name, model_name, resolve_folder)
                
                if c_info is not None:
                    pdf_name = os.path.basename(st.session_state.last_uploaded_pdf_path)
                    ori_pdf_name = st.session_state.uploaded_file_name
                    json_name = os.path.basename(st.session_state.last_json_path)
                    llm_json_name = os.path.basename(output_path[0])
                    
                    new_rows = pd.DataFrame([
                        {"Key": "ORI_FILE_NAME", "Value": ori_pdf_name},
                        {"Key": "PDF_FILE_NAME", "Value": pdf_name},
                        {"Key": "JSON_FILE_NAME", "Value": json_name},
                        {"Key": "LLM_JSON_FILE_NAME", "Value": llm_json_name},
                    ])
                    c_info = pd.concat([c_info.drop(14, errors="ignore"), new_rows], ignore_index=True)
                    
                    a_info["ORI_FILE_NAME"] = ori_pdf_name
                    a_info["PDF_FILE_NAME"] = pdf_name
                    a_info["JSON_FILE_NAME"] = json_name
                    a_info["LLM_JSON_FILE_NAME"] = llm_json_name
                    
                    a_info = a_info[['AUTHOR', 'AFFILIATION', 'ROLE', 'ORI_FILE_NAME','PDF_FILE_NAME', 'JSON_FILE_NAME','LLM_JSON_FILE_NAME']]
                    
                    st.session_state.json_data = json_data
                    st.session_state.a_paper_info = a_info
                    st.session_state.c_paper_info = c_info
                    st.session_state.a_paper_info_original = a_info.copy()
                    st.session_state.c_paper_info_original = c_info.copy()
                    
                    # -------------------------------------------------------------
                    # [추가] 서지정보 추출 직후 제목 중복 체크
                    # -------------------------------------------------------------
                    extracted_title = c_info.loc[c_info['Key'] == 'TITLE', 'Value'].values[0] if 'TITLE' in c_info['Key'].values else ""
                    dup_pdf = check_title_duplicate_in_db(extracted_title, exclude_pdf_filename=pdf_name)
                    
                    if dup_pdf:
                        st.session_state.title_dup_pdf = dup_pdf
                        st.session_state.title_dup_confirm_state = "CHECKING"
                    else:
                        st.session_state.title_dup_confirm_state = "PROCEED"
                        
                    st.session_state.extraction_done = True
                    st.rerun()
                else:
                    st.error(f"서지정보 추출 실패. 실패 수: {fail_count}")

        with col_reset1:
            if st.button("초기화", key="reset_btn_1"):
                reset_upload_page()

    # [4] 결과 편집 및 저장 UI
    if st.session_state.extraction_done:
        st.write("---")
        
        # -------------------------------------------------------------
        # [추가] 논문 제목 중복 발생 시 경고 UI
        # -------------------------------------------------------------
        if st.session_state.get("title_dup_pdf") and st.session_state.get("title_dup_confirm_state") == "CHECKING":
            # -------------------------------------------------------------
            # [수정] 논문 제목 중복 발생 시 경고 UI
            # -------------------------------------------------------------
            if st.session_state.get("title_dup_pdf") and st.session_state.get("title_dup_confirm_state") == "CHECKING":
                with st.container(border=True):
                    st.error("🚨 **동일한 논문제목이 서버에 존재하고 있습니다.**")
                    
                    # [수정] 안내 문구 옆에 PDF 원문 보기 버튼 배치
                    dup_pdf = st.session_state.title_dup_pdf
                    col_info, col_pdf_btn = st.columns([0.7, 0.3])
                    with col_info:
                        st.info("기존 DB에 등록된 정보는 아래와 같습니다.")
                    with col_pdf_btn:
                        display_pdf_viewer_button(dup_pdf)
                    
                    existing_df = get_duplicate_paper_info(dup_pdf)
                    if not existing_df.empty:
                        st.dataframe(existing_df.T, use_container_width=True)
                    else:
                        st.warning("DB에서 메타데이터를 찾을 수 없습니다.")
                    
                    st.write("---")
                    
                    # [수정] 일반 사용자는 변경 신청, 관리자는 강제 덮어쓰기 허용
                    is_admin_user = (st.session_state.username == "AD00000")
                    if is_admin_user:
                        st.write("**[관리자 권한] 기존 데이터를 삭제하고 새로운 데이터로 덮어쓰시겠습니까?**")
                        col_y, col_n = st.columns(2)
                        if col_y.button("✅ 예 (기존 데이터 강제 덮어쓰기)", use_container_width=True):
                            delete_paper_files(dup_pdf)
                            conn = sqlite3.connect(DB_FILE)
                            cur = conn.cursor()
                            cur.execute("DELETE FROM c_info WHERE PDF_FILE_NAME = ?", (dup_pdf,))
                            cur.execute("DELETE FROM a_info WHERE PDF_FILE_NAME = ?", (dup_pdf,))
                            conn.commit()
                            conn.close()
                            
                            st.session_state.title_dup_confirm_state = "PROCEED"
                            st.success("기존 데이터가 삭제되었습니다. 서지정보를 확인 후 저장해주세요.")
                            st.rerun()
                    else:
                        st.write("**기존 논문을 업데이트하시려면 변경 신청을 진행해주세요.**")
                        col_y, col_n = st.columns(2)
                        
                        if col_y.button("📤 PDF파일 변경 신청", use_container_width=True):
                            user_id = st.session_state.username
                            new_pdf_fname = os.path.basename(st.session_state.temp_file_path)
                            ori_fname = st.session_state.uploaded_file_name
                            
                            if request_pdf_change(new_pdf_fname, ori_fname, dup_pdf, user_id):
                                st.session_state.keep_temp_file = True  # <--- [핵심 추가] 파일 삭제 방지
                                st.toast("✅ 변경 요청이 성공적으로 접수되었습니다.", icon="✅")
                                import time
                                time.sleep(1.5)
                                reset_upload_page()
                            else:
                                st.error("요청 처리 중 오류가 발생했습니다.")
                    
                    # '아니오' 버튼은 관리자/일반 공통
                    if col_n.button("❌ 아니오 (업로드 취소)", use_container_width=True):
                        reset_upload_page()
                
                st.stop() # 사용자가 선택하기 전까지 아래 UI(에디터)를 숨김
            # -------------------------------------------------------------

        # 이하 정상 진행 상태 (PROCEED)
        st.subheader("추출된 논문 서지정보")
        if st.session_state.editing:
            edited_c = st.data_editor(st.session_state.c_paper_info, key="c_editor", num_rows="dynamic")
            edited_a = st.data_editor(st.session_state.a_paper_info, key="a_editor", num_rows="dynamic")

            user_data = get_user_by_id(st.session_state.username)
            user_name = user_data[0] if user_data else ""
            my_eng_names = [nm for nm in user_data[10:14] if nm] if user_data else []

            extracted_authors = []
            if 'AUTHOR' in edited_a.columns:
                extracted_authors = edited_a['AUTHOR'].unique().tolist()
            
            def author_sort_key(name):
                for eng_name in my_eng_names:
                    if eng_name and str(name).strip().lower() == str(eng_name).strip().lower():
                        return 0
                return 1
            
            sorted_authors = sorted(extracted_authors, key=author_sort_key)
            
            default_index = 0
            if sorted_authors:
                is_match = False
                top_author = sorted_authors[0]
                for eng_name in my_eng_names:
                    if eng_name and str(top_author).strip().lower() == str(eng_name).strip().lower():
                        is_match = True
                        break
                if is_match:
                    default_index = 1
            
            selected_myself = st.selectbox(
                "본인 선택 (이 논문의 저자 중 본인을 선택하세요)", 
                options=["선택안함"] + sorted_authors,
                index=default_index
            )
            st.write("") 

            col1, col2 = st.columns([0.5, 0.5])
            
            if col1.button("저장", key="save_btn"):
                if selected_myself == "선택안함":
                    st.error("이 논문의 저자 중 본인을 선택하세요")
                else:
                    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    df_c_transposed = edited_c.set_index("Key").T.reset_index(drop=True)
                    df_c_transposed["SAVE_DATE"] = current_time
                    edited_a["SAVE_DATE"] = current_time
                    
                    if '이름' not in edited_a.columns: edited_a['이름'] = None
                    if '직원번호' not in edited_a.columns: edited_a['직원번호'] = None                       
                    edited_a.loc[edited_a['AUTHOR'] == selected_myself, '이름'] = user_name
                    edited_a.loc[edited_a['AUTHOR'] == selected_myself, '직원번호'] = st.session_state.username

                    key_cols = ["PDF_FILE_NAME"]
                    
                    try:
                        conn = sqlite3.connect(DB_FILE)
                        cur = conn.cursor()
                        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='a_info'")
                        if cur.fetchone():
                            cur.execute("PRAGMA table_info(a_info)")
                            columns = [info[1] for info in cur.fetchall()]
                            if '이름' not in columns: cur.execute("ALTER TABLE a_info ADD COLUMN 이름 TEXT")
                            if '직원번호' not in columns: cur.execute("ALTER TABLE a_info ADD COLUMN 직원번호 TEXT")
                            conn.commit()
                        conn.close()
                    except Exception as e:
                        print(f"Column check error: {e}")

                    c_saved = update_or_add_paper_data(df_c_transposed, "c_info", key_cols, user_id=st.session_state.username)
                    a_saved = update_or_add_paper_data(edited_a, "a_info", key_cols, user_id=st.session_state.username)

                    if c_saved and a_saved:
                        st.session_state.show_save_success = True
                        st.session_state.editing = False
                        st.session_state.c_paper_info_original = edited_c.copy()
                        st.session_state.a_paper_info_original = edited_a.copy()
                        st.rerun()

            if col2.button("취소", key="cancel_btn"):
                st.session_state.c_paper_info = st.session_state.c_paper_info_original
                st.session_state.a_paper_info = st.session_state.a_paper_info_original
                st.session_state.editing = False
                st.rerun()
        else:
            st.dataframe(st.session_state.c_paper_info)
            doi_value = st.session_state.c_paper_info.loc[st.session_state.c_paper_info["Key"] == "DOI", "Value"]
            if not doi_value.empty:
                st.link_button("🔗 DOI URL", url=doi_value.iloc[0])
            st.dataframe(st.session_state.a_paper_info[["ROLE", "AUTHOR", "AFFILIATION"]])

            col_edit, col_reset2 = st.columns([0.5, 0.5])
            with col_edit:
                if st.button("편집", key="edit_btn"):
                    st.session_state.show_save_success = False
                    st.session_state.editing = True
                    st.rerun()
            with col_reset2:
                if st.button("초기화", key="reset_btn_2"):
                    reset_upload_page()

            if st.session_state.show_save_success:
                st.success("데이터가 성공적으로 저장되었습니다!")

def show_user_management_page():
    """사용자 관리 페이지를 표시합니다."""
    st.subheader("사용자 관리")

    if "current_selected_user_id" not in st.session_state:
        st.session_state.current_selected_user_id = None
    if "user_mgmt_form_key" not in st.session_state:
        st.session_state.user_mgmt_form_key = 0

    with st.form(key=f"user_mgmt_form_{st.session_state.user_mgmt_form_key}"):
        st.markdown("#### 사용자 추가/편집")

        user_data = None
        if st.session_state.current_selected_user_id:
            user_data_tuple = get_user_by_id(st.session_state.current_selected_user_id)
            if user_data_tuple:
                user_data = dict(
                    zip(
                        [
                            "name",
                            "id",
                            "kri",
                            "hname",
                            "jkind",
                            "jrank",
                            "duty",
                            "dep",
                            "state",
                            "password",
                            "hname1",
                            "hname2",
                            "hname3",
                            "hname4",
                        ],
                        user_data_tuple,
                    )
                )

        is_editing = user_data is not None

        cols = st.columns(2)
        form_data = {
            "name": cols[0].text_input(
                "이름", value=user_data["name"] if is_editing else ""
            ),
            "id": cols[1].text_input(
                "ID", value=user_data["id"] if is_editing else "", disabled=is_editing
            ),
            "kri": cols[0].text_input(
                "KRI", value=user_data["kri"] if is_editing else ""
            ),
            "hname": cols[1].text_input(
                "한글이름", value=user_data["hname"] if is_editing else ""
            ),
            "jkind": cols[0].text_input(
                "직종", value=user_data["jkind"] if is_editing else ""
            ),
            "jrank": cols[1].text_input(
                "직급", value=user_data["jrank"] if is_editing else ""
            ),
            "duty": cols[0].text_input(
                "직위", value=user_data["duty"] if is_editing else ""
            ),
            "dep": cols[1].text_input(
                "부서", value=user_data["dep"] if is_editing else ""
            ),
            "state": cols[0].text_input(
                "상태", value=user_data["state"] if is_editing else ""
            ),
            "password": cols[1].text_input(
                "비밀번호",
                type="password",
                help="새 사용자는 필수. 편집 시 비워두면 기존 비밀번호 유지.",
            ),
        }

        c1, c2, c3 = st.columns([0.3, 0.3, 0.4])
        save_btn = c1.form_submit_button("저장")
        cancel_btn = c2.form_submit_button("취소")
        reset_pwd_btn = (
            c3.form_submit_button("비밀번호 초기화") if is_editing else False
        )

        if save_btn:
            # [수정] 사용자 ID 전달 (관리자)
            success, message = add_or_update_user(form_data, not is_editing, user_id=st.session_state.username)
            if success:
                st.success(
                    f"사용자 '{form_data['id']}'가 {'업데이트' if is_editing else '추가'}되었습니다."
                )
                st.session_state.current_selected_user_id = None
                st.session_state.user_mgmt_form_key += 1
                st.rerun()
            else:
                st.error(message)
        if cancel_btn:
            st.session_state.current_selected_user_id = None
            st.session_state.user_mgmt_form_key += 1
            st.rerun()
        if reset_pwd_btn:
            reset_pw = form_data["id"] + "!!"
            update_password(form_data["id"], reset_pw)
            st.success(
                f"'{form_data['id']}'의 비밀번호가 '{reset_pw}'로 초기화되었습니다."
            )
            st.session_state.current_selected_user_id = None
            st.session_state.user_mgmt_form_key += 1
            st.rerun()

    st.markdown("---")
    st.markdown("#### 현재 사용자 목록")
    df_users = get_all_users_data()
    if not df_users.empty:
        df_display = df_users.drop(columns=["password"])
        selected = st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            selection_mode="single-row",
            on_select="rerun",
            key="user_table",
        )
        if selected and selected["selection"]["rows"]:
            sel_id = df_display.iloc[selected["selection"]["rows"][0]]["id"]
            st.session_state.current_selected_user_id = sel_id
            st.rerun()

# [추가] 관리자용 전체 논문 조회 함수
def get_all_papers():
    """관리자용: 전체 논문 리스트 조회 (c_info + a_info 저자/이름 통합)"""
    conn = sqlite3.connect(DB_FILE)
    try:
        # [수정] 저자(영문)와 이름(한글)을 모두 합쳐서 SEARCH_AUTHORS로 만듦
        # IFNULL을 사용하여 NULL 값 처리 (SQLite 호환)
        query = """
            SELECT c.*, 
                GROUP_CONCAT(IFNULL(a.AUTHOR, '') || ' ' || IFNULL(a.이름, ''), ', ') as SEARCH_AUTHORS
            FROM c_info c
            LEFT JOIN a_info a ON c.PDF_FILE_NAME = a.PDF_FILE_NAME
            GROUP BY c.PDF_FILE_NAME
            ORDER BY c.PUBLICATION_YEAR DESC, c.TITLE
        """
        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        st.error(f"전체 논문 조회 중 오류: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

# [수정] 통계 대시보드 표시 함수
def show_dashboard(df, is_admin=False):
    # --- 스타일 설정 ---
    COLOR_SEQ = px.colors.qualitative.Pastel
    ADMIN_COLOR = px.colors.qualitative.Prism
    
    st.markdown("## 📊 논문 통계 대시보드")
    
    if df.empty:
        st.info("통계를 표시할 데이터가 없습니다.")
        return

    # --- 1. 상단 KPI (핵심 지표) ---
    st.markdown("### 📌 핵심 요약")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    
    total_papers = len(df) 
    
    current_year = datetime.datetime.now().year
    this_year_papers = len(df[df['PUBLICATION_YEAR'].astype(str) == str(current_year)])
    
    first_author_cnt = 0
    corres_author_cnt = 0
    if 'ROLE' in df.columns:
        first_author_cnt = len(df[df['ROLE'] == 'FIRST_AUTHOR'])
        corres_author_cnt = len(df[df['ROLE'] == 'CORRESPONDING_AUTHOR'])

    kpi1.metric("총 논문 수", f"{total_papers}편", delta=f"올해 {this_year_papers}편")
    
    if not is_admin and 'ROLE' in df.columns:
        kpi2.metric("주저자(1저자)", f"{first_author_cnt}편", help="First Author")
        kpi3.metric("교신저자", f"{corres_author_cnt}편", help="Corresponding Author")
        contribution_rate = ((first_author_cnt + corres_author_cnt) / total_papers * 100) if total_papers > 0 else 0
        kpi4.metric("주요 기여율", f"{contribution_rate:.1f}%")
    else:
        unique_journals = df['JOURNAL_NAME'].nunique() if 'JOURNAL_NAME' in df.columns else 0
        kpi2.metric("등재 저널 수", f"{unique_journals}개")
        kpi3.metric("DB 업데이트", "실시간")
        kpi4.metric("관리 모드", "ON")

    st.markdown("---")

    # --- 2. 그래프 영역 ---
    tab1, tab2, tab3 = st.tabs(["📈 연도별/성장 추이", "📖 저널 및 토픽 분석", "👥 역할 및 저자 분석"])

    with tab1:
        col_y1, col_y2 = st.columns([0.6, 0.4])
        
        # [Chart 1] 연도별 발행 수 (Bar + Line)
        if 'PUBLICATION_YEAR' in df.columns:
            year_counts = df['PUBLICATION_YEAR'].astype(str).value_counts().sort_index().reset_index()
            year_counts.columns = ['Year', 'Count']
            
            # 누적 합계 계산
            year_counts['Cumulative'] = year_counts['Count'].cumsum()

            with col_y1:
                st.markdown("#### 📅 연도별 발행 및 성장 추이")
                fig_year = go.Figure()
                fig_year.add_trace(go.Bar(
                    x=year_counts['Year'], y=year_counts['Count'],
                    name='연간 논문 수',
                    marker_color='#636EFA',
                    opacity=0.8
                ))
                fig_year.add_trace(go.Scatter(
                    x=year_counts['Year'], y=year_counts['Cumulative'],
                    name='누적 논문 수',
                    yaxis='y2',
                    line=dict(color='#EF553B', width=3),
                    mode='lines+markers'
                ))
                
                fig_year.update_layout(
                    xaxis=dict(title='연도'),
                    yaxis=dict(title='연간 편수', showgrid=False),
                    yaxis2=dict(title='누적 편수', overlaying='y', side='right', showgrid=False),
                    legend=dict(x=0.01, y=0.99),
                    template="plotly_white",
                    hovermode="x unified",
                    height=400
                )
                st.plotly_chart(fig_year, use_container_width=True)

            with col_y2:
                # [Chart 2] 최근 7년 집중 분석 (Donut Chart)
                st.markdown("#### 🔥 최근 7년 비중")
                
                # None 값을 제외하고 정렬 (에러 해결)
                valid_years = df['PUBLICATION_YEAR'].dropna().unique()
                recent_years = sorted(valid_years, reverse=True)[:7]
                
                recent_df = df[df['PUBLICATION_YEAR'].isin(recent_years)]
                
                if not recent_df.empty:
                    # [수정 시작] -------------------------------------------------------
                    # 1. 연도별 개수를 집계하고 연도순(오름차순)으로 정렬합니다.
                    #    (value_counts()로 세고, sort_index()로 연도 정렬)
                    pie_data = recent_df['PUBLICATION_YEAR'].value_counts().sort_index().reset_index()
                    pie_data.columns = ['PUBLICATION_YEAR', 'Count']

                    # 2. 집계된 데이터(pie_data)를 사용하여 차트를 그립니다.
                    fig_recent = px.pie(
                        pie_data, 
                        names='PUBLICATION_YEAR', 
                        values='Count', # 집계된 개수 값을 지정
                        hole=0.4,
                        color_discrete_sequence=px.colors.sequential.RdBu
                    )
                    
                    # 3. sort=False를 설정하여 값의 크기가 아닌 '데이터의 순서(연도순)'대로 표시합니다.
                    fig_recent.update_traces(textposition='inside', textinfo='percent+label', sort=False)
                    # [수정 끝] ---------------------------------------------------------
                    
                    fig_recent.update_layout(showlegend=False, margin=dict(t=20, b=20, l=20, r=20), height=350)
                    st.plotly_chart(fig_recent, use_container_width=True)
                else:
                    st.info("최근 7년 데이터가 없습니다.")

    with tab2:
        col_j1, col_j2 = st.columns([0.5, 0.5])
        
        # [Chart 3] 주요 저널 TOP 10
        if 'JOURNAL_NAME' in df.columns:
            journal_counts = df['JOURNAL_NAME'].value_counts().head(10).reset_index()
            journal_counts.columns = ['Journal', 'Count']
            
            with col_j1:
                st.markdown("#### 🏆 Top 10 저널")
                fig_journal = px.bar(
                    journal_counts, 
                    x='Count', 
                    y='Journal', 
                    orientation='h',
                    text='Count',
                    color='Count',
                    color_continuous_scale='Blues'
                )
                fig_journal.update_layout(
                    yaxis={'categoryorder':'total ascending'},
                    xaxis_title="논문 수",
                    yaxis_title="",
                    coloraxis_showscale=False,
                    template="plotly_white",
                    height=500
                )
                st.plotly_chart(fig_journal, use_container_width=True)

        # [Chart 4] 논문 제목 워드클라우드 (Treemap)
        if 'TITLE' in df.columns:
            with col_j2:
                st.markdown("#### 🧠 주요 연구 키워드 (Top 20)")
                
                all_titles = " ".join(df['TITLE'].dropna().astype(str).tolist()).lower()
                all_titles = re.sub(r'[^\w\s]', '', all_titles)
                words = all_titles.split()
                
                stopwords = set(['the', 'of', 'and', 'in', 'to', 'a', 'with', 'for', 'on', 'by', 'an', 'at', 'study', 'analysis', 'using', 'between', 'during', 'associated', 'clinical', 'patients','after','from','report','outcomes','case','acute','treatment','association','multicenter','disease','risk','effect','factors','model','comparison','trial','effects','impact','early','review','characteristics'])
                # [추가] 유사 단어 병합 매핑 (입력 단어 -> 표시될 단어)
                merge_keywords = {
                    'cell': 'cell/cells', 'cells': 'cell/cells',
                    'korea': 'korea/korean', 'korean': 'korea/korean'
                }                
                filtered_words = []
                for w in words:
                    if w not in stopwords and len(w) > 2:
                        # 매핑 테이블에 있으면 변환된 값 사용, 없으면 원래 단어 사용
                        final_word = merge_keywords.get(w, w)
                        filtered_words.append(final_word)
                
                word_counts = Counter(filtered_words).most_common(20)
                word_df = pd.DataFrame(word_counts, columns=['Keyword', 'Frequency'])
                # print(word_df)
                
                if not word_df.empty:
                    fig_word = px.treemap(
                        word_df, 
                        path=['Keyword'], 
                        values='Frequency',
                        color='Frequency',
                        color_continuous_scale='Teal'
                    )
                    fig_word.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=500)
                    st.plotly_chart(fig_word, use_container_width=True)
                else:
                    st.info("키워드를 추출할 수 없습니다.")

    with tab3:
        if is_admin:
            # 관리자 모드: 저자별 통계
            st.markdown("#### 👨‍🔬 전체 저자 활동 순위")
            try:
                conn = sqlite3.connect(DB_FILE)
                q = """
                    SELECT AUTHOR as '저자명', COUNT(*) as '논문수',
                    SUM(CASE WHEN ROLE='FIRST_AUTHOR' THEN 1 ELSE 0 END) as '1저자',
                    SUM(CASE WHEN ROLE='CORRESPONDING_AUTHOR' THEN 1 ELSE 0 END) as '교신저자'
                    FROM a_info 
                    GROUP BY AUTHOR 
                    ORDER BY COUNT(*) DESC 
                    LIMIT 20
                """
                author_stats = pd.read_sql_query(q, conn)
                conn.close()
                
                if not author_stats.empty:
                    fig_auth = go.Figure()
                    fig_auth.add_trace(go.Bar(
                        x=author_stats['저자명'], y=author_stats['논문수'],
                        name='총 논문 수', marker_color='#E2E2E2'
                    ))
                    fig_auth.add_trace(go.Scatter(
                        x=author_stats['저자명'], y=author_stats['1저자'],
                        name='1저자 수', mode='markers', marker=dict(size=10, color='red')
                    ))
                    fig_auth.add_trace(go.Scatter(
                        x=author_stats['저자명'], y=author_stats['교신저자'],
                        name='교신저자 수', mode='markers', marker=dict(size=10, color='blue')
                    ))
                    fig_auth.update_layout(
                        template="plotly_white", 
                        xaxis_tickangle=-45,
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )
                    st.plotly_chart(fig_auth, use_container_width=True)
                    
                    with st.expander("상세 데이터 보기"):
                        st.dataframe(author_stats, use_container_width=True)
                else:
                    st.info("저자 데이터가 없습니다.")
            except Exception as e:
                st.error(f"저자 통계 오류: {e}")
        
        else:
            # 개인 모드: 역할 비중 및 DOI 현황
            col_r1, col_r2 = st.columns(2)
            
            with col_r1:
                if 'ROLE' in df.columns:
                    st.markdown("#### 👤 내 역할(Role) 분포")
                    role_counts = df['ROLE'].value_counts().reset_index()
                    role_counts.columns = ['Role', 'Count']
                    
                    role_map = {
                        'FIRST_AUTHOR': '제1저자', 
                        'CORRESPONDING_AUTHOR': '교신저자', 
                        'CO_AUTHOR': '공동저자'
                    }
                    role_counts['Role_Name'] = role_counts['Role'].map(role_map).fillna(role_counts['Role'])
                    
                    fig_role = px.sunburst(
                        role_counts, 
                        path=['Role_Name'], 
                        values='Count',
                        color='Role_Name',
                        color_discrete_sequence=px.colors.qualitative.Set2
                    )
                    fig_role.update_layout(height=400)
                    st.plotly_chart(fig_role, use_container_width=True)

            with col_r2:
                if 'DOI' in df.columns:
                    st.markdown("#### 🌐 DOI 등록 현황")
                    has_doi = df['DOI'].apply(lambda x: "등록됨" if x and str(x).strip() else "미등록")
                    doi_counts = has_doi.value_counts().reset_index()
                    doi_counts.columns = ['Status', 'Count']
                    
                    fig_doi = px.bar(
                        doi_counts, 
                        x='Status', 
                        y='Count', 
                        color='Status', 
                        text='Count',
                        color_discrete_map={'등록됨': '#00CC96', '미등록': '#EF553B'}
                    )
                    fig_doi.update_layout(template="plotly_white", height=400)
                    st.plotly_chart(fig_doi, use_container_width=True)

def show_my_papers_page():
    """로그인한 사용자의 논문 리스트 및 통계를 보여주는 페이지"""
    
    current_theme_name = st.session_state.get("current_theme", "Professional Navy (기본)")
    if current_theme_name not in THEMES:
        current_theme_name = "Professional Navy (기본)"
    theme = THEMES[current_theme_name]

    # 1. 관리자 여부 확인
    is_admin = (st.session_state.username == "AD00000")
    
    if is_admin:
        st.subheader("전체 논문 리스트 (관리자) 🗂️")
    else:
        st.subheader("나의 논문 리스트 📚")
    
    # 필터 상태 초기화
    if "search_filters" not in st.session_state:
        st.session_state.search_filters = {
            "title": "", "author": "", "year": "전체", "dept": "전체", "journal": "전체", "applied": False
        }
    
    # [상태 변수] PDF 변경 모드
    if "change_pdf_mode" not in st.session_state:
        st.session_state.change_pdf_mode = False
    if "target_pdf_row_idx" not in st.session_state:
        st.session_state.target_pdf_row_idx = None

    # [상태 변수] 관리자 편집 모드
    if "admin_paper_editing" not in st.session_state:
        st.session_state.admin_paper_editing = False
    if "admin_edit_target_pdf" not in st.session_state:
        st.session_state.admin_edit_target_pdf = None

    # 2. 데이터 가져오기
    if is_admin:
        df_base = get_all_papers()
        display_cols = ['TITLE', 'PUBLICATION_YEAR', 'JOURNAL_NAME', 'SEARCH_AUTHORS', 'DOI', 'PDF_FILE_NAME']
    else:
        user_data = get_user_by_id(st.session_state.username)
        if user_data:
            user_name = user_data[0] 
            user_id = user_data[1] 
            df_base = get_my_papers(user_name, user_id)
            display_cols = ['AUTHOR', 'ROLE', 'AFFILIATION', 'TITLE', 'PUBLICATION_YEAR', 'JOURNAL_NAME', 'DOI', 'PDF_FILE_NAME']
        else:
            st.error("사용자 프로필 정보를 불러올 수 없습니다.")
            return

    # 탭 배치
    tab_list, tab_dash = st.tabs(["📄 리스트 보기", "📊 통계 대시보드"])

    # --- [탭 1] 리스트 보기 및 검색 ---
    with tab_list:
        
        filter_opts = get_filter_options()
        years = ["전체"] + filter_opts["years"]
        journals = ["전체"] + filter_opts["journals"]
        depts = ["전체"] + filter_opts["depts"]

        with st.container(border=True):
            st.markdown("#### 🔍 논문 검색")
            with st.form(key="search_form"):
                if is_admin:
                    col1, col2, col3 = st.columns([1.5, 1, 1])
                    with col1:
                        search_title = st.text_input("논문명 (포함 검색)", value=st.session_state.search_filters["title"])
                    with col2:
                        search_author = st.text_input("저자명", value=st.session_state.search_filters["author"])
                    with col3:
                        curr_yr = st.session_state.search_filters["year"]
                        idx_yr = years.index(curr_yr) if curr_yr in years else 0
                        search_year = st.selectbox("발행년도", years, index=idx_yr)
                    
                    col4, col5 = st.columns([1, 1.5])
                    with col4:
                        curr_dept = st.session_state.search_filters["dept"]
                        idx_dept = depts.index(curr_dept) if curr_dept in depts else 0
                        search_dept = st.selectbox("부서 (직원정보 기준)", depts, index=idx_dept)
                    with col5:
                        curr_jrn = st.session_state.search_filters["journal"]
                        idx_jrn = journals.index(curr_jrn) if curr_jrn in journals else 0
                        search_journal = st.selectbox("저널명", journals, index=idx_jrn)
                else:
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        search_title = st.text_input("논문명 (포함 검색)", value=st.session_state.search_filters["title"])
                    with col2:
                        curr_yr = st.session_state.search_filters["year"]
                        idx_yr = years.index(curr_yr) if curr_yr in years else 0
                        search_year = st.selectbox("발행년도", years, index=idx_yr)
                    with col3:
                        curr_jrn = st.session_state.search_filters["journal"]
                        idx_jrn = journals.index(curr_jrn) if curr_jrn in journals else 0
                        search_journal = st.selectbox("저널명", journals, index=idx_jrn)
                    
                    search_dept = "전체"
                    search_author = ""

                st.write("") 
                c_btn1, c_btn2 = st.columns(2)
                with c_btn1:
                    search_pressed = st.form_submit_button("검색", type="primary", use_container_width=True)
                with c_btn2:
                    reset_pressed = st.form_submit_button("검색 조건 초기화", type="secondary", use_container_width=True)

            if reset_pressed:
                st.session_state.search_filters = {
                    "title": "", "author": "", "year": "전체", "dept": "전체", "journal": "전체", "applied": False
                }
                st.session_state.change_pdf_mode = False
                st.session_state.admin_paper_editing = False 
                st.rerun()
            elif search_pressed:
                st.session_state.search_filters = {
                    "title": search_title,
                    "author": search_author,
                    "year": search_year,
                    "dept": search_dept,
                    "journal": search_journal,
                    "applied": True
                }
                st.session_state.change_pdf_mode = False
                st.session_state.admin_paper_editing = False
                st.rerun()

        # 데이터 필터링 로직
        df_view = df_base.copy()
        if not df_view.empty and st.session_state.search_filters["applied"]:
            f = st.session_state.search_filters
            if f["title"]:
                df_view = df_view[df_view['TITLE'].str.contains(f["title"], case=False, na=False)]
            if f["year"] != "전체":
                df_view = df_view[df_view['PUBLICATION_YEAR'].astype(str) == f["year"]]
            if f["journal"] != "전체":
                df_view = df_view[df_view['JOURNAL_NAME'] == f["journal"]]
            if is_admin and f["author"]:
                if 'SEARCH_AUTHORS' in df_view.columns:
                    df_view = df_view[df_view['SEARCH_AUTHORS'].str.contains(f["author"], case=False, na=False)]
                elif 'AUTHOR_LIST' in df_view.columns:
                    df_view = df_view[df_view['AUTHOR_LIST'].str.contains(f["author"], case=False, na=False)]
            if is_admin and f["dept"] != "전체":
                try:
                    conn = sqlite3.connect(DB_FILE)
                    cur = conn.cursor()
                    cur.execute("SELECT id FROM user_info WHERE dep = ?", (f["dept"],))
                    dept_user_ids = [row[0] for row in cur.fetchall()]
                    conn.close()
                    if dept_user_ids:
                        conn = sqlite3.connect(DB_FILE)
                        placeholders = ','.join(['?'] * len(dept_user_ids))
                        q_paper = f"SELECT DISTINCT PDF_FILE_NAME FROM a_info WHERE 직원번호 IN ({placeholders})"
                        target_pdfs_df = pd.read_sql_query(q_paper, conn, params=tuple(dept_user_ids))
                        conn.close()
                        target_pdfs = target_pdfs_df['PDF_FILE_NAME'].tolist()
                        df_view = df_view[df_view['PDF_FILE_NAME'].isin(target_pdfs)]
                    else:
                        df_view = pd.DataFrame() 
                except Exception as e:
                    st.error(f"부서 검색 오류: {e}")

        # 결과 리스트 출력
        if df_view.empty:
            st.info("검색 결과가 없습니다.")
        else:
            st.success(f"총 {len(df_view)}건의 논문이 있습니다.")
            
            df_view = df_view.reset_index(drop=True)
            df_view['연번'] = df_view.index + 1

            valid_cols = [c for c in display_cols if c in df_view.columns]
            
            rename_map = {
                'TITLE': '논문 제목', 'PUBLICATION_YEAR': '발행년도', 'JOURNAL_NAME': '저널명', 
                'SEARCH_AUTHORS': '저자 목록 (영문/한글)', 'AUTHOR_LIST': '저자 목록',
                'AUTHOR': '저자', 'ROLE': '역할', 'AFFILIATION': '소속', 'DOI': 'DOI'
            }
            final_view = df_view[['연번'] + valid_cols].rename(columns=rename_map)

            event = st.dataframe(
                final_view, 
                use_container_width=True, 
                hide_index=True,
                selection_mode="single-row",
                on_select="rerun",
                key="my_papers_table",
                height=600
            )

            # 상세 보기 및 기능 버튼
            if event.selection["rows"]:
                idx = event.selection["rows"][0]
                
                # 다른 행을 선택하면 각종 모드 초기화
                if st.session_state.target_pdf_row_idx != idx:
                    st.session_state.change_pdf_mode = False
                    st.session_state.admin_paper_editing = False # 편집 모드 초기화
                    st.session_state.target_pdf_row_idx = idx

                row = df_view.iloc[idx]
                
                pdf_fname = row.get("PDF_FILE_NAME")
                doi_value = row.get("DOI")
                title = row.get("TITLE")

                # --- 1) 기본 보기 모드 (편집 중이 아닐 때) ---
                if not st.session_state.admin_paper_editing:
                    st.markdown("---")
                    st.markdown(f"##### 📄 선택된 논문: {title}")

                    # [수정] 4개의 버튼 영역을 1:1:1:1 (동일 비율)로 배치하도록 수정
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        display_pdf_viewer_button(pdf_fname)

                    with col2:
                        if doi_value and str(doi_value).strip():
                            doi_str = str(doi_value).strip()
                            doi_url = doi_str if doi_str.startswith("http") else f"https://doi.org/{doi_str}"
                            st.link_button("🌐 DOI 사이트", doi_url, use_container_width=True)
                        else:
                            st.button("DOI 없음", disabled=True, use_container_width=True)

                    with col3:
                        if is_admin:
                            if st.button("✏️ 논문 정보 편집/삭제 (관리자)", use_container_width=True, type="secondary"):
                                st.session_state.admin_paper_editing = True
                                st.session_state.admin_edit_target_pdf = pdf_fname
                                st.rerun()
                        else:
                            if st.button("📤 PDF 파일 변경 신청", use_container_width=True, type="primary"):
                                st.session_state.change_pdf_mode = not st.session_state.change_pdf_mode
                    # [추가] PDF 삭제 기능 영역
                    with col4:
                        # 관리자는 col3에서 이미 "편집/삭제" 기능을 제공하므로 일반 사용자에게만 노출
                        if not is_admin:
                            if st.button("🗑️ PDF 삭제", use_container_width=True, type="primary"):
                                try:
                                    conn = sqlite3.connect(DB_FILE)
                                    cur = conn.cursor()
                                    
                                    # 1. DB (c_info, a_info) 에서 현재 논문 데이터 삭제
                                    cur.execute("DELETE FROM c_info WHERE PDF_FILE_NAME = ?", (pdf_fname,))
                                    cur.execute("DELETE FROM a_info WHERE PDF_FILE_NAME = ?", (pdf_fname,))
                                    conn.commit()
                                    conn.close()
                                    # 2. 파일 삭제
                                    delete_paper_files(pdf_fname)
                                    # # 2. 서버 스토리지에 있는 파일도 함께 삭제 (디스크 확보)
                                    # pdf_path = os.path.join(upload_folder, pdf_fname)
                                    # if os.path.exists(pdf_path):
                                    #     os.remove(pdf_path)
                                        
                                    # json_fname = f"{os.path.splitext(pdf_fname)[0]}.json"
                                    # json_path = os.path.join(upload_folder, json_fname)
                                    # if os.path.exists(json_path):
                                    #     os.remove(json_path)
                                    # if os.path.exists(resolve_folder):
                                    #     file_hash = os.path.splitext(pdf_fname)[0]
                                    #     for f in os.listdir(resolve_folder):
                                    #         if file_hash in f:
                                    #             try: os.remove(os.path.join(resolve_folder, f))
                                    #             except: pass                                        

                                    # 상태 변수 초기화 및 리스트 갱신
                                    st.success(f"✅ 데이터가 성공적으로 삭제되었습니다: {title}")
                                    st.session_state.target_pdf_row_idx = None
                                    st.session_state.change_pdf_mode = False
                                    st.rerun()
                                    
                                except Exception as e:
                                    st.error(f"❌ 데이터 삭제 중 오류가 발생했습니다: {e}")

                    if not is_admin and st.session_state.change_pdf_mode:
                        st.info("💡 교체할 새로운 PDF 파일을 업로드하세요. (접수처리 메뉴로 전송됩니다)")
                        new_pdf = st.file_uploader("교체할 PDF 업로드", type=["pdf"], key="change_pdf_uploader")
                        
                        if new_pdf:
                            file_bytes = new_pdf.getvalue()
                            file_hash = calculate_hash(file_bytes)
                            new_pdf_filename = f"{file_hash}.pdf"
                            save_path = os.path.join(upload_folder, new_pdf_filename)
                            if not os.path.exists(save_path):
                                with open(save_path, "wb") as f:
                                    f.write(file_bytes)
                            
                            try:
                                conn = sqlite3.connect(DB_FILE)
                                cur = conn.cursor()
                                save_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                user_info = get_user_by_id(st.session_state.username)
                                u_id = st.session_state.username
                                u_author = user_info[0] if user_info else ""
                                
                                cur.execute(
                                    """
                                    INSERT INTO u_info 
                                    (ORI_FILE_NAME, PDF_FILE_NAME, AUTHOR, ROLE, EMAIL, DONE, SAVE_DATE, ID, OLD_FILE_NAME) 
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    """,
                                    (new_pdf.name, new_pdf_filename, u_author, "PDF_CHANGE_REQUEST", "", 0, save_date, u_id, pdf_fname)
                                )
                                conn.commit()
                                conn.close()
                                st.success("✅ 변경 요청이 접수처리(관리자) 신청되었습니다.")
                                st.session_state.change_pdf_mode = False 
                            except Exception as e:
                                st.error(f"DB 저장 중 오류: {e}")

                # --- 2) 관리자 편집 모드 (편집 버튼 누른 후) ---
                elif is_admin and st.session_state.admin_paper_editing and st.session_state.admin_edit_target_pdf == pdf_fname:
                    st.markdown("---")
                    st.markdown(f"#### ✏️ 논문 정보 편집: {title}")
                    st.info("💡 'c_info'(서지정보)와 'a_info'(저자정보)를 직접 수정할 수 있습니다.")

                    conn = sqlite3.connect(DB_FILE)
                    try:
                        c_query = "SELECT * FROM c_info WHERE PDF_FILE_NAME = ?"
                        c_df_edit = pd.read_sql_query(c_query, conn, params=(pdf_fname,))
                        
                        a_query = "SELECT * FROM a_info WHERE PDF_FILE_NAME = ?"
                        a_df_edit = pd.read_sql_query(a_query, conn, params=(pdf_fname,))
                        # [수정] ROLE 기준 정렬 (FIRST -> CORRESPONDING -> CO_AUTHOR)
                        if not a_df_edit.empty and 'ROLE' in a_df_edit.columns:
                            role_order = {"FIRST_AUTHOR": 1, "CORRESPONDING_AUTHOR": 2, "CO_AUTHOR": 3,"FIRST&CORRESPONDING_AUTHOR": 4, "SINGLE_AUTHOR": 5}
                            a_df_edit['ROLE_SORT'] = a_df_edit['ROLE'].map(role_order).fillna(99)
                            a_df_edit = a_df_edit.sort_values(by=['ROLE_SORT']).drop(columns=['ROLE_SORT'])                        
                    except Exception as e:
                        st.error(f"데이터 로드 실패: {e}")
                        c_df_edit = pd.DataFrame()
                        a_df_edit = pd.DataFrame()
                    finally:
                        conn.close()

                    # [수정] c_info 전치 (Transpose)하여 보기 좋게 표시
                    # 가로로 긴 데이터를 세로형(Key-Value)으로 변환
                    if not c_df_edit.empty:
                        # T (Transpose) -> reset_index -> 컬럼명 변경
                        c_df_transposed = c_df_edit.T.reset_index()
                        c_df_transposed.columns = ["Key", "Value"]
                        # [수정] 데이터 에디터 입력 오류 방지를 위해 Value 컬럼을 문자열로 변환
                        c_df_transposed["Value"] = c_df_transposed["Value"].fillna("").astype(str)
                    else:
                        c_df_transposed = pd.DataFrame(columns=["Key", "Value"])

                    st.markdown("**1. 서지정보 (c_info)**")
                    
                    # [수정] 앞의 5개, 뒤의 4개 컬럼 숨기기
                    if len(c_df_transposed) > 9:
                        c_df_display = c_df_transposed.iloc[5:-4]
                    else:
                        c_df_display = c_df_transposed.iloc[5:] if len(c_df_transposed) > 5 else c_df_transposed
                    
                    # [수정] 데이터 에디터 설정
                    # Key 컬럼은 수정 불가능하게(disabled), Value 컬럼만 수정 가능하게 설정
                    edited_c_transposed = st.data_editor(
                        c_df_display,
                        key="admin_edit_c",
                        use_container_width=True,
                        column_config={
                            "Key": st.column_config.TextColumn("필드명 (Key)", disabled=True),
                            "Value": st.column_config.TextColumn("값 (Value)")
                        },
                        hide_index=True
                    )
                    
                    st.markdown("**2. 저자정보 (a_info)**")
                    # [수정] 앞의 5개, 뒤의 4개 컬럼 숨기기
                    a_cols_head = a_df_edit.columns[:5]
                    a_cols_tail = a_df_edit.columns[-4:]
                    a_cols_to_hide_all = list(a_cols_head) + list(a_cols_tail)
                    a_df_display = a_df_edit.drop(columns=a_cols_to_hide_all, errors='ignore')
                    
                    edited_a = st.data_editor(a_df_display, key="admin_edit_a", num_rows="dynamic", use_container_width=True)

                    st.write("") 

                    col_save, col_cancel, col_delete = st.columns([0.4, 0.3, 0.3])

                    # [저장]
                    with col_save:
                        if st.button("💾 저장 (DB 반영)", type="primary", use_container_width=True):
                            key_cols = ["PDF_FILE_NAME"]
                            try:
                                # [수정] 전치된 c_info를 다시 원래의 가로 형태(DB 구조)로 복원
                                # "Key" 컬럼을 인덱스로 설정하고 전치(.T)
                                # c_df_restored = edited_c_transposed.set_index("Key").T
                                c_df_restored_partial = edited_c_transposed.set_index("Key").T
                                
                                # [수정] 숨겨진 컬럼 복원 (c_info)
                                c_df_final = c_df_edit.copy()
                                for col in c_df_restored_partial.columns:
                                    c_df_final[col] = c_df_restored_partial[col].values

                                # [수정] 숨겨진 컬럼 복원 (a_info)
                                for col in a_cols_head:
                                    if col in c_df_edit.columns:
                                        edited_a[col] = c_df_edit[col].iloc[0]

                                # 복원된 데이터프레임의 인덱스를 리셋하거나 그대로 사용 (update 함수 로직에 맞춤)
                                # update_or_add_paper_data는 컬럼명 매칭으로 동작하므로 인덱스 이름은 상관없음
                                
                                # [수정] 사용자 ID 전달 (이력 관리)
                                c_saved = update_or_add_paper_data(c_df_final, "c_info", key_cols, user_id=st.session_state.username)                               
                                a_saved = update_or_add_paper_data(edited_a, "a_info", key_cols, user_id=st.session_state.username)
                                
                                if c_saved and a_saved:
                                    st.success("✅ 수정사항이 저장되었습니다.")
                                    st.session_state.admin_paper_editing = False
                                    st.rerun()
                                else:
                                    st.error("저장 중 오류가 발생했습니다.")
                            except Exception as e:
                                st.error(f"저장 실패: {e}")

                    # [취소]
                    with col_cancel:
                        if st.button("❌ 취소", use_container_width=True):
                            st.session_state.admin_paper_editing = False
                            st.rerun()

                    # [삭제]
                    with col_delete:
                        if st.button("🗑️ 삭제 (파일 포함)", type="primary", use_container_width=True):
                            try:
                                conn = sqlite3.connect(DB_FILE)
                                cur = conn.cursor()
                                
                                # 1. DB 삭제
                                cur.execute("DELETE FROM c_info WHERE PDF_FILE_NAME = ?", (pdf_fname,))
                                cur.execute("DELETE FROM a_info WHERE PDF_FILE_NAME = ?", (pdf_fname,))
                                conn.commit()
                                
                                # 2. 파일 삭제
                                delete_paper_files(pdf_fname)
                                # pdf_path = os.path.join(upload_folder, pdf_fname)
                                # if os.path.exists(pdf_path):
                                #     os.remove(pdf_path)
                                
                                # json_fname = f"{os.path.splitext(pdf_fname)[0]}.json"
                                # json_path = os.path.join(upload_folder, json_fname)
                                # if os.path.exists(json_path):
                                #     os.remove(json_path)
                                
                                # if os.path.exists(resolve_folder):
                                #     file_hash = os.path.splitext(pdf_fname)[0]
                                #     for f in os.listdir(resolve_folder):
                                #         if file_hash in f:
                                #             try: os.remove(os.path.join(resolve_folder, f))
                                #             except: pass

                                conn.close()
                                
                                st.success(f"삭제 성공 : {title}")
                                st.session_state.admin_paper_editing = False
                                st.rerun()
                                
                            except Exception as e:
                                st.error(f"삭제 실패 : {title} ({e})")

    with tab_dash:
        show_dashboard(df_view, is_admin=is_admin)

def show_settings_page():
    """설정 페이지를 표시합니다."""
    import textwrap  # 들여쓰기 제거를 위해 필요

    st.subheader("⚙️ 환경 설정")
    
    tabs_list = ["🔐 계정 및 보안"]
    if st.session_state.username == "AD00000":
        tabs_list.append("🎨 화면 설정 (관리자)")
        # [추가] 데이터 관리 탭 추가
        tabs_list.append("🗄️ 데이터 관리 (관리자)")
    
    tabs = st.tabs(tabs_list)

    # [탭 1] 계정 및 보안
    with tabs[0]:
        st.write(f"현재 로그인 사용자: **{st.session_state.username}**")
        st.markdown("#### 비밀번호 변경")
        with st.container(border=True):
            current_pwd = st.text_input("현재 비밀번호", type="password", key="current_pwd")
            new_pwd = st.text_input("새 비밀번호", type="password", key="new_pwd")
            confirm_pwd = st.text_input("새 비밀번호 확인", type="password", key="confirm_pwd")

            if st.button("비밀번호 변경 확인", type="primary"):
                if not verify_user(st.session_state.username, current_pwd):
                    st.error("현재 비밀번호가 올바르지 않습니다.")
                elif new_pwd != confirm_pwd:
                    st.error("새 비밀번호가 일치하지 않습니다.")
                elif not new_pwd:
                    st.error("새 비밀번호는 비워둘 수 없습니다.")
                else:
                    update_password(st.session_state.username, new_pwd)
                    st.success("비밀번호가 성공적으로 변경되었습니다! 다시 로그인해주세요.")
                    st.session_state.logged_in = False
                    st.session_state.page = "login"
                    st.rerun()

    # [탭 2] 화면 설정 (관리자 전용)
    if st.session_state.username == "AD00000" and len(tabs) > 1:
        with tabs[1]:
            st.markdown("#### 전체 디자인 테마 변경")
            st.info("💡 아래에서 테마를 선택하고 '미리보기'를 확인한 후 적용하세요.")
            
            # 현재 테마 DB 확인
            current_theme = st.session_state.get("current_theme", get_system_theme())
            theme_options = list(THEMES.keys())
            
            try:
                default_ix = theme_options.index(current_theme)
            except ValueError:
                default_ix = 0

            # 1. 테마 선택
            selected_theme = st.selectbox(
                "테마 색상 선택", 
                theme_options, 
                index=default_ix,
                key="theme_selector"
            )
            
            preview = THEMES[selected_theme]

            st.markdown("---")
            st.markdown(f"##### 👀 '{selected_theme}' 테마 미리보기")
            
            preview_html = textwrap.dedent(f"""
<div style="background-color: {preview['bg_color']}; padding: 20px; border-radius: 10px; border: 1px solid #ddd; font-family: sans-serif;">
<h4 style="color: {preview['header_color']}; margin-top: 0; margin-bottom: 10px;">헤더 텍스트 예시</h4>
<p style="color: #666; font-size: 0.9em; margin-bottom: 20px;">
    선택된 메뉴는 빨간 테두리로 강조되고, 일반 메뉴는 테마 색상으로 채워집니다.
</p>

<div style="display: flex; gap: 15px; align-items: center;">
<div style="flex: 1; text-align: center;">
<button style="
width: 100%;
background: linear-gradient(135deg, {preview['gradient_start']} 0%, {preview['gradient_end']} 100%);
color: #ffffff;
border: 3px solid #ff4b4b;
padding: 10px 20px;
border-radius: 8px;
font-weight: 700;
font-size: 1rem;
box-shadow: 0 4px 12px rgba(0,0,0,0.2);
cursor: default;">
➤ 선택된 메뉴
</button>
</div>
<div style="flex: 1; text-align: center;">
<button style="
width: 100%;
background-color: {preview['primary']}; 
color: #ffffff; !important
border: 1px solid transparent;
padding: 10px 20px;
border-radius: 8px;
font-weight: 500;
font-size: 1rem;
box-shadow: 0 2px 4px rgba(0,0,0,0.1);
cursor: default;">
일반 메뉴
</button>
</div>
</div>
</div>
            """)
            st.markdown(preview_html, unsafe_allow_html=True)
            
            st.write("")

            if st.button("이 테마로 전체 적용하기", type="secondary"):
                if set_system_theme(selected_theme):
                    st.session_state.current_theme = selected_theme
                    st.success(f"✅ '{selected_theme}' 테마가 전체 시스템에 적용되었습니다.")
                    st.rerun()
                else:
                    st.error("테마 저장 중 오류가 발생했습니다.")

    # [탭 3] 데이터 관리 (관리자 전용)
    if st.session_state.username == "AD00000" and len(tabs) > 2:
        with tabs[2]:
            st.markdown("#### Resolved 폴더 정리")
            st.info("💡 분석 결과(JSON) 폴더에서 동일한 해시를 가진 파일들을 찾아, 타임스탬프 기준 가장 최신 파일만 남기고 이전 중복 파일들을 모두 삭제합니다.")
            
            if st.button("🗑️ Resolved 파일 정리 실행", type="primary"):
                with st.spinner("파일을 정리하는 중입니다..."):
                    deleted = cleanup_resolved_files()
                st.success(f"✅ 정리 완료: 총 {deleted}개의 이전 중복 파일이 삭제되었습니다.")

def show_my_info_page():
    """내정보 수정 페이지를 표시합니다."""
    st.subheader("내정보 수정")

    # 세션 상태 초기화
    if "eng_name_inputs" not in st.session_state:
        st.session_state.eng_name_inputs = ["", "", "", ""]
    if "eng_name_active" not in st.session_state:
        st.session_state.eng_name_active = [True, True, True, True]
    if "excluded_authors" not in st.session_state:
        st.session_state.excluded_authors = []
    if "claim_candidates" not in st.session_state:
        st.session_state.claim_candidates = None
    if "claim_target_info" not in st.session_state:
        st.session_state.claim_target_info = None
        
    # 지정 완료 후 선택 상태를 유지하기 위한 변수
    if "just_claimed_idx" not in st.session_state:
        st.session_state.just_claimed_idx = None

    # ---------------------------------------------------------------------------
    # [1] 논문 실적(a_info) 기반 영어 이름 자동 동기화 로직 (페이지 진입 시 1회만 실행)
    # ---------------------------------------------------------------------------
    # [수정] 이미 동기화가 수행되었는지 확인 (False/None일 때만 실행)
    if not st.session_state.get("hname_auto_synced"):
        try:
            conn = sqlite3.connect(DB_FILE)
            cur = conn.cursor()
            
            # 내 논문(a_info)에서 사용된 저자명(AUTHOR) 추출
            cur.execute("SELECT DISTINCT AUTHOR FROM a_info WHERE 직원번호 = ?", (st.session_state.username,))
            found_authors = [row[0] for row in cur.fetchall() if row[0]]
            
            # 현재 user_info의 hname 정보 조회
            cur.execute("SELECT hname1, hname2, hname3, hname4 FROM user_info WHERE id = ?", (st.session_state.username,))
            current_hnames_row = cur.fetchone()
            
            if current_hnames_row:
                current_hnames = list(current_hnames_row)
                existing_names = set(name for name in current_hnames if name)
                candidates = [name for name in found_authors if name not in existing_names]
                
                is_updated = False
                if candidates:
                    for i in range(4):
                        if not current_hnames[i] and candidates:
                            name_to_add = candidates.pop(0)
                            current_hnames[i] = name_to_add
                            is_updated = True
                    
                    if is_updated:
                        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        cur.execute(
                            "UPDATE user_info SET hname1=?, hname2=?, hname3=?, hname4=?, MOD_DT=?, MOD_ID=? WHERE id=?", 
                            (current_hnames[0], current_hnames[1], current_hnames[2], current_hnames[3], 
                             current_time, st.session_state.username, st.session_state.username)
                        )
                        conn.commit()
        except Exception as e:
            print(f"Auto-update hname error: {e}")
        finally:
            if conn: conn.close()
            # [수정] 실행 완료 플래그 설정 (이 페이지에 머무는 동안 다시 실행 안 함)
            st.session_state.hname_auto_synced = True

    # ---------------------------------------------------------------------------
    # [2] 사용자 정보 조회 및 UI 표시
    # ---------------------------------------------------------------------------
    user_data_tuple = get_user_by_id(st.session_state.username)
    if not user_data_tuple:
        st.error("사용자 정보를 불러올 수 없습니다.")
        return

    user_data_keys = [
        "name", "id", "kri", "email", "hname", "jkind", "jrank", "duty", "dep",
        "state", "password", "hname1", "hname2", "hname3", "hname4",
    ]
    user_data = dict(zip(user_data_keys, user_data_tuple))

    # [내 정보 수정 폼]
    with st.form(key="my_info_form"):
        st.text_input("ID", value=user_data["id"], disabled=True)
        name = st.text_input("이름", value=user_data["name"])
        kri = st.text_input("KRI", value=user_data["kri"])
        email = st.text_input("Email", value=user_data["email"])

        col1, col2, _ = st.columns([0.2, 0.2, 0.6])
        if col1.form_submit_button("변경완료"):
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            try:
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                c.execute(
                    "UPDATE user_info SET name = ?, kri = ?, email = ?, MOD_DT = ?, MOD_ID = ? WHERE id = ?", 
                    (name, kri, email, current_time, st.session_state.username, st.session_state.username)
                )
                conn.commit()
                st.success("정보가 업데이트되었습니다.")
            except Exception as e:
                conn.rollback()
                st.error(f"오류 발생: {e}")
            finally:
                conn.close()
        if col2.form_submit_button("취소"):
            st.session_state.page = "upload"
            st.rerun()

    st.markdown("---")

    # [3] 영어 이름 관리
    col_load, col_save = st.columns([0.5, 0.5])
    
    # DB에 hname1이 없으면 [변환] 버튼 모드
    if not user_data.get("hname1"):
        st.subheader("영어이름으로 변환")
        with col_load:
            if st.button("변환", key="convert_name_btn"):
                korean_name = user_data.get("name", "")
                if korean_name:
                    variations = korean_name_to_english(korean_name)
                    variations.extend([""] * 4)
                    st.session_state.eng_name_inputs = variations[:4]
                    st.session_state.eng_name_active = [True, True, True, True]
                else:
                    st.warning("이름이 없습니다.")
                st.rerun()
    
    # DB에 hname1이 있으면 [자동 불러오기] 모드
    else:
        st.subheader("영어이름 관리")
        
        # UI 자동 채우기: 입력창이 비어있으면 DB 값으로 채움
        is_inputs_empty = all(x == "" for x in st.session_state.eng_name_inputs)
        if is_inputs_empty:
            st.session_state.eng_name_inputs = [user_data.get(f"hname{i}", "") or "" for i in range(1, 5)]
            st.session_state.eng_name_active = [True] * 4
            st.rerun()

        with col_load:
            if st.button("DB 값 다시 불러오기", key="load_name_btn"):
                st.session_state.eng_name_inputs = [user_data.get(f"hname{i}", "") for i in range(1, 5)]
                st.session_state.eng_name_active = [True] * 4
                st.rerun()
    # [추가] 삭제 버튼 클릭 시 실행될 콜백 함수 정의
    def delete_eng_name_callback(idx):
        # 1. 데이터 리스트 초기화
        st.session_state.eng_name_inputs[idx] = ""
        # 2. 위젯의 상태 키 값 초기화 (화면 갱신 전 수행됨)
        st.session_state[f"eng_var_{idx}"] = ""
    # 입력 필드 표시
    for i in range(4):
        col1, col2 = st.columns([4, 1])
        with col1:
            disabled = not st.session_state.eng_name_active[i]
            val = st.session_state.eng_name_inputs[i] if st.session_state.eng_name_inputs[i] else ""
            # st.session_state.eng_name_inputs[i] = st.text_input(f"영어이름 후보 {i+1}", value=val, key=f"eng_var_{i}", disabled=disabled)
            # [수정] 입력된 값을 변수에 받고, 리스트에 업데이트합니다.
            new_val = st.text_input(f"영어이름 후보 {i+1}", value=val, key=f"eng_var_{i}", disabled=disabled)
            st.session_state.eng_name_inputs[i] = new_val            
        with col2:
            st.write(""); st.write("")
            # if st.button("삭제", key=f"del_btn_{i}", disabled=disabled):
            # [수정] on_click 파라미터를 사용하여 삭제 로직을 콜백으로 처리
            st.button(
                "삭제", 
                key=f"del_btn_{i}", 
                disabled=disabled, 
                on_click=delete_eng_name_callback, 
                args=(i,)
            )             
    
    # 저장 버튼
    with col_save:
        if st.button("내 영어 이름 저장", key="save_eng_names"):
            names = [st.session_state.eng_name_inputs[i].strip() for i in range(4) if st.session_state.eng_name_active[i] and st.session_state.eng_name_inputs[i]]
            names.extend([None]*4)
            try:
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                conn = sqlite3.connect(DB_FILE)
                conn.execute(
                    "UPDATE user_info SET hname1=?, hname2=?, hname3=?, hname4=?, MOD_DT=?, MOD_ID=? WHERE id=?", 
                    (*names[:4], current_time, st.session_state.username, st.session_state.username)
                )
                conn.commit()
                st.success("저장되었습니다.")
            except Exception as e:
                st.error(f"저장 실패: {e}")
            finally:
                conn.close()

    st.markdown("---")
    st.subheader("저자정보에서 확인")

    # [검색 로직] (기존 유지)
    if st.button("검색", key="search_author_name"):
        st.session_state.excluded_authors = []
        
        search_names = [st.session_state.eng_name_inputs[i].strip() for i in range(4) if st.session_state.eng_name_active[i] and st.session_state.eng_name_inputs[i]]
        korean_name_query = user_data.get("name", "")

        if search_names or korean_name_query:
            with st.spinner("검색 중..."):
                results_df = search_author_by_name(search_names, korean_name=korean_name_query)
                
                if not results_df.empty:
                    # 데이터 전처리
                    results_df.insert(0, '연번', range(1, len(results_df) + 1))
                    
                    auth_res = results_df['AUTHOR'].drop_duplicates().sort_values().to_frame(name='AUTHOR')
                    auth_res.insert(0, '연번', range(1, len(auth_res) + 1))
                    
                    aff_res = results_df['AFFILIATION'].drop_duplicates().sort_values().to_frame(name='AFFILIATION')
                    aff_res.insert(0, '연번', range(1, len(aff_res) + 1))
                    
                    disp_df = results_df.copy()
                    disp_df['AUTHOR'] = disp_df['AUTHOR'].map(dict(zip(auth_res['AUTHOR'], auth_res['연번'])))
                    disp_df['AFFILIATION'] = disp_df['AFFILIATION'].map(dict(zip(aff_res['AFFILIATION'], aff_res['연번'])))

                    st.session_state.author_search_results = results_df
                    st.session_state.author_search_display = disp_df
                    st.session_state.author_results = auth_res
                    st.session_state.author_affiliation_results = aff_res
                    
                    st.session_state.claim_candidates = None
                    st.session_state.claim_target_info = None
                    st.session_state.just_claimed_idx = None # 검색 시 초기화
                else:
                    st.session_state.author_search_results = pd.DataFrame()
                    st.session_state.author_search_display = pd.DataFrame()
        else:
            st.warning("검색을 위한 영어 이름이나 한글 이름이 없습니다.")
            st.session_state.author_search_results = pd.DataFrame()
        st.session_state.search_clicked = True

    # [결과 표시] (기존 유지)
    if "author_search_results" in st.session_state:
        df_display = st.session_state.get("author_search_display", pd.DataFrame())
        df_auth = st.session_state.get("author_results", pd.DataFrame())
        df_aff = st.session_state.get("author_affiliation_results", pd.DataFrame())

        if not df_display.empty:
            st.write(f"검색 결과: 총 {len(df_display)}건.")
            
            # 메인 리스트
            event = st.dataframe(
                df_display,
                use_container_width=False,
                hide_index=True,
                selection_mode="single-row",
                on_select="rerun",
                key="author_search_table",
                column_config={"연번": st.column_config.NumberColumn(width=40)}
            )
            
            # AUTHOR 요약
            st.write(f"AUTHOR 검색 결과: 총 {len(df_auth)}건")
            event_auth = st.dataframe(
                df_auth,
                use_container_width=False,
                hide_index=True,
                selection_mode="single-row",
                on_select="rerun",
                key="author_summary_table",
                column_config={
                    "연번": st.column_config.NumberColumn(width=40),
                    "AUTHOR": st.column_config.TextColumn(width=400)
                }
            )

            # AUTHOR 선택 시 내 영어이름 저장 로직
            if event_auth.selection["rows"]:
                idx_auth = event_auth.selection["rows"][0]
                selected_author_name = df_auth.iloc[idx_auth]["AUTHOR"]
                
                col_info, col_save_btn, col_exclude_btn = st.columns([0.3, 0.4, 0.4])
                with col_info:
                    st.info(f"선택된 이름:\n**{selected_author_name}**")
                with col_save_btn:
                    if st.button("내 영어이름으로 저장", key="add_my_eng_name_btn", use_container_width=True):
                        latest_user_data = get_user_by_id(st.session_state.username)
                        current_hnames = [latest_user_data[10], latest_user_data[11], latest_user_data[12], latest_user_data[13]]
                        if selected_author_name in current_hnames:
                            st.warning("이미 등록됨")
                        else:
                            updated_hnames = list(current_hnames)
                            updated = False
                            for i in range(4):
                                if not updated_hnames[i]:
                                    updated_hnames[i] = selected_author_name
                                    updated = True
                                    break
                            if updated:
                                try:
                                    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    conn = sqlite3.connect(DB_FILE)
                                    conn.execute(
                                        "UPDATE user_info SET hname1=?, hname2=?, hname3=?, hname4=?, MOD_DT=?, MOD_ID=? WHERE id=?", 
                                        (*updated_hnames, current_time, st.session_state.username, st.session_state.username)
                                    )
                                    conn.commit()
                                    conn.close()
                                    st.session_state.eng_name_inputs = [name if name else "" for name in updated_hnames]
                                    st.success(f"추가되었습니다.")
                                    st.rerun()
                                except Exception as e: st.error(f"실패: {e}")
                            else: st.error("슬롯(4개) 가득 참")
                with col_exclude_btn:
                    if st.button("검색에서 제외", key="exclude_auth_btn", use_container_width=True):
                        st.session_state.excluded_authors.append(selected_author_name)
                        current_df = st.session_state.author_search_results
                        filtered_df = current_df[current_df['AUTHOR'] != selected_author_name]
                        if filtered_df.empty:
                            st.session_state.author_search_results = pd.DataFrame()
                            st.session_state.author_search_display = pd.DataFrame()
                            st.warning("제외 후 남은 결과가 없습니다.")
                        else:
                            filtered_df = filtered_df.copy()
                            if '연번' in filtered_df.columns: filtered_df['연번'] = range(1, len(filtered_df) + 1)
                            auth_res_new = filtered_df['AUTHOR'].drop_duplicates().sort_values().to_frame(name='AUTHOR')
                            auth_res_new.insert(0, '연번', range(1, len(auth_res_new) + 1))
                            aff_res_new = filtered_df['AFFILIATION'].drop_duplicates().sort_values().to_frame(name='AFFILIATION')
                            aff_res_new.insert(0, '연번', range(1, len(aff_res_new) + 1))
                            disp_df_new = filtered_df.copy()
                            disp_df_new['AUTHOR'] = disp_df_new['AUTHOR'].map(dict(zip(auth_res_new['AUTHOR'], auth_res_new['연번'])))
                            disp_df_new['AFFILIATION'] = disp_df_new['AFFILIATION'].map(dict(zip(aff_res_new['AFFILIATION'], aff_res_new['연번'])))
                            st.session_state.author_search_results = filtered_df
                            st.session_state.author_search_display = disp_df_new
                            st.session_state.author_results = auth_res_new
                            st.session_state.author_affiliation_results = aff_res_new
                            st.success(f"'{selected_author_name}'을(를) 결과에서 제외했습니다.")
                            st.rerun()

            st.write(f"AFFILIATION 검색 결과: 총 {len(df_aff)}건")
            st.dataframe(
                df_aff,
                use_container_width=False,
                hide_index=True,
                column_config={
                    "연번": st.column_config.NumberColumn(width=40),
                    "AFFILIATION": st.column_config.TextColumn(width=1200)
                }
            )

            # [메인 리스트 선택 및 상세 기능]
            selected_rows = event.selection["rows"]
            
            # 지정 완료 직후 Rerun 시에는 선택이 풀리므로, 강제로 선택 상태 복구
            if not selected_rows and st.session_state.just_claimed_idx is not None:
                selected_rows = [st.session_state.just_claimed_idx]

            if selected_rows:
                idx = selected_rows[0]
                row = st.session_state.author_search_results.iloc[idx]
                
                st.markdown("##### 선택된 논문 작업")
                col1, col2 = st.columns([0.5, 0.5])
                
                pdf_fname = row.get("PDF_FILE_NAME")
                author_in_row = row.get("AUTHOR")
                name_in_row = row.get("이름")
                affiliation_in_row = row.get("AFFILIATION")
                current_emp_id = row.get("직원번호")

                with col1:
                    display_pdf_viewer_button(pdf_fname)

                with col2:
                    if st.session_state.just_claimed_idx == idx:
                        st.success("✅ 내 논문으로 지정되었습니다! (DB 반영 완료)")
                        if st.button("확인 (목록 갱신)", key="confirm_refresh_btn"):
                            st.session_state.just_claimed_idx = None
                            st.rerun()
                    else:
                        is_claimed = False
                        if current_emp_id is not None:
                            s_id = str(current_emp_id).strip().lower()
                            if s_id not in ['none', 'nan', '', 'nat']:
                                is_claimed = True

                        if not is_claimed:
                            if st.button("내 논문으로 지정 (직원번호 연동) 🙋‍♂️", key="claim_btn"):
                                search_target_name = user_data["name"] 
                                matches = search_users_by_name(search_target_name, None)
                                
                                def update_session_state(idx, user_id, user_name):
                                    st.session_state.author_search_results.at[idx, '직원번호'] = user_id
                                    st.session_state.author_search_results.at[idx, '이름'] = user_name
                                    if "author_search_display" in st.session_state and '직원번호' in st.session_state.author_search_display.columns:
                                        st.session_state.author_search_display.at[idx, '직원번호'] = user_id
                                        st.session_state.author_search_display.at[idx, '이름'] = user_name

                                if not matches:
                                    success, msg = claim_my_paper(
                                        pdf_fname, author_in_row, affiliation_in_row, 
                                        st.session_state.username, user_data["name"]
                                    )
                                    if success:
                                        update_session_state(idx, st.session_state.username, user_data["name"])
                                        st.session_state.just_claimed_idx = idx
                                        st.rerun()
                                    else:
                                        st.session_state.claim_msg = ("error", msg)
                                        st.rerun()
                                
                                elif len(matches) == 1:
                                    target_user = matches[0]
                                    success, msg = claim_my_paper(
                                        pdf_fname, author_in_row, affiliation_in_row, 
                                        target_user['id'], target_user['name']
                                    )
                                    if success:
                                        update_session_state(idx, target_user['id'], target_user['name'])
                                        st.session_state.just_claimed_idx = idx
                                        st.rerun()
                                    else:
                                        st.session_state.claim_msg = ("error", msg)
                                        st.rerun()
                                
                                else:
                                    st.session_state.claim_candidates = matches
                                    st.session_state.claim_target_info = {
                                        "pdf": pdf_fname,
                                        "auth": author_in_row,
                                        "aff": affiliation_in_row,
                                        "idx": idx 
                                    }
                                    st.rerun()
                        else:
                            st.info(f"이미 지정됨 (직원번호: {current_emp_id})")

            if st.session_state.get("claim_candidates"):
                st.markdown("---")
                st.warning(f"⚠️ 동명이인이 {len(st.session_state.claim_candidates)}명 발견되었습니다. 올바른 직원을 선택하세요.")
                
                options = {f"{u['name']} (ID: {u['id']}, 부서: {u['dep']})": u for u in st.session_state.claim_candidates}
                selected_label = st.radio("직원 선택", list(options.keys()))
                
                col_sel_ok, col_sel_cancel = st.columns([0.5, 0.5])
                
                with col_sel_ok:
                    if st.button("확인 (선택한 직원으로 지정)", key="confirm_claim"):
                        selected_user = options[selected_label]
                        info = st.session_state.claim_target_info
                        
                        success, msg = claim_my_paper(
                            info["pdf"], info["auth"], info["aff"], 
                            selected_user['id'], selected_user['name']
                        )
                        if success:
                            t_idx = info.get("idx")
                            if t_idx is not None:
                                st.session_state.author_search_results.at[t_idx, '직원번호'] = selected_user['id']
                                st.session_state.author_search_results.at[t_idx, '이름'] = selected_user['name']
                                if "author_search_display" in st.session_state and '직원번호' in st.session_state.author_search_display.columns:
                                    st.session_state.author_search_display.at[t_idx, '직원번호'] = selected_user['id']
                                
                                st.session_state.just_claimed_idx = t_idx 
                            
                            st.session_state.claim_candidates = None
                            st.session_state.claim_target_info = None
                            st.rerun()
                        else:
                            st.error(msg)
                            
                with col_sel_cancel:
                    if st.button("취소", key="cancel_claim"):
                        st.session_state.claim_candidates = None
                        st.session_state.claim_target_info = None
                        st.rerun()

            else:
                if not event.selection["rows"]:
                    st.info("👆 리스트에서 행을 클릭하세요.")
                
        elif st.session_state.get("search_clicked"):
            st.info("검색 결과가 없습니다.")


# [누락된 함수 복구] 접수처리 페이지 함수
def show_receipt_processing_page():
    st.subheader("접수 처리 (관리자)")

    # 세션 상태 초기화
    if "receipt_analysis_done" not in st.session_state:
        st.session_state.receipt_analysis_done = False
    if "receipt_target_pdf" not in st.session_state:
        st.session_state.receipt_target_pdf = None
    if "receipt_editing" not in st.session_state:
        st.session_state.receipt_editing = False
    # [추가] 다중 처리 모드 세션 상태
    if "receipt_multi_mode" not in st.session_state:
        st.session_state.receipt_multi_mode = False

    # [추가] 분석 로직을 처리하는 내부 헬퍼 함수
    def _trigger_analysis(row_dict):
        target_pdf_name = row_dict["PDF_FILE_NAME"]
        target_ori_name = row_dict["ORI_FILE_NAME"]
        target_author_name = row_dict["AUTHOR"]
        target_id = row_dict.get("ID", "")

        # [추가] OLD_FILE_NAME 추출
        target_old_file_name = row_dict.get("OLD_FILE_NAME", "") 

        file_path = os.path.join(upload_folder, target_pdf_name)
        if not os.path.exists(file_path):
            st.error(f"파일을 찾을 수 없습니다: {target_pdf_name}")
            return False

        with st.spinner(f"'{target_ori_name}' 분석 중..."):
            json_data, error = get_pdf_json(file_path, PDF_SERVICE_URL, REQUEST_TIMEOUT)
            if not json_data:
                st.error(f"분석 실패: {error}")
                return False

            json_filename = f"{os.path.splitext(target_pdf_name)[0]}.json"
            json_path = os.path.join(upload_folder, json_filename)
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)
            
            json_data, a_info, c_info, fail_count, model_name = get_paper_df(json_path)
            if c_info is None:
                st.error(f"서지정보 추출 실패. {fail_count}")
                return False

            output_path = save_output_file(json_data, json_filename, model_name, resolve_folder)
            llm_json_name = os.path.basename(output_path[0])

            if 'receipt_chosen_user' in st.session_state:
                del st.session_state['receipt_chosen_user']
            
            new_rows = pd.DataFrame([
                {"Key": "ORI_FILE_NAME", "Value": target_ori_name},
                {"Key": "PDF_FILE_NAME", "Value": target_pdf_name},
                {"Key": "JSON_FILE_NAME", "Value": json_filename},
                {"Key": "LLM_JSON_FILE_NAME", "Value": llm_json_name},
            ])
            c_info = pd.concat([c_info.drop(15, errors="ignore"), new_rows], ignore_index=True)
            
            a_info["ORI_FILE_NAME"] = target_ori_name
            a_info["PDF_FILE_NAME"] = target_pdf_name
            a_info["JSON_FILE_NAME"] = json_filename
            a_info["LLM_JSON_FILE_NAME"] = llm_json_name
            if '이름' not in a_info.columns: a_info['이름'] = None
            a_info = a_info[['AUTHOR', 'AFFILIATION', 'ROLE', '이름', 'ORI_FILE_NAME','PDF_FILE_NAME', 'JSON_FILE_NAME','LLM_JSON_FILE_NAME']]
            
            st.session_state.receipt_c_info = c_info
            st.session_state.receipt_a_info = a_info
            st.session_state.receipt_c_info_original = c_info.copy()
            st.session_state.receipt_a_info_original = a_info.copy()
            st.session_state.receipt_target_pdf = target_pdf_name
            st.session_state.receipt_target_old_pdf = target_old_file_name # [추가] 세션에 저장
            st.session_state.receipt_target_author = target_author_name
            st.session_state.receipt_target_id = target_id
            st.session_state.receipt_analysis_done = True
            st.session_state.receipt_editing = False
            return True

    # 1. 상단 필터
    is_multi_mode = st.session_state.get("receipt_multi_mode", False)
    filter_option = st.radio(
        "처리 상태 선택", 
        ("처리전", "처리완료", "전체"), 
        index=0, 
        horizontal=True,
        disabled=is_multi_mode
    )

    # 2. 데이터 가져오기
    conn = sqlite3.connect(DB_FILE)
    query_base = "SELECT * FROM u_info"
    
    if filter_option == "처리전":
        query = query_base + " WHERE DONE = 0 OR DONE = '0' ORDER BY SAVE_DATE ASC"
    elif filter_option == "처리완료":
        query = query_base + " WHERE DONE >= 1 OR DONE = '1' OR DONE = '2' ORDER BY SAVE_DATE ASC"
    else:
        query = query_base + " ORDER BY SAVE_DATE ASC"
    
    try:
        df = pd.read_sql_query(query, conn)
        # DONE 컬럼 타입 강제 변환 (에러 방지)
        if 'DONE' in df.columns:
            df['DONE'] = pd.to_numeric(df['DONE'], errors='coerce').fillna(0).astype(int)        
    except Exception as e:
        st.error(f"데이터 조회 실패: {e}")
        conn.close()
        return
    finally:
        conn.close()

    # 3. 테이블 표시 (멀티 선택)
    st.write(f"총 {len(df)}건")
    
    # 컬럼 순서 재배치 (가독성)
    desired_order = ['ORI_FILE_NAME', 'AUTHOR', 'ID', 'ROLE', 'EMAIL', 'PDF_FILE_NAME', 'OLD_FILE_NAME', 'SAVE_DATE', 'DONE']
    available_cols = [c for c in desired_order if c in df.columns]
    remaining_cols = [c for c in df.columns if c not in available_cols]
    df_display = df[available_cols + remaining_cols]

    event = st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        selection_mode="multi-row" if not is_multi_mode else "single-row", # 다중 모드 중에는 선택 비활성화
        on_select="rerun",
        key="receipt_table"
    )

    selected_indices = event.selection.get("rows", [])
    
    # [추가] 다중 처리 모드 진행 블록
    if is_multi_mode:
        idx = st.session_state.receipt_multi_current_index
        total = st.session_state.receipt_multi_total_count

        # 모든 항목 처리 완료 시
        if idx >= total:
            st.success("✅ 다중 항목 분석이 모두 완료되었습니다.")
            # 다중 모드 상태 초기화
            st.session_state.receipt_multi_mode = False
            del st.session_state.receipt_multi_queue
            del st.session_state.receipt_multi_current_index
            del st.session_state.receipt_multi_total_count
            # 분석 상태 초기화
            if "receipt_analysis_done" in st.session_state: del st.session_state.receipt_analysis_done
            if "receipt_target_pdf" in st.session_state: del st.session_state.receipt_target_pdf
            if "receipt_target_old_pdf" in st.session_state: del st.session_state.receipt_target_old_pdf # [추가]
            st.rerun()

        # 진행 상태 표시 및 중단 버튼
        st.markdown("---")
        st.info(f"🚀 **다중 항목 분석**: [{idx + 1}/{total} 진행중]")
        if st.button("⏹️ 다중 항목 분석 중단"):
            st.warning("분석을 중단합니다. 지금까지 저장된 내용은 유지됩니다.")
            # 다중 모드 상태 초기화
            st.session_state.receipt_multi_mode = False
            del st.session_state.receipt_multi_queue
            del st.session_state.receipt_multi_current_index
            del st.session_state.receipt_multi_total_count
            # 분석 상태 초기화
            if "receipt_analysis_done" in st.session_state: del st.session_state.receipt_analysis_done
            if "receipt_target_pdf" in st.session_state: del st.session_state.receipt_target_pdf
            if "receipt_target_old_pdf" in st.session_state: del st.session_state.receipt_target_old_pdf # [추가]
            st.rerun()

        current_pdf_name = st.session_state.receipt_multi_queue[idx]
        
        # 현재 아이템에 대한 분석이 아직 로드되지 않았다면 분석 실행
        if st.session_state.get("receipt_target_pdf") != current_pdf_name:
            row = df[df['PDF_FILE_NAME'] == current_pdf_name].iloc[0]
            if _trigger_analysis(row.to_dict()):
                st.rerun()
            else: # 분석 실패 시 다음으로
                st.session_state.receipt_multi_current_index += 1
                st.rerun()

    # 4. 하단 액션 버튼 (다중 모드가 아닐 때)
    if selected_indices:
        selected_rows = df.iloc[selected_indices]
        st.info(f"선택된 항목: {len(selected_rows)}건")
        
        col_btn1, col_btn2 = st.columns([0.7, 0.3])

        # [버튼 1] 메일로 처리결과 전송
        with col_btn1:
            if filter_option == "처리완료" or filter_option == "전체":
                if st.button("📧 메일로 처리결과 전송"):
                    targets = selected_rows[selected_rows['DONE'] >= 1]
                    
                    if targets.empty:
                        st.warning("선택된 항목 중 '처리완료'된 건이 없습니다.")
                    else:
                        if 'EMAIL' in targets.columns:
                            valid_targets = targets[targets['EMAIL'].notna() & (targets['EMAIL'] != "")]
                            
                            if valid_targets.empty:
                                st.warning("선택된 항목에 유효한 이메일 주소가 없습니다.")
                            else:
                                try:
                                    pdf_list = valid_targets['PDF_FILE_NAME'].tolist()
                                    if pdf_list:
                                        conn = sqlite3.connect(DB_FILE)
                                        placeholders = ','.join(['?'] * len(pdf_list))
                                        title_query = f"SELECT PDF_FILE_NAME, TITLE FROM c_info WHERE PDF_FILE_NAME IN ({placeholders})"
                                        title_df = pd.read_sql_query(title_query, conn, params=tuple(pdf_list))
                                        conn.close()
                                        title_map = dict(zip(title_df['PDF_FILE_NAME'], title_df['TITLE']))
                                    else:
                                        title_map = {}
                                except Exception as e:
                                    st.error(f"논문 제목 조회 중 오류: {e}")
                                    title_map = {}

                                email_groups = {}
                                for _, row in valid_targets.iterrows():
                                    email = row['EMAIL']
                                    author = row['AUTHOR']
                                    ori_filename = row['ORI_FILE_NAME']
                                    pdf_filename = row['PDF_FILE_NAME']
                                    paper_title = title_map.get(pdf_filename, "")
                                    
                                    if email not in email_groups:
                                        email_groups[email] = []
                                    
                                    email_groups[email].append({
                                        'author': author,
                                        'title': paper_title,
                                        'ori_filename': ori_filename,
                                        'pdf_filename': pdf_filename
                                    })
                                
                                success_count = 0
                                fail_log = []
                                conn = sqlite3.connect(DB_FILE)
                                cur = conn.cursor()
                                
                                try:
                                    with st.spinner(f"{len(email_groups)}명에게 메일 전송 중..."):
                                        for email, details_list in email_groups.items():
                                            is_sent, msg = send_processing_result_email(email, details_list)
                                            
                                            if is_sent:
                                                success_count += 1
                                                for item in details_list:
                                                    cur.execute(
                                                        "UPDATE u_info SET DONE = 2 WHERE PDF_FILE_NAME = ?", 
                                                        (item['pdf_filename'],)
                                                    )
                                            else:
                                                fail_log.append(f"{email}: {msg}")
                                    
                                    conn.commit()
                                    
                                    if success_count > 0:
                                        st.success(f"{success_count}명에게 메일 발송 및 상태 업데이트 완료!")
                                        if fail_log:
                                            st.error(f"일부 발송 실패:\n" + "\n".join(fail_log))
                                        st.rerun()
                                    elif fail_log:
                                        st.error(f"발송 실패:\n" + "\n".join(fail_log))

                                except Exception as e:
                                    st.error(f"작업 중 오류 발생: {e}")
                                finally:
                                    conn.close()
                        else:
                            st.error("데이터에 이메일 정보가 없습니다.")

        # [버튼 2] 삭제
        with col_btn2:
            if st.button("🗑️ 선택된 항목 삭제", type="primary"):
                conn = sqlite3.connect(DB_FILE)
                cur = conn.cursor()
                deleted_count = 0
                
                try:
                    progress_bar = st.progress(0)
                    total = len(selected_rows)
                    
                    for i, (_, row) in enumerate(selected_rows.iterrows()):
                        target_pdf_name = row["PDF_FILE_NAME"]
                        cur.execute("DELETE FROM u_info WHERE PDF_FILE_NAME = ?", (target_pdf_name,))

                        # 2. 파일 삭제
                        delete_paper_files(target_pdf_name)                        
                        # file_hash = os.path.splitext(target_pdf_name)[0]
                        # if os.path.exists(upload_folder):
                        #     for filename in os.listdir(upload_folder):
                        #         if file_hash in filename:
                        #             try: os.remove(os.path.join(upload_folder, filename))
                        #             except: pass
                        
                        deleted_count += 1
                        progress_bar.progress((i + 1) / total)

                    conn.commit()
                    st.success(f"{deleted_count}건 삭제되었습니다.")
                    st.session_state.receipt_analysis_done = False
                    st.session_state.receipt_target_pdf = None
                    st.session_state.receipt_target_old_pdf = None # [추가]
                    st.session_state.receipt_editing = False
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"삭제 중 오류 발생: {e}")
                finally:
                    conn.close()

    # 5. 다중/단일 분석 시작 버튼 (다중 모드가 아닐 때만 표시)
    if selected_indices and not is_multi_mode:
        if len(selected_indices) > 1:
            if st.button("🚀 다중 항목 분석 시작"):
                selected_rows = df.iloc[selected_indices]
                st.session_state.receipt_multi_mode = True
                st.session_state.receipt_multi_queue = selected_rows['PDF_FILE_NAME'].tolist()
                st.session_state.receipt_multi_current_index = 0
                st.session_state.receipt_multi_total_count = len(selected_rows)
                # 이전 분석 상태 초기화
                if "receipt_analysis_done" in st.session_state: del st.session_state.receipt_analysis_done
                if "receipt_target_pdf" in st.session_state: del st.session_state.receipt_target_pdf
                if "receipt_target_old_pdf" in st.session_state: del st.session_state.receipt_target_old_pdf # [추가]
                st.rerun()
        elif len(selected_indices) == 1:
            row = df.iloc[selected_indices[0]]
            st.markdown("---")
            st.markdown(f"##### 🔍 단일 항목 분석: {row['ORI_FILE_NAME']}")
            if st.button("서지정보 분석 (단일 항목)"):
                if _trigger_analysis(row.to_dict()):
                    st.rerun()

    # 6. 분석 결과 표시 및 처리 (공통 UI)
    if st.session_state.get("receipt_analysis_done") and st.session_state.get("receipt_target_pdf"):
        st.markdown("---")
        st.subheader("📊 서지정보 분석 결과")
        
        if st.session_state.receipt_editing:
            edited_c = st.data_editor(st.session_state.receipt_c_info, key="receipt_c_editor", num_rows="dynamic")
            edited_a = st.data_editor(st.session_state.receipt_a_info, key="receipt_a_editor", num_rows="dynamic")
            
            target_author_name = st.session_state.get("receipt_target_author", "")
            target_id_from_upload = st.session_state.get("receipt_target_id", "")
            
            extracted_authors = []
            if 'AUTHOR' in edited_a.columns:
                extracted_authors = edited_a['AUTHOR'].unique().tolist()
            
            # 제출자 선택을 위한 세션 변수 초기화
            if 'receipt_chosen_user' not in st.session_state:
                st.session_state.receipt_chosen_user = None

            chosen_user = st.session_state.receipt_chosen_user

            # 아직 제출자가 확정되지 않은 경우, 매칭 로직 수행
            if not chosen_user:
                # 1. 업로드 시 ID가 제공되었는지 확인
                if target_id_from_upload and target_id_from_upload.strip():
                    user_by_id = get_user_by_id(target_id_from_upload)
                    # ID로 사용자를 찾았고, 이름이 제출자명과 일치하는 경우
                    if user_by_id and user_by_id[0] == target_author_name:
                        # search_users_by_name과 동일한 형식의 dict로 변환
                        chosen_user = {
                            'name': user_by_id[0], 'id': user_by_id[1], 'dep': user_by_id[8],
                            'hname1': user_by_id[11], 'hname2': user_by_id[12],
                            'hname3': user_by_id[13], 'hname4': user_by_id[14],
                        }
                        st.session_state.receipt_chosen_user = chosen_user

                # 2. ID로 찾지 못한 경우, 이름으로 검색
                if not chosen_user:
                    matches = search_users_by_name(target_author_name)
                    if len(matches) == 1:
                        chosen_user = matches[0]
                        st.session_state.receipt_chosen_user = chosen_user
                    elif len(matches) > 1:
                        # 3. 동명이인 중 영어 이름으로 자동 선택 시도
                        found_match = False
                        for user in matches:
                            eng_names = [user.get(f'hname{i}') for i in range(1, 5) if user.get(f'hname{i}')]
                            for eng in eng_names:
                                if eng in extracted_authors:
                                    chosen_user = user
                                    st.session_state.receipt_chosen_user = user
                                    found_match = True
                                    break
                            if found_match: break
                        
                        # 4. 자동 선택 실패 시, 관리자에게 선택 요청
                        if not found_match:
                            st.warning(f"⚠️ 제출자 '{target_author_name}'에 해당하는 직원이 여러 명 검색되었습니다. 아래에서 올바른 제출자를 선택해주세요.")
                            options = {f"{u['name']} (ID: {u['id']}, 부서: {u['dep']})": u for u in matches}
                            selected_label = st.radio("제출자 선택", list(options.keys()), key="receipt_submitter_select")
                            if st.button("이 직원으로 선택", key="confirm_receipt_submitter"):
                                st.session_state.receipt_chosen_user = options[selected_label]
                                st.rerun()
                            st.stop()

            # 제출자가 확정된 후 UI 표시
            submitter_display = f"{target_author_name}"
            matched_eng_name = None
            if chosen_user:
                submitter_display = f"{chosen_user['name']} (ID: {chosen_user['id']}, {chosen_user['dep']})"
                eng_names = [chosen_user.get(f'hname{i}') for i in range(1, 5) if chosen_user.get(f'hname{i}')]
                for eng in eng_names:
                    if eng in extracted_authors:
                        matched_eng_name = eng
                        break

            options_list = ["선택안함"] + sorted(extracted_authors)
            default_index = options_list.index(matched_eng_name) if matched_eng_name and matched_eng_name in options_list else 0
            
            selected_author = st.selectbox(
                f"저자 선택 (제출자: {submitter_display})", 
                options=options_list,
                index=default_index
            )
            st.write("") 

            col_save, col_cancel = st.columns([0.5, 0.5])
            
            with col_save:
                if st.button("저장 (DB반영 및 완료처리)", type="primary"):
                    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    # -------------------------------------------------------------
                    # [추가] OLD_FILE_NAME 값이 있으면, 기존 DB 데이터 및 물리적 파일 삭제
                    # -------------------------------------------------------------
                    old_pdf_filename = st.session_state.get("receipt_target_old_pdf")
                    if old_pdf_filename and str(old_pdf_filename).strip() not in ["", "None", "nan"]:
                        try:
                            conn_del = sqlite3.connect(DB_FILE)
                            cur_del = conn_del.cursor()
                            
                            # 1. DB에서 기존 논문 정보(c_info, a_info) 삭제
                            cur_del.execute("DELETE FROM c_info WHERE PDF_FILE_NAME = ?", (old_pdf_filename,))
                            cur_del.execute("DELETE FROM a_info WHERE PDF_FILE_NAME = ?", (old_pdf_filename,))
                            conn_del.commit()
                            conn_del.close()
                            
                            # 2. 기존 물리적 파일 (pdf, json) 삭제
                            delete_paper_files(old_pdf_filename)
                            # old_pdf_path = os.path.join(upload_folder, old_pdf_filename)
                            # if os.path.exists(old_pdf_path):
                            #     os.remove(old_pdf_path)
                                
                            # old_json_fname = f"{os.path.splitext(old_pdf_filename)[0]}.json"
                            # old_json_path = os.path.join(upload_folder, old_json_fname)
                            # if os.path.exists(old_json_path):
                            #     os.remove(old_json_path)

                            # if os.path.exists(resolve_folder):
                            #     file_hash = os.path.splitext(old_pdf_filename)[0]
                            #     for f in os.listdir(resolve_folder):
                            #         if file_hash in f:
                            #             try: os.remove(os.path.join(resolve_folder, f))
                            #             except: pass                                             
                        except Exception as e:
                            print(f"기존 데이터 삭제 오류: {e}")
                    # -------------------------------------------------------------                    
                    df_c_transposed = edited_c.set_index("Key").T.reset_index(drop=True)
                    df_c_transposed["SAVE_DATE"] = current_time
                    
                    df_a_to_save = edited_a.copy()
                    df_a_to_save["SAVE_DATE"] = current_time
                    
                    if '이름' not in df_a_to_save.columns: df_a_to_save['이름'] = None
                    if '직원번호' not in df_a_to_save.columns: df_a_to_save['직원번호'] = None
                    
                    df_a_to_save['이름'] = df_a_to_save['이름'].astype(object)
                    df_a_to_save['직원번호'] = df_a_to_save['직원번호'].astype(object)

                    if selected_author != "선택안함" and target_author_name:
                        clean_selected_author = selected_author.strip()
                        mask = df_a_to_save['AUTHOR'].astype(str).str.strip() == clean_selected_author
                        
                        # 기본 이름은 u_info에서 온 이름으로 설정
                        df_a_to_save.loc[mask, '이름'] = str(target_author_name)
                        
                        # matches_for_id = search_users_by_name(target_author_name)
                        # target_user_id = None
                        # if matches_for_id:
                        #     target_user_id = matches_for_id[0]['id']
                        #     for user in matches_for_id:
                        #         eng_names = [user.get(f'hname{i}') for i in range(1, 5) if user.get(f'hname{i}')]
                        #         if clean_selected_author in eng_names:
                        #             target_user_id = user['id']
                        # #             break
                        # if target_user_id:
                        #     df_a_to_save.loc[mask, '직원번호'] = str(target_user_id)
                        target_user_id_to_save = None
                        if target_id_from_upload and target_id_from_upload.strip():
                            chosen_user = st.session_state.get('receipt_chosen_user')

                        if chosen_user:
                            # 동명이인 처리 등에서 선택된 직원이 있으면 그 정보를 우선 사용
                            target_user_id_to_save = chosen_user['id']
                            # 이름도 HR DB에 있는 정확한 이름으로 업데이트
                            df_a_to_save.loc[mask, '이름'] = str(chosen_user['name'])
                        elif target_id_from_upload and target_id_from_upload.strip():
                            # 비회원 업로드 시 입력한 직원번호가 있으면 차선으로 사용
                            target_user_id_to_save = target_id_from_upload
                        else:
                            matches_for_id = search_users_by_name(target_author_name)
                            if matches_for_id:
                                target_user_id_to_save = matches_for_id[0]['id']
                                for user in matches_for_id:
                                    eng_names = [user.get(f'hname{i}') for i in range(1, 5) if user.get(f'hname{i}')]
                                    if clean_selected_author in eng_names:
                                        target_user_id_to_save = user['id']
                                        break
                        
                        if target_user_id_to_save:
                            df_a_to_save.loc[mask, '직원번호'] = str(target_user_id_to_save)

                    key_cols = ["PDF_FILE_NAME"]
                    try:
                        conn = sqlite3.connect(DB_FILE)
                        cur = conn.cursor()
                        cur.execute("PRAGMA table_info(a_info)")
                        columns = [info[1] for info in cur.fetchall()]
                        if '이름' not in columns: cur.execute("ALTER TABLE a_info ADD COLUMN 이름 TEXT")
                        if '직원번호' not in columns: cur.execute("ALTER TABLE a_info ADD COLUMN 직원번호 TEXT")
                        conn.commit()
                        conn.close()
                    except Exception as e: print(f"Column check error: {e}")

                    # [수정] user_id 전달하여 이력 관리 (접수처리는 관리자만 하므로 'AD00000' 혹은 현재 로그인 유저)
                    c_saved = update_or_add_paper_data(df_c_transposed, "c_info", key_cols, user_id=st.session_state.username)
                    a_saved = update_or_add_paper_data(df_a_to_save, "a_info", key_cols, user_id=st.session_state.username)
                    
                    if c_saved and a_saved:
                        try:
                            conn = sqlite3.connect(DB_FILE)
                            cur = conn.cursor()
                            # -------------------------------------------------------------
                            # [추가] 변경 신청 처리 완료 시, 구버전 파일 정리
                            # -------------------------------------------------------------
                            cur.execute("SELECT OLD_FILE_NAME FROM u_info WHERE PDF_FILE_NAME = ?", (st.session_state.receipt_target_pdf,))
                            row = cur.fetchone()
                            if row and row[0]:
                                old_pdf = row[0]
                                # 해시 중복이 아닌, 새로운 파일로 교체된 경우 구버전 파일/DB 삭제
                                if old_pdf != st.session_state.receipt_target_pdf:
                                    cur.execute("DELETE FROM c_info WHERE PDF_FILE_NAME = ?", (old_pdf,))
                                    cur.execute("DELETE FROM a_info WHERE PDF_FILE_NAME = ?", (old_pdf,))
                                    delete_paper_files(old_pdf)
                            # -------------------------------------------------------------                            
                            cur.execute("UPDATE u_info SET DONE = 1 WHERE PDF_FILE_NAME = ?", (st.session_state.receipt_target_pdf,))
                            conn.commit()
                            
                            # [수정] 다중/단일 모드에 따라 다음 동작 결정
                            if st.session_state.get("receipt_multi_mode"):
                                st.session_state.receipt_multi_current_index += 1
                                # 다음 아이템을 위해 분석 상태 초기화
                                st.session_state.receipt_analysis_done = False
                                st.session_state.receipt_target_pdf = None
                                st.session_state.receipt_target_old_pdf = None # [추가]
                                st.session_state.receipt_editing = False
                                if 'receipt_success_msg' in st.session_state: del st.session_state.receipt_success_msg
                                st.rerun()
                            else:
                                # 기존 단일 모드 완료 로직
                                st.session_state.receipt_success_msg = "저장 및 처리완료 되었습니다."
                                st.session_state.receipt_c_info_original = edited_c.copy()
                                st.session_state.receipt_a_info_original = df_a_to_save.copy()
                                st.session_state.receipt_editing = False
                                st.rerun()

                        except Exception as e: st.error(f"오류: {e}")

            with col_cancel:
                if st.button("취소"):
                    st.session_state.receipt_c_info = st.session_state.receipt_c_info_original.copy()
                    st.session_state.receipt_a_info = st.session_state.receipt_a_info_original.copy()
                    st.session_state.receipt_editing = False
                    st.rerun()

        else:
            st.dataframe(st.session_state.receipt_c_info, use_container_width=True)
            doi_value = st.session_state.receipt_c_info.loc[st.session_state.receipt_c_info["Key"] == "DOI", "Value"]
            if not doi_value.empty:
                st.link_button("🔗 DOI URL", url=doi_value.iloc[0])
            st.dataframe(st.session_state.receipt_a_info[["ROLE", "AUTHOR", "AFFILIATION", "이름"]], use_container_width=True)
            
            col_edit, col_close = st.columns([0.5, 0.5])
            with col_edit:
                if st.button("편집", key="receipt_edit_btn"):
                    st.session_state.receipt_editing = True
                    st.rerun()
            with col_close:
                if st.button("닫기 (분석 종료)"):
                    st.session_state.receipt_analysis_done = False
                    st.session_state.receipt_target_pdf = None
                    st.session_state.receipt_target_old_pdf = None # [추가]
                    st.rerun()

    if st.session_state.get("receipt_success_msg"):
        st.success(st.session_state.receipt_success_msg)
        del st.session_state["receipt_success_msg"]


def main():
    if "logged_in" not in st.session_state: st.session_state.logged_in = False
    if "login_view_mode" not in st.session_state: st.session_state.login_view_mode = "login"
    
    # [중요] 시스템 테마 로드
    if "current_theme" not in st.session_state:
        st.session_state.current_theme = get_system_theme()

    if st.session_state.logged_in: current_layout = "wide"
    elif st.session_state.login_view_mode == "upload": current_layout = "wide"
    else: current_layout = "centered"

    st.set_page_config(page_title="논문실적 수집기", layout=current_layout, page_icon="📄")
    
    # 스타일 적용
    apply_custom_styles(st.session_state.current_theme)
    init_db()

    if "page" not in st.session_state: st.session_state.page = "login"

    if st.session_state.logged_in:
        create_sidebar()
        p = st.session_state.page
        if p == "upload": show_main_app_page()
        elif p == "receipts" and st.session_state.username == "AD00000": show_receipt_processing_page()
        elif p == "my_papers": show_my_papers_page()
        elif p == "my_info": show_my_info_page()
        elif p == "user_management" and st.session_state.username == "AD00000": show_user_management_page()
        elif p == "settings": show_settings_page()
        else: 
            st.session_state.page = "upload"
            st.rerun()
    else:
        show_login_page()

if __name__ == "__main__":
    version = "1.0.4"
    main()