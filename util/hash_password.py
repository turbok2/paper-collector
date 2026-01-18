import sqlite3
import pandas as pd
import bcrypt
import os
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed

DB_NAME = "paper.db"


def create_hash(password):
    """단일 비밀번호를 해싱하는 함수 (병렬 처리용)"""
    # password가 문자열이 아니거나 비어있으면 그대로 반환
    if not isinstance(password, str) or not password:
        return password

    # 이미 bcrypt로 해시된 값인지 확인 (보통 '$2a$', '$2b$', '$2y$'로 시작)
    if password.startswith("$2"):
        return password  # 이미 암호화된 값이면 그대로 반환

    # 암호화되지 않은 값이면 해싱 수행
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def hash_user_info_passwords():
    """
    'user_info' 테이블의 'password' 컬럼 값을 병렬 처리로 암호화합니다.
    """
    if not os.path.exists(DB_NAME):
        print(f"[오류] 데이터베이스 파일 '{DB_NAME}'을(를) 찾을 수 없습니다.")
        return

    conn = sqlite3.connect(DB_NAME)
    print(f"'{DB_NAME}' 데이터베이스의 'user_info' 테이블 암호화를 시작합니다...")

    try:
        df = pd.read_sql_query("SELECT * FROM user_info", conn)

        if "password" not in df.columns:
            print(f"[오류] 'user_info' 테이블에 'password' 컬럼이 존재하지 않습니다.")
            return

        # 1. 암호화가 필요한 비밀번호만 필터링
        passwords_to_hash = df["password"][
            df["password"].apply(
                lambda x: isinstance(x, str) and not x.startswith("$2")
            )
        ]

        if passwords_to_hash.empty:
            print("모든 비밀번호가 이미 암호화되어 있습니다. 작업을 종료합니다.")
            return

        print(f"총 {len(passwords_to_hash)}개의 비밀번호를 암호화합니다...")

        # 2. 병렬 처리를 사용하여 암호화 실행
        # ProcessPoolExecutor를 사용하면 CPU 코어 수만큼 프로세스를 만들어 작업을 분배
        with ProcessPoolExecutor() as executor:
            # 해시 결과를 저장할 딕셔너리 {인덱스: 해시된 비밀번호}
            results = {}

            # tqdm을 이용해 진행률 표시
            # executor.map 대신 submit을 사용해 인덱스를 함께 관리
            futures = {
                executor.submit(create_hash, password): index
                for index, password in passwords_to_hash.items()
            }

            for future in tqdm(
                as_completed(futures),
                total=len(passwords_to_hash),
                desc="암호화 진행률",
            ):
                index = futures[future]
                try:
                    hashed_password = future.result()
                    results[index] = hashed_password
                except Exception as e:
                    print(f"오류 발생 (인덱스 {index}): {e}")

        # 3. 원본 데이터프레임에 암호화된 결과 업데이트
        for index, hashed_password in results.items():
            df.loc[index, "password"] = hashed_password

        # 4. 변경된 DataFrame을 다시 DB에 저장
        print("\n데이터베이스에 변경사항을 저장하는 중입니다...")
        df.to_sql("user_info", conn, if_exists="replace", index=False)
        conn.commit()

        print("모든 작업이 성공적으로 완료되었습니다.")

    except Exception as e:
        conn.rollback()
        print(f"작업 중 오류가 발생했습니다: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    hash_user_info_passwords()
