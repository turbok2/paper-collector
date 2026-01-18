import sqlite3
import pandas as pd
import os

# --- 통합될 새로운 데이터베이스 파일 이름 ---
DB_NAME = "paper.db"

# --- 원본 데이터베이스 파일과 테이블 이름 매핑 ---
SOURCE_DBS = {
    "user_info.db": "user_info",
    "c_info.db": "c_info",
    "a_info.db": "a_info",
    "hr_info.db": "hr_info",
}


def migrate_databases():
    """
    기존의 4개 .db 파일에서 데이터를 읽어와
    하나의 paper.db 파일로 통합합니다.
    """
    print(f"'{DB_NAME}'으로 데이터베이스 통합을 시작합니다...")

    # 새로운 통합 DB에 연결
    conn_new = sqlite3.connect(DB_NAME)

    try:
        # 각 원본 DB 파일에 대해 반복 작업
        for db_file, table_name in SOURCE_DBS.items():
            # 원본 DB 파일이 존재하는지 확인
            if not os.path.exists(db_file):
                print(
                    f"[경고] 원본 파일 '{db_file}'을(를) 찾을 수 없습니다. 이 테이블은 건너뜁니다."
                )
                continue

            print(f"- '{db_file}' 파일 처리 중...")

            # 원본 DB에 연결하여 데이터를 DataFrame으로 읽기
            conn_old = sqlite3.connect(db_file)
            try:
                df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn_old)

                # 읽어온 데이터를 새로운 통합 DB의 테이블에 저장
                # if_exists='replace'는 스크립트를 여러 번 실행해도 덮어쓰므로 안전합니다.
                df.to_sql(table_name, conn_new, if_exists="replace", index=False)

                print(
                    f"  -> '{table_name}' 테이블에 {len(df)}개의 행을 성공적으로 통합했습니다."
                )

            except Exception as e:
                print(f"  [오류] '{db_file}' 처리 중 오류 발생: {e}")
            finally:
                conn_old.close()

    except Exception as e:
        print(f"통합 프로세스 중 심각한 오류가 발생했습니다: {e}")
    finally:
        conn_new.close()
        print(f"\n'{DB_NAME}'으로 데이터베이스 통합 작업이 완료되었습니다.")


if __name__ == "__main__":
    migrate_databases()
