import os
import json
import yaml
import pandas as pd
from dotenv import load_dotenv
from LLM_MODEL import LocalApi, GPTApi
import requests  # requests 라이브러리 임포트


# --- PDF 분석 서비스 호출 함수 ---
def get_pdf_json(pdf_path, service_url, request_timeout):
    """
    지정된 PDF 파일을 외부 서비스로 전송하여 JSON 분석 결과를 받습니다.

    Args:
        pdf_path (str): 분석할 PDF 파일의 로컬 경로.
        service_url (str): PDF 분석 서비스의 URL.
        request_timeout (int): 요청 타임아웃 (초).

    Returns:
        dict or None: 서비스에서 반환된 JSON 데이터 (성공 시), 또는 None (실패 시).
    """
    error = ""
    try:
        with open(pdf_path, "rb") as f:
            files = {"file": (os.path.basename(pdf_path), f, "application/pdf")}
            # st.info(f"PDF 분석 서비스 ({service_url})로 파일을 전송 중입니다. 잠시 기다려 주세요...")
            response = requests.post(service_url, files=files, timeout=request_timeout)

        response.raise_for_status()  # HTTP 오류가 발생하면 예외를 발생시킵니다.
        return response.json(), error
    except requests.exceptions.Timeout:
        error = f"요청 시간 초과: PDF 분석 서비스가 {request_timeout}초 내에 응답하지 않았습니다."
        return None, error
    except requests.exceptions.ConnectionError:
        error = "연결 오류: PDF 분석 서비스에 연결할 수 없습니다. 서비스 URL을 확인하거나 네트워크 상태를 확인해주세요."
        return None, error
    except requests.exceptions.RequestException as e:
        error = f"PDF 분석 요청 중 오류 발생: {e}"
        return None, error
    except json.JSONDecodeError:
        error = "서비스에서 유효한 JSON 응답을 받지 못했습니다."
        return None, error
    except Exception as e:
        error = f"예상치 못한 오류 발생: {e}"
        return None, error


DEBUG = False

PROMPT_PATH = r"Active_prompts_TOTAL.yaml"

LLAMA_URL = "http://10.91.200.20:11437"

MODEL_NAME = "gpt-4o-2024-08-06"  # gpt-4o-2024-11-20
# MODEL_NAME = "gpt-4o-2024-11-20"

# MODEL_NAME = "llama3.1:70b"
# MODEL_NAME = "llama3.1:8b"


# 실행 파라미터
ALLOWED_TYPES = None  # 예: ["Text", "Title"] 또는 None

# TARGET_PAGES = [2] # 원하는 페이지 별도 입력
TARGET_PAGES = None

MAX_PAGE_NUMBER = 2  # 없으면, 1~2 페이지 자동 선택

# [STEP 1] API KEY loading
load_dotenv(override=True)  # modify
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("❌🔑❌ 'OPENAI_API_KEY'가 .env 파일에 없습니다.")
# if DEBUG: print("✅ API KEY LOADED :", bool(OPENAI_API_KEY))


# [STEP 2] ACTIVE_PROMPT loading
def load_prompts(yaml_path):
    with open(yaml_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# [STEP 3] JSON TEXT loading (HURIDOCS)
# INPUT용 JSON 전처리 함수
def extract_text_from_json_blocks(
    json_data,
    allowed_types=None,
    target_pages=None,
    max_page_number=2,
    max_preview_length=3000,
):

    if not isinstance(json_data, list):
        raise ValueError("Expected json_data to be a list of blocks")

    # Determine unique types in data for reference
    all_types = sorted(set(block.get("type", "Unknown") for block in json_data))

    filtered_text_blocks = []
    for block in json_data:
        page = block.get("page_number")
        text = block.get("text", "")
        block_type = block.get("type", "Unknown")

        if not isinstance(page, int) or not isinstance(text, str):
            continue  # skip invalid entries

        # 타겟 페이지 번호 필터링
        if target_pages is not None:
            if page not in target_pages:
                continue

        elif max_page_number is not None:
            if page > max_page_number:
                continue  # skip pages beyond the limit

        if allowed_types is not None and block_type not in allowed_types:
            continue  # skip types not in the allowed list

        filtered_text_blocks.append(text)

    combined_text = "\n".join(filtered_text_blocks)

    # ✅ 터미널 출력 (지정된 길이까지만 미리보기)
    if DEBUG:
        print("-" * 80)
        print("\n📄📄 [FILTERED EXTRACTED TEXT] 📄📄\n")
        preview = combined_text[:max_preview_length]
        print(
            preview
            + ("\n... (truncated)" if len(combined_text) > max_preview_length else "")
        )
        print("-" * 80)

    # print(f"✅ Found {len(filtered_text_blocks)} text blocks from pages ≤ {max_page_number}")
    # print(f"✅ Types available in data: {all_types}")

    return combined_text, all_types


# [STEP 4] PROMPT의 각 field 읽고, description에 따라 작업 수행 정의
def process_file(file_path, prompts, llm):
    with open(file_path, "r", encoding="utf-8") as f:
        json_data = json.load(f)

    combined_text, all_types = extract_text_from_json_blocks(
        json_data,
        allowed_types=ALLOWED_TYPES,
        target_pages=TARGET_PAGES,
        max_page_number=MAX_PAGE_NUMBER,
    )
    result = {}

    # ✅ 한 글자라도 텍스트 없으면 NO_TEXT 처리
    if combined_text.strip() == "":
        for field in prompts.keys():
            result[field] = "NO_TEXT"
            result[f"RAW_{field}"] = "NO_TEXT"
        return result

    for field, field_info in prompts.items():
        instruction = field_info.get("description", "")
        # if DEBUG: print(f"[INFO] Extracting '{field}'...")

        res = llm.send_request(field, instruction, combined_text)
        parsed = res["parsed"]
        # raw = res["raw"]
        # status = "success" if parsed != "ERROR" else "error"

        result[field] = parsed
        # result[f"RAW_{field}"] = raw

    return result


# def parsing_json(json_data):
#     c_df = pd.DataFrame(list(json_data.items()), columns=['Key', 'Value'])
#     authors = json_data["AUTHOR_LIST"].split("; ")
#     affiliations = json_data["AUTHOR_AFFILIATION"]["AFFILIATION"]
#     print("authors:\n",authors)
#     print("affiliations:\n",affiliations)
#     # 저자와 소속을 매칭 (저자 수만큼만)
#     structured_data = []
#     for i, author in enumerate(authors):
#         structured_data.append({
#             'Title': json_data["TITLE"],
#             'Author': author,
#             'Affiliation': affiliations[i] if i < len(affiliations) else 'N/A'
#         })

#     a_df = pd.DataFrame(structured_data)
#     return a_df, c_df


def parsing_json(json_data):
    # [STEP 1] C_DATA 구성
    DESIRED_KEYS = [
        "TITLE",
        "AUTHOR_LIST",
        "AFFILIATION_LIST",
        "FIRST_AUTHOR",
        "CORRESPONDING_AUTHOR",
        "KEYWORDS",
        "DATE_METADATA",
        "BIBLIOGRAPHY_INFORMATION",
        "JOURNAL_NAME",
        "PUBLICATION_YEAR",
        "VOLUME",
        "ISSUE",
        "PAGE",
        "DOI",
    ]

    filtered_data = {k: json_data.get(k, "") for k in DESIRED_KEYS}
    filtered_data["JSON_FILE_NAME"] = "json_input"  # 또는 외부에서 전달받을 수 있음

    # CO_AUTHOR 처리
    all_authors = set(
        name.strip()
        for name in json_data.get("AUTHOR_LIST", "").split(";")
        if name.strip()
    )
    first_authors = set(
        name.strip()
        for name in json_data.get("FIRST_AUTHOR", "").split(";")
        if name.strip()
    )
    corresponding_authors = set(
        name.strip()
        for name in json_data.get("CORRESPONDING_AUTHOR", "").split(";")
        if name.strip()
    )
    co_authors = all_authors - first_authors - corresponding_authors
    filtered_data["CO_AUTHOR"] = "; ".join(sorted(co_authors))

    C_DATA = pd.DataFrame([filtered_data])

    # [STEP 2] AUTHOR_ROLE 생성
    ROLE_PRIORITY = {"FIRST_AUTHOR": 1, "CORRESPONDING_AUTHOR": 2, "CO_AUTHOR": 3}
    AUTHOR_ROLE_MAP = {}

    def add_roles(names_str, role, remove_co=False):
        for name in (n.strip() for n in names_str.split(";") if n.strip()):
            AUTHOR_ROLE_MAP.setdefault(name, set())
            if remove_co:
                AUTHOR_ROLE_MAP[name].discard("CO_AUTHOR")
            AUTHOR_ROLE_MAP[name].add(role)

    add_roles(json_data.get("AUTHOR_LIST", ""), "CO_AUTHOR")
    add_roles(json_data.get("FIRST_AUTHOR", ""), "FIRST_AUTHOR", remove_co=True)
    add_roles(
        json_data.get("CORRESPONDING_AUTHOR", ""),
        "CORRESPONDING_AUTHOR",
        remove_co=True,
    )

    AUTHOR_ROLE_DATA = pd.DataFrame(
        [
            {
                "JSON_FILE_NAME": "json_input",
                "AUTHOR": name,
                "ROLE": "; ".join(
                    sorted(roles, key=lambda r: ROLE_PRIORITY.get(r, 99))
                ),
            }
            for name, roles in AUTHOR_ROLE_MAP.items()
        ]
    )

    # [STEP 3] AUTHOR_AFFILIATION
    AUTHOR_AFFILIATIONS = []
    for entry in json_data.get("AUTHOR_AFFILIATION", []):
        author = entry.get("AUTHOR", "").strip()
        aff_text = entry.get("AFFILIATION", "").strip()
        if aff_text:
            for aff in [a.strip() for a in aff_text.split(";") if a.strip()]:
                AUTHOR_AFFILIATIONS.append(
                    {
                        "JSON_FILE_NAME": "json_input",
                        "AUTHOR": author,
                        "AFFILIATION": aff,
                    }
                )

    AUTHOR_AFFILIATION_DATA = pd.DataFrame(AUTHOR_AFFILIATIONS)

    # [STEP 4] A_DATA 병합
    A_DATA = pd.merge(
        AUTHOR_AFFILIATION_DATA,
        AUTHOR_ROLE_DATA,
        on=["JSON_FILE_NAME", "AUTHOR"],
        how="outer",
    )
    # print("AUTHOR_AFFILIATION_DATA:\n",AUTHOR_AFFILIATION_DATA)
    # print("AUTHOR_ROLE_DATA:\n", AUTHOR_ROLE_DATA)
    cdf = C_DATA.T.reset_index()
    cdf.columns = ["Key", "Value"]
    # dict, list 등 복잡한 객체를 문자열로 변환
    cdf["Value"] = cdf["Value"].apply(
        lambda x: (
            json.dumps(x, ensure_ascii=False) if isinstance(x, (dict, list)) else x
        )
    )

    return A_DATA, cdf


def count_no_text(json_data):
    cnt_total = len(json_data)
    no_cnt = sum(1 for v in json_data.values() if v == "NO_TEXT")
    return cnt_total, no_cnt


def get_paper_df(filename):
    prompts = load_prompts(PROMPT_PATH)

    # ✅ 모델 선택
    if "gpt" in MODEL_NAME:
        print("gpt")
        llm = GPTApi(model_name=MODEL_NAME, api_key=OPENAI_API_KEY)
    else:
        print("local")
        llm = LocalApi(model_name=MODEL_NAME, base_url=LLAMA_URL)

    # if DEBUG: print(f"\n[📄] Processing {filename} ...")

    json_data = process_file(filename, prompts, llm)
    # print("=====json_data:\n", json_data)
    cnt_total, no_cnt = count_no_text(json_data)
    print(f"전체 항목 수: {cnt_total}, 'NO_TEXT'인 항목 수: {no_cnt}")
    if no_cnt > 5:
        return None, None, no_cnt
    a_result, c_result = parsing_json(json_data)
    # print(c_result)
    # print(a_result)
    return json_data, a_result, c_result, no_cnt, MODEL_NAME
