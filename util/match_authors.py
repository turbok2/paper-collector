# match_authors.py
import os
import sqlite3
from dotenv import load_dotenv
from LLM_MODEL import GPTApi
from difflib import SequenceMatcher

# 환경 변수 로드
load_dotenv(override=True)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("❌🔑❌ 'OPENAI_API_KEY'가 .env 파일에 없습니다.")

MODEL_NAME = "gpt-4o-2024-08-06"


def load_processed_authors(csv_path="match_results.csv"):
    """
    이미 처리된 author 목록을 CSV 파일에서 로드합니다.

    Args:
        csv_path (str): CSV 파일 경로

    Returns:
        set: 처리된 author 이름 집합
    """
    import pandas as pd

    try:
        df = pd.read_csv(csv_path, encoding="utf-8-sig")
        processed_authors = set(df["author"].tolist())
        print(f"📁 기존 처리된 저자 {len(processed_authors)}명을 불러왔습니다.\n")
        return processed_authors
    except FileNotFoundError:
        print(f"📁 {csv_path} 파일이 없습니다. 새로 시작합니다.\n")
        return set()
    except Exception as e:
        print(f"[ERROR] CSV 파일 로드 중 오류: {e}\n")
        return set()


# 프롬프트 정의
KOREAN_NAME_CHECK_PROMPT = """
You are an expert in identifying Korean names written in English.

Given an English name, determine if it represents a Korean person's name.

Korean names typically have these characteristics:
- Usually 2-4 syllables when romanized
- Common patterns: [Given name] [Family name] (e.g., Minsoo Kim, Jiyoung Park)
- Family names: Kim, Lee, Park, Choi, Jung, Kang, Cho, Yoon, Jang, Lim, Han, Oh, Seo, Shin, Kwon, Hwang, Ahn, Song, Hong, etc.
- Given names often have repeated consonants or vowels (e.g., Seung-ho, Min-jung)

Examples of Korean names in English:
- Taehyung Kim
- Jieun Lee
- Seojun Park
- Minho Choi

Examples of non-Korean names:
- John Smith
- Maria Garcia
- Wang Wei
- Tanaka Yuki

Analyze the given name and respond with ONLY "YES" if it's a Korean name, or "NO" if it's not.

Name to analyze: {author_name}

Answer (YES/NO):
"""

TRANSLATE_TO_KOREAN_PROMPT = """
You are an expert in translating romanized Korean names back to Korean (Hangul).

IMPORTANT: The input name is in the format [Given name] [Family name].
You must convert it to Korean format: [Family name][Given name] in Hangul.

Examples:
- "Minsoo Kim" → "김민수" (Kim is family name, Minsoo is given name)
- "Jieun Lee" → "이지은" (Lee is family name, Jieun is given name)
- "Seojun Park" → "박서준" (Park is family name, Seojun is given name)
- "Yuna Choi" → "최유나" (Choi is family name, Yuna is given name)
- "A Mi Kim" → "김아미" (Kim is family name, A Mi is given name)

Rules:
- The LAST word is always the family name (성)
- Everything BEFORE the last word is the given name (이름)
- Convert to Korean format: [성][이름] in Hangul
- Use common Korean name conventions
- If uncertain, provide the most common spelling

Romanized name: {author_name}

Provide ONLY the Korean (Hangul) name without any explanation:
"""


def is_korean_name(author_name, llm):
    """
    주어진 영문 이름이 한국식 이름인지 LLM을 통해 판단합니다.

    Args:
        author_name (str): 영문 이름
        llm: LLM API 인스턴스

    Returns:
        bool: 한국식 이름이면 True, 아니면 False
    """
    try:
        prompt = KOREAN_NAME_CHECK_PROMPT.format(author_name=author_name)
        response = llm.llm.invoke(prompt)

        # response 객체에서 content 추출
        if hasattr(response, "content"):
            result = response.content.strip().upper()
        else:
            result = str(response).strip().upper()

        return "YES" in result
    except Exception as e:
        print(f"[ERROR] 한국식 이름 판단 중 오류: {e}")
        return False


def translate_to_korean(author_name, llm):
    """
    영문 이름을 한국어 이름으로 번역합니다.
    [Given name] [Family name] → [성][이름] 형식으로 변환

    Args:
        author_name (str): 영문 이름 (Given name Family name 순서)
        llm: LLM API 인스턴스

    Returns:
        str: 한국어 이름 (성+이름 순서)
    """
    try:
        prompt = TRANSLATE_TO_KOREAN_PROMPT.format(author_name=author_name)
        response = llm.llm.invoke(prompt)

        # response 객체에서 content 추출
        if hasattr(response, "content"):
            korean_name = response.content.strip()
        else:
            korean_name = str(response).strip()

        return korean_name
    except Exception as e:
        print(f"[ERROR] 한국어 번역 중 오류: {e}")
        return author_name


def has_chonnam_affiliation(affiliations):
    """
    소속 정보 중에 'chonnam national'이 포함되어 있는지 확인합니다.

    Args:
        affiliations (list): 소속 정보 리스트

    Returns:
        bool: chonnam national이 있으면 True, 없으면 False
    """
    if not affiliations:
        return False

    for affiliation in affiliations:
        if affiliation and "chonnam national" in affiliation.lower():
            return True

    return False


def calculate_similarity(str1, str2):
    """
    두 문자열 간의 유사도를 계산합니다.

    Args:
        str1 (str): 첫 번째 문자열
        str2 (str): 두 번째 문자열

    Returns:
        float: 유사도 (0.0 ~ 1.0)
    """
    return SequenceMatcher(None, str1, str2).ratio()


def match_authors_with_users(db_path="paper.db", limit=10):
    """
    a_info 테이블의 AUTHOR를 읽고, 전남대 소속이면서 한국식 이름이면
    한국어로 번역한 후 user_info 테이블의 name과 매칭하여 결과를 반환합니다.

    Args:
        db_path (str): SQLite 데이터베이스 경로
        limit (int): 처리할 AUTHOR 수 (테스트용)

    Returns:
        list: 매칭 결과 리스트
    """
    # 기존 처리된 author 로드
    processed_authors = load_processed_authors("match_results.csv")
    # LLM 초기화
    llm = GPTApi(model_name=MODEL_NAME, api_key=OPENAI_API_KEY)

    # DB 연결
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # a_info 테이블에서 AUTHOR와 AFFILIATION 읽기
    # 같은 AUTHOR라도 AFFILIATION이 다를 수 있으므로 그룹화
    if limit == 0:
        # limit이 0이면 전체 데이터 조회
        cursor.execute("""
            SELECT AUTHOR, GROUP_CONCAT(AFFILIATION, '|||') as AFFILIATIONS
            FROM a_info 
            WHERE AUTHOR IS NOT NULL AND AUTHOR != ''
            GROUP BY AUTHOR
            ORDER BY AUTHOR
        """)
    else:
        # limit이 지정되면 해당 개수만큼만 조회
        cursor.execute("""
            SELECT AUTHOR, GROUP_CONCAT(AFFILIATION, '|||') as AFFILIATIONS
            FROM a_info 
            WHERE AUTHOR IS NOT NULL AND AUTHOR != ''
            GROUP BY AUTHOR
            ORDER BY AUTHOR
            LIMIT ?
        """, (limit,))
    author_data = cursor.fetchall()

    # user_info 테이블에서 name 읽기
    cursor.execute(
        "SELECT DISTINCT name FROM user_info WHERE name IS NOT NULL AND name != ''"
    )
    user_names = [row[0] for row in cursor.fetchall()]

    print(f"📊 총 {len(author_data)}명의 저자를 처리합니다.")
    print(f"📊 user_info에 {len(user_names)}명의 사용자가 있습니다.\n")

    results = []

    for idx, (author, affiliations_str) in enumerate(author_data, 1):
        print(f"[{idx}/{len(author_data)}] 처리 중: {author}")
        # 이미 처리된 author면 스킵
        if author in processed_authors:
            print(f"  → 이미 처리됨. 패스.\n")
            continue
        # AFFILIATION 리스트로 변환
        affiliations = affiliations_str.split("|||") if affiliations_str else []

        # 1. 전남대 소속 확인
        if not has_chonnam_affiliation(affiliations):
            print(f"  → 전남대 소속 아님. 패스.\n")
            continue

        print(f"  → 전남대 소속 확인됨")

        # 2. 한국식 이름인지 확인
        if not is_korean_name(author, llm):
            print(f"  → 한국식 이름이 아님. 패스.\n")
            continue

        # 3. 한국어로 번역 (Given name Family name → 성이름 순서)
        korean_name = translate_to_korean(author, llm)
        print(f"  → 한국어 번역: {korean_name}")

        # 4. user_info의 name과 매칭
        best_match = None
        best_similarity = 0.0

        # 한국 이름에서 성과 이름 분리
        if len(korean_name) < 2:
            print(f"  → 이름이 너무 짧음. 패스.\n")
            continue

        korean_family_name = korean_name[0]  # 첫 글자가 성
        korean_given_name = korean_name[1:]  # 나머지가 이름

        for user_name in user_names:
            # user_name에서도 성과 이름 분리
            if len(user_name) < 2:
                continue

            user_family_name = user_name[0]  # 첫 글자가 성
            user_given_name = user_name[1:]  # 나머지가 이름

            # 1) 성이 다르면 무조건 제외
            if korean_family_name != user_family_name:
                continue

            # 2) 이름 길이가 다르면 무조건 제외 (2글자 vs 3글자)
            if len(korean_given_name) != len(user_given_name):
                continue

            # 3) 성이 같고 이름 길이도 같으면 유사도 계산
            similarity = calculate_similarity(korean_name, user_name)
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = user_name

        # 5. 결과 저장
        match_status = (
            "✅ 완전 일치"
            if best_similarity == 1.0
            else f"🔍 유사 ({best_similarity:.2f})"
        )
        print(f"  → 매칭 결과: {best_match} {match_status}\n")

        results.append(
            {
                "author": author,
                "korean_name": korean_name,
                "matched_user": best_match,
                "similarity": best_similarity,
                "affiliations": affiliations,
            }
        )

    conn.close()

    return results


def print_results(results):
    """
    매칭 결과를 보기 좋게 출력합니다.
    """
    print("\n" + "=" * 80)
    print("📋 매칭 결과 요약 (전남대 소속 한국식 이름만)")
    print("=" * 80)

    for i, result in enumerate(results, 1):
        print(f"\n[{i}]")
        print(f"  영문 이름:     {result['author']}")
        print(f"  한국어 이름:   {result['korean_name']}")
        print(f"  매칭된 사용자: {result['matched_user']}")
        print(f"  유사도:        {result['similarity']:.2%}")

        if result["similarity"] == 1.0:
            print(f"  상태:          ✅ 완전 일치")
        elif result["similarity"] >= 0.8:
            print(f"  상태:          🟢 높은 유사도")
        elif result["similarity"] >= 0.6:
            print(f"  상태:          🟡 중간 유사도")
        else:
            print(f"  상태:          🔴 낮은 유사도")

        # 소속 정보 출력 (chonnam national 포함된 것만)
        chonnam_affs = [
            aff for aff in result["affiliations"] if "chonnam national" in aff.lower()
        ]
        if chonnam_affs:
            print(f"  전남대 소속:   {chonnam_affs[0]}")

    print("\n" + "=" * 80)
    print(f"총 {len(results)}건의 매칭 결과")
    print("=" * 80)


if __name__ == "__main__":
    # 함수 실행
    results = match_authors_with_users(db_path="paper.db", limit=4575)

    # 결과 출력
    print_results(results)

    # 결과를 DataFrame으로 변환 (선택사항)
    import pandas as pd

    # 결과를 CSV로 저장
    if results:
        df = pd.DataFrame(results)
        df.to_csv(
            "match_results.csv",
            index=False,
            encoding="utf-8-sig",
            mode="a",
            header=not os.path.exists("match_results.csv"),
        )
        print(f"\n✅ {len(results)}건의 결과가 match_results.csv에 저장되었습니다.")
