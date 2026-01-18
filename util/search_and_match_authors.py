import os
import sqlite3
from typing import List, Dict, TypedDict

import pandas as pd
from dotenv import load_dotenv

# [수정됨] Pydantic v1 호환성을 위해 import 경로 변경
from pydantic.v1 import BaseModel, Field
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

# --- .env 파일에서 API 키 로드 ---
# .env 파일이 스크립트 실행 위치에 있는지 확인하세요.
if not load_dotenv(override=True):
    print(
        "경고: .env 파일을 찾을 수 없습니다. OPENAI_API_KEY가 환경 변수에 설정되어 있어야 합니다."
    )

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError(
        "❌ 'OPENAI_API_KEY'를 .env 파일이나 환경 변수에서 찾을 수 없습니다."
    )

# [추가됨] API 키가 정상적으로 로드되었는지 확인 (키 자체는 출력하지 않음)
print("✅ OPENAI_API_KEY 로드 완료.")
# print(OPENAI_API_KEY)
MODEL_NAME = "gpt-4o-2024-08-06"

# --- LLM 모델 초기화 ---
llm = ChatOpenAI(model=MODEL_NAME, temperature=0, openai_api_key=OPENAI_API_KEY)


# [수정 없음] Pydantic 모델 정의는 그대로 사용합니다.
class KoreanName(BaseModel):
    """한국 이름 식별 및 번역을 위한 데이터 모델"""

    is_korean_name: bool = Field(
        description="주어진 이름이 한국식 이름인지 여부 (True/False)"
    )
    translated_name: str = Field(
        description="한국식 이름일 경우, 한글로 번역된 이름. 아닐 경우 원래 이름."
    )


class SimilarName(BaseModel):
    """유사 이름 검색을 위한 데이터 모델"""

    most_similar_name: str = Field(
        description="주어진 목록에서 대상 이름과 가장 유사한 이름"
    )


# === LangGraph 상태 정의 ===
class GraphState(TypedDict):
    """
    그래프의 각 단계 간에 전달될 데이터의 상태를 정의합니다.
    """

    db_path: str
    author_names: List[str]
    user_names: List[str]
    korean_authors: List[Dict[str, str]]
    matches: List[Dict[str, str]]
    final_result: List[str]


# === LangGraph 노드 함수 정의 ===
def fetch_names_from_db(state: GraphState) -> GraphState:
    """a_info와 user_info 테이블에서 이름을 가져옵니다."""
    print("--- 1. 데이터베이스에서 이름 가져오는 중 ---")
    db_path = state["db_path"]
    try:
        with sqlite3.connect(db_path) as conn:
            a_info_df = pd.read_sql_query(
                "SELECT DISTINCT AUTHOR FROM a_info ORDER BY AUTHOR;", conn
            )
            author_names = a_info_df["AUTHOR"].tolist()

            user_info_df = pd.read_sql_query(
                "SELECT name FROM user_info ORDER BY name;", conn
            )
            user_names = user_info_df["name"].tolist()

        test_author_names = author_names[:30]

        print(f"✅ 총 {len(author_names)}명의 저자 중 상위 10명을 테스트합니다.")
        print(f"✅ 사용자 {len(user_names)}명을 찾았습니다.")
        return {**state, "author_names": test_author_names, "user_names": user_names}
    except Exception as e:
        print(f"❌ 데이터베이스 조회 중 오류 발생: {e}")
        return {**state, "author_names": [], "user_names": []}


def translate_korean_names(state: GraphState) -> GraphState:
    """저자 이름이 한국식인지 식별하고 한글로 번역합니다."""
    print("\n--- 2. 한국식 이름 식별 및 번역 중 ---")
    author_names = state["author_names"]
    korean_authors = []

    # JSON 출력을 위해 LLM 구성 (function calling 방식 사용)
    structured_llm = llm.with_structured_output(KoreanName)
    print(len(author_names))
    print(author_names)
    for author in author_names:
        prompt = f"""
        당신은 사람의 이름을 분석하는 전문가입니다. 주어진 이름 '{author}'가 한국인의 로마자 표기 이름인지 판단하고, 맞다면 자연스러운 한글 이름으로 번역해 주세요.

        ### 분석 규칙:
        1.  **구조:** 한국 이름은 보통 1음절의 성(Family Name)과 2음절의 이름(Given Name)으로 구성됩니다. 영어로 변환할 때는 성을 마지막에 위치시킨다. (예: 김철수 Cheol-su Kim)
        2.  **표기법:** 이름은 하이픈(-)으로 연결되거나('Gil-dong'), 띄어쓰기로 구분되거나('Min Jun'), 붙여쓸 수 있습니다('Yuna').
        3.  **보수적 판단:** 이름에 중간 이니셜(예: 'Adam I. Rubin')이 있거나, 서양식 이름(예: 'Cardona', 'Smith')이 포함된 경우 한국 이름이 아닐 확률이 높습니다. 확실하지 않으면 한국 이름이 아니라고 판단하세요.

        ### 긍정 예시 (이런 이름은 한국 이름입니다):
        * 'Gil-dong Hong' -> '홍길동'
        * 'Cheol-su Kim' -> '김철수'
        * 'Younghee Lee' -> '이영희'
        * 'Ji Sung Park' -> '박지성'

        ### 부정 예시 (이런 이름은 한국 이름이 아닙니다):
        * 'A. Cardona' (이니셜 포함)
        * 'John Smith' (전형적인 서양 이름)
        * 'Abdallah Elmughrabi' (비한국어권 이름)

        'is_korean_name'이 true일 경우, 가장 자연스러운 한글 표기법으로 'translated_name'을 채워주세요. 아닐 경우, 'translated_name'에는 원본 이름을 그대로 넣어주세요.
        JSON 형식으로만 답변해주세요.
        """
        try:
            result = structured_llm.invoke(prompt)
            if result.is_korean_name:
                korean_authors.append(
                    {"original": author, "translated": result.translated_name}
                )
                print(
                    f"   - '{author}' -> '{result.translated_name}' (한국 이름으로 식별 및 번역)"
                )
        except Exception as e:
            print(f"   - ❌ '{author}' 처리 중 오류 발생: {e}")
            # [추가됨] 오류 발생 시 다음 이름으로 넘어가도록 루프를 중단하지 않음
            continue

    print(f"✅ 총 {len(korean_authors)}개의 한국 이름을 식별했습니다.")
    return {**state, "korean_authors": korean_authors}


def find_matches(state: GraphState) -> GraphState:
    """번역된 한국 이름과 사용자 목록을 비교하여 일치/유사 항목을 찾습니다."""
    print("\n--- 3. 사용자 목록과 이름 비교 중 ---")
    korean_authors = state["korean_authors"]
    user_names = state["user_names"]
    matches = []

    # user_names 리스트가 비어있으면 유사 이름 찾기를 시도하지 않음
    if not user_names:
        print("   - ⚠️ 사용자 목록이 비어 있어 매칭을 건너뜁니다.")
        return {**state, "matches": matches}

    structured_llm_similar = llm.with_structured_output(SimilarName)

    for author in korean_authors:
        translated_name = author["translated"]

        if translated_name in user_names:
            match_info = {
                "original_author": author["original"],
                "translated_author": translated_name,
                "matched_user": translated_name,
                "match_type": "정확히 일치",
            }
            matches.append(match_info)
            print(f"   - ✅ 정확히 일치: '{translated_name}'")
            continue

        print(
            f"   - ⚠️ '{translated_name}'에 대해 정확히 일치하는 사용자가 없어 유사한 이름을 찾습니다."
        )
        prompt_similar = f"""
        당신은 한국어 이름 매칭 전문가입니다. 주어진 이름 '{translated_name}'과 아래 '사용자 목록'에 있는 이름들을 비교하여, 발음과 철자를 모두 고려했을 때 가장 유사한 이름 **단 한 개**만 찾아주세요.

        -   **대상 이름:** '{translated_name}'
        -   **사용자 목록:** {', '.join(user_names)}

        가장 유사도가 높다고 판단되는 이름을 JSON 형식으로 답변해주세요.
        """
        try:
            similar_result = structured_llm_similar.invoke(prompt_similar)
            most_similar = similar_result.most_similar_name

            match_info = {
                "original_author": author["original"],
                "translated_author": translated_name,
                "matched_user": most_similar,
                "match_type": "유사",
            }
            matches.append(match_info)
            print(f"   - ➡️  유사 이름: '{translated_name}' -> '{most_similar}'")
        except Exception as e:
            print(f"   - ❌ '{translated_name}'의 유사 이름 검색 중 오류: {e}")
            continue

    return {**state, "matches": matches}


# 이하 코드는 수정할 필요가 없습니다.
def format_results(state: GraphState) -> GraphState:
    print("\n--- 4. 최종 결과 정리 중 ---")
    matches = state["matches"]
    if not matches:
        print("결과: 매칭되는 저자를 찾지 못했습니다.")
        return {**state, "final_result": ["매칭되는 저자를 찾지 못했습니다."]}

    output = ["--- 저자-사용자 매칭 결과 ---"]
    for match in matches:
        output.append(
            f"저자(원문): {match['original_author']} | "
            f"저자(번역): {match['translated_author']} | "
            f"매칭된 사용자: {match['matched_user']} ({match['match_type']})"
        )
    print("\n".join(output))
    return {**state, "final_result": output}


def build_graph():
    workflow = StateGraph(GraphState)
    workflow.add_node("fetch_names", fetch_names_from_db)
    workflow.add_node("translate", translate_korean_names)
    workflow.add_node("find_matches", find_matches)
    workflow.add_node("format_results", format_results)
    workflow.set_entry_point("fetch_names")
    workflow.add_edge("fetch_names", "translate")
    workflow.add_edge("translate", "find_matches")
    workflow.add_edge("find_matches", "format_results")
    workflow.add_edge("format_results", END)
    return workflow.compile()


def find_korean_author_matches(db_path: str) -> List[str]:
    app = build_graph()
    initial_state = {"db_path": db_path}
    final_state = app.invoke(initial_state)
    return final_state.get("final_result", ["오류: 최종 결과를 가져올 수 없습니다."])


if __name__ == "__main__":
    DB_FILE = "paper.db"
    print("\n\n=== 저자-사용자 매칭 프로세스 시작 ===")
    results = find_korean_author_matches(DB_FILE)
    print("\n=== 최종 결과 ===")
    for line in results:
        print(line)
