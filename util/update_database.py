import sqlite3
import pandas as pd
import os
import bcrypt

DB_NAME = "paper.db"


def update_db_schema():
    """
    2. 'user_info' 테이블에 password 컬럼을 추가하고 값을 채웁니다.
    """
    if not os.path.exists(DB_NAME):
        print(
            f"[오류] '{DB_NAME}' 파일을 찾을 수 없습니다. manage.py를 실행하기 전 create_paper_db.py를 먼저 실행해야 합니다."
        )
        return

    conn = sqlite3.connect(DB_NAME)
    print(f"'{DB_NAME}' 데이터베이스 스키마 업데이트를 시작합니다...")

    try:
        cursor = conn.cursor()

        # # 1. 'users' 테이블 삭제
        # try:
        #     cursor.execute("DROP TABLE users")
        #     print("- 'users' 테이블을 성공적으로 삭제했습니다.")
        # except sqlite3.OperationalError:
        #     print("- 'users' 테이블이 이미 존재하지 않아 건너뜁니다.")

        # 2. 'user_info' 테이블에 password 추가 및 업데이트
        # 먼저 user_info 데이터를 DataFrame으로 로드
        df = pd.read_sql_query("SELECT * FROM user_info", conn)
        import time

        # df 로드 이후에 추가
        print(f"[디버그] user_info 행 개수: {len(df)}")

        # bcrypt 1회 시간 측정
        test_pwd = (str(df["id"].iloc[0]) + "!!").encode("utf-8")
        start = time.time()
        bcrypt.hashpw(test_pwd, bcrypt.gensalt(rounds=10))
        elapsed = time.time() - start
        print(f"[디버그] bcrypt 1회 소요 시간(대략): {elapsed:.3f}초")

        total_est = elapsed * len(df)
        print(f"[디버그] 전체 예상 시간(대략): {total_est/60:.1f}분")

        # 'password' 컬럼 추가 (값은 user_id 값에 '!!'를 붙인 것)
        # user_id 컬럼이 문자열이 아닐 경우를 대비해 .astype(str) 추가
        # df["password"] = df["id"].astype(str) + "!!"
        new_password = df["id"].astype(str) + "!!"
        # 각 행마다 bcrypt 해시 생성
        print("[디버그] bcrypt 해시 생성 시작...")
        df["password"] = new_password.apply(
            lambda pwd: bcrypt.hashpw(
                pwd.encode("utf-8"), bcrypt.gensalt(rounds=10)
            ).decode("utf-8")
        )
        print("[디버그] bcrypt 해시 생성 완료")
        print(
            "- 'user_info' 테이블에 'password' 컬럼을 추가하고 값을 업데이트했습니다."
        )

        # 변경된 DataFrame을 다시 DB에 저장
        df.to_sql("user_info", conn, if_exists="replace", index=False)

        conn.commit()
        print("\n데이터베이스 스키마 업데이트가 성공적으로 완료되었습니다.")

    except Exception as e:
        conn.rollback()
        print(f"작업 중 오류가 발생했습니다: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    update_db_schema()
