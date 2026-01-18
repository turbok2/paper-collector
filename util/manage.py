import streamlit as st
import sqlite3
import pandas as pd
import bcrypt

# ==============================================================================
# 1. 데이터베이스 설정 및 함수
# ==============================================================================
DB_NAME = "paper.db"

def load_data(table_name, exclude_columns=None):
    """지정된 테이블에서 데이터를 로드하고 특정 컬럼을 제외할 수 있습니다."""
    conn = sqlite3.connect(DB_NAME)
    try:
        query = f"SELECT * FROM {table_name}"
        df = pd.read_sql_query(query, conn)
        if exclude_columns:
            cols_to_drop = [col for col in exclude_columns if col in df.columns]
            df = df.drop(columns=cols_to_drop)
        return df
    finally:
        conn.close()

def save_data(table_name, df):
    """데이터프레임을 지정된 테이블에 저장합니다."""
    conn = sqlite3.connect(DB_NAME)
    try:
        df.to_sql(table_name, conn, if_exists="replace", index=False)
    finally:
        conn.close()

# ==============================================================================
# 2. Streamlit 앱 구성
# ==============================================================================
st.set_page_config(layout="wide")
st.title("🗃️ DB Manager")

# --- 탭 이름과 실제 DB 테이블 이름 매핑 (Users 제외) ---
db_mapping = {
    "User Info": "user_info",
    "C Info": "c_info",
    "A Info": "a_info",
}
table_display_names = list(db_mapping.keys())

# ==============================================================================
# 3. 사이드바 (탐색 및 기능)
# ==============================================================================
with st.sidebar:
    st.header("🗂️ 테이블 선택")
    
    # 사이드바 라디오 버튼으로 표시할 테이블 선택
    selected_display_name = st.radio(
        "관리할 테이블을 선택하세요:",
        options=table_display_names,
        label_visibility="collapsed"
    )
    
    # 선택된 이름에 해당하는 실제 테이블 이름 가져오기
    table_name = db_mapping[selected_display_name]

    st.divider()

    # --- 선택된 테이블에 대한 공용 기능 ---
    with st.expander(f"⚙️ {selected_display_name} 편집 메뉴", expanded=True):
        
        if st.button(f"🔄 Reload Data", key=f"reload_{table_name}", use_container_width=True):
            keys_to_delete = [f"df_{table_name}", f"df_display_{table_name}"]
            for key in keys_to_delete:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

        action = st.radio(
            f"작업 선택", ["행 편집", "행 추가", "행 삭제"],
            key=f"action_{table_name}",
        )

        # --- 데이터 로드 (user_info는 비밀번호 제외) ---
        is_user_info = (selected_display_name == "User Info")
        if is_user_info:
            df_display = st.session_state.get(f"df_display_{table_name}", load_data(table_name))
            # df_display = st.session_state.get(f"df_display_{table_name}", load_data(table_name, exclude_columns=['password']))
            df_full = load_data(table_name)
        else:
            df_display = st.session_state.get(f"df_{table_name}", load_data(table_name))
            df_full = df_display

        # --- 공용 액션 처리 ---
        if action == "행 편집":
            if df_display.empty: st.warning("데이터가 없습니다.")
            else:
                row_to_edit = st.selectbox("편집할 행 선택", df_display.index, key=f"edit_row_{table_name}")
                edited_row = {}
                for col in df_display.columns:
                    default_value = str(df_display.loc[row_to_edit, col])
                    edited_row[col] = st.text_input(f"{col}", value=default_value, key=f"edit_{table_name}_{col}_{row_to_edit}")
                
                if st.button("변경사항 저장", key=f"save_edit_{table_name}"):
                    for col, val in edited_row.items():
                        original_dtype = df_full[col].dtype
                        try: df_full.loc[row_to_edit, col] = pd.Series([val]).astype(original_dtype)[0]
                        except (ValueError, TypeError): st.error(f"'{col}' 컬럼에 잘못된 값이 입력되었습니다."); break
                    else:
                        save_data(table_name, df_full)
                        st.session_state[f"df_display_{table_name}" if is_user_info else f"df_{table_name}"] = df_full.drop(columns=['password']) if is_user_info else df_full
                        st.success("데이터베이스가 업데이트되었습니다."); st.rerun()

        elif action == "행 추가":
            new_row = {}
            for col in df_display.columns:
                new_row[col] = st.text_input(f"새 {col} 입력", key=f"add_{table_name}_{col}")

            if st.button("새 행 추가", key=f"add_row_{table_name}"):
                new_df = pd.DataFrame([new_row])
                for col in df_full.columns:
                    if col not in new_df.columns: continue
                    try: new_df[col] = new_df[col].astype(df_full[col].dtype)
                    except (ValueError, TypeError): st.error(f"'{col}' 컬럼의 데이터 타입이 일치하지 않습니다."); break
                else:
                    df_updated = pd.concat([df_full, new_df], ignore_index=True)
                    save_data(table_name, df_updated)
                    st.session_state[f"df_display_{table_name}" if is_user_info else f"df_{table_name}"] = df_updated.drop(columns=['password']) if is_user_info else df_updated
                    st.success("새로운 행이 추가되었습니다."); st.rerun()
        
        elif action == "행 삭제":
            if df_display.empty: st.warning("데이터가 없습니다.")
            else:
                row_to_delete = st.selectbox("삭제할 행 선택", df_display.index, key=f"delete_row_{table_name}")
                if st.button("선택한 행 삭제", key=f"delete_button_{table_name}"):
                    df_deleted = df_full.drop(row_to_delete).reset_index(drop=True)
                    save_data(table_name, df_deleted)
                    st.session_state[f"df_display_{table_name}" if is_user_info else f"df_{table_name}"] = df_deleted.drop(columns=['password']) if is_user_info else df_deleted
                    st.success("선택한 행이 삭제되었습니다."); st.rerun()
        
        # --- 일괄 입력 ---
        st.divider()
        st.subheader("📁 일괄 입력")
        # ... (이하 기능은 기존과 동일)

        # --- 위험 구역 ---
        st.divider()
        st.subheader("⚠️ 위험 구역")
        # ... (이하 기능은 기존과 동일)

# ==============================================================================
# 4. 메인 컨텐츠 표시
# ==============================================================================

st.header(f"{selected_display_name} 데이터")

# 데이터 로드 및 표시 (사이드바에서 이미 로드됨)
st.markdown(f"**- 총 {len(df_display)}개**의 데이터가 있습니다.")
st.dataframe(df_display, use_container_width=True)