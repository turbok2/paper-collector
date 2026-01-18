import sqlite3
import pandas as pd
import os

# 파일명 설정
SOURCE_DB = "paper.db"      # 원본 데이터베이스 (읽어올 곳)
TARGET_DB = "user_info.db"  # 새로 저장할 데이터베이스 (저장할 곳)

def extract_user_info_to_new_db():
    # 1. 원본 파일 존재 여부 확인
    if not os.path.exists(SOURCE_DB):
        print(f"[오류] 원본 파일 '{SOURCE_DB}'을 찾을 수 없습니다.")
        return

    print(f"--- 작업 시작: '{SOURCE_DB}' -> '{TARGET_DB}' ---")

    try:
        # -------------------------------------------------------
        # 단계 1: 원본 DB(paper.db)에서 데이터 읽어오기
        # -------------------------------------------------------
        conn_src = sqlite3.connect(SOURCE_DB)
        
        # user_info 테이블의 모든 데이터를 DataFrame으로 가져옵니다.
        try:
            df = pd.read_sql_query("SELECT * FROM user_info", conn_src)
            print(f"[읽기 성공] '{SOURCE_DB}'에서 {len(df)}건의 데이터를 읽었습니다.")
        except Exception as e:
            print(f"[읽기 오류] 테이블을 찾을 수 없거나 읽는 중 에러 발생: {e}")
            conn_src.close()
            return
        
        conn_src.close() # 읽기 끝났으니 원본 연결 종료

        # -------------------------------------------------------
        # 단계 2: 새 DB(user_info.db)에 데이터 저장하기
        # -------------------------------------------------------
        conn_target = sqlite3.connect(TARGET_DB)
        
        # DataFrame을 통째로 새 DB의 'user_info' 테이블로 저장
        # if_exists='replace': 이미 파일/테이블이 있다면 덮어씁니다.
        df.to_sql("user_info", conn_target, if_exists="replace", index=False)
        
        conn_target.close() # 저장 끝났으니 타겟 연결 종료

        print(f"[저장 성공] '{TARGET_DB}' 파일에 'user_info' 테이블 저장을 완료했습니다.")
        print("\n✅ 모든 작업이 성공적으로 끝났습니다.")

    except Exception as e:
        print(f"❌ 작업 중 예상치 못한 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    extract_user_info_to_new_db()