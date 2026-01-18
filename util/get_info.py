import os
import requests
import json
import time
from tqdm import tqdm  # tqdm 라이브러리 임포트

# 설정
PDF_DIR = "data"  # PDF 파일이 있는 폴더
RESULT_DIR = "result"  # 결과를 저장할 폴더
SERVICE_URL = "http://1.227.21.165:5060"  # pdf-document-layout-analysis 서비스 URL
REQUEST_TIMEOUT = 600  # 각 요청의 타임아웃 (초) - 10분 설정


def format_seconds(seconds):
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    result = f"{hours}시간 {minutes}분 {secs}초"
    return result

def get_pdf_json(pdf_path,SERVICE_URL,REQUEST_TIMEOUT):
    # 1. JSON 분석 결과 요청 및 저장
    err_code=''
    pdf_file = os.path.basename(pdf_path)
    try:
        with open(pdf_path, "rb") as f:
            files = {"file": (pdf_file, f, "application/pdf")} # 파일 이름과 파일 경로 전달
            response = requests.post(
                SERVICE_URL, files=files, timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()  # HTTP 오류 발생 시 예외 발생

        json_data = response.json()

    except requests.exceptions.RequestException as e:
        err_code = f"  오류: '{pdf_file}' JSON 분석 중 오류 발생: {e}"
        # print(f"  오류: '{pdf_file}' JSON 분석 중 오류 발생: {e}")
    except json.JSONDecodeError:
        err_code = f"  오류: '{pdf_file}' JSON 응답 디코딩 실패. 유효한 JSON이 아닐 수 있습니다."
        # print(f"  오류: '{pdf_file}' JSON 응답 디코딩 실패. 유효한 JSON이 아닐 수 있습니다.")
    except Exception as e:
        err_code = f"  오류: '{pdf_file}' JSON 처리 중 예기치 않은 오류 발생: {e}"
        # print(f"  오류: '{pdf_file}' JSON 처리 중 예기치 않은 오류 발생: {e}")
    return json_data, err_code
        
def get_pdf_vpdf(pdf_path, vis_output_path,SERVICE_URL,REQUEST_TIMEOUT):
    # 2. 시각화된 PDF 출력 요청 및 저장
    err_code=''
    visualize_url = f"{SERVICE_URL}/visualize"
    pdf_file = os.path.basename(pdf_path)
    try:
        with open(pdf_path, "rb") as f:
            files = {"file": (pdf_file, f, "application/pdf")}
            response = requests.post(
                visualize_url, files=files, timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()  # HTTP 오류 발생 시 예외 발생

        with open(vis_output_path, "wb") as f:
            f.write(response.content)
        # print(f"  시각화된 PDF 저장: '{vis_output_path}'") # tqdm 사용 시 너무 많은 출력 방지
        # print(f"  '{pdf_file}' 시각화된 PDF 저장 완료.")  # tqdm과 함께 출력

    except requests.exceptions.RequestException as e:
        err_code = f"  오류: '{pdf_file}' 시각화된 PDF 생성 중 오류 발생: {e}"
        # print(f"  오류: '{pdf_file}' 시각화된 PDF 생성 중 오류 발생: {e}")
    except Exception as e:
        err_code = f"  오류: '{pdf_file}' 시각화 처리 중 예기치 않은 오류 발생: {e}"
        # print(f"  오류: '{pdf_file}' 시각화 처리 중 예기치 않은 오류 발생: {e}")
    return err_code
                    
def main():
    """
    data 폴더의 모든 PDF 파일을 처리하여 JSON 분석 결과와 시각화된 PDF를 저장합니다.
    진행률과 시간을 표시합니다.
    """
    if not os.path.exists(PDF_DIR):
        print(f"오류: '{PDF_DIR}' 폴더가 존재하지 않습니다.")
        print("PDF 파일을 이 폴더에 넣어주세요.")
        return

    if not os.path.exists(RESULT_DIR):
        os.makedirs(RESULT_DIR)
        print(f"'{RESULT_DIR}' 폴더를 생성했습니다.")

    pdf_files = [f for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf")]

    if not pdf_files:
        print(f"'{PDF_DIR}' 폴더에 PDF 파일이 없습니다. PDF 파일을 추가해주세요.")
        return

    total_files = len(pdf_files)
    print(
        f"'{PDF_DIR}' 폴더에서 {total_files}개의 PDF 파일을 찾았습니다. 처리를 시작합니다..."
    )

    start_time = time.time()  # 전체 시작 시간 기록

    # tqdm을 사용하여 진행률 바 표시
    # desc: 진행률 바 앞에 표시될 설명
    # unit: 단위
    # leave=True: 완료 후 진행률 바를 남김
    for i, pdf_file in enumerate(tqdm(pdf_files, desc="PDF 처리 중", unit="파일"), 1):

        pdf_path = os.path.join(PDF_DIR, pdf_file)
        filename_without_ext = os.path.splitext(pdf_file)[0]

        # 각 파일의 예상 시간 계산을 위한 시작 시간 기록
        file_start_time = time.time()

        # JSON 결과 경로 및 시각화 PDF 경로 정의
        json_output_path = os.path.join(RESULT_DIR, f"{filename_without_ext}.json")
        vis_output_path = os.path.join(RESULT_DIR, f"{filename_without_ext}_vis.pdf")
        pdf_json, err_code1 = get_pdf_json(pdf_path,SERVICE_URL,REQUEST_TIMEOUT)
        if err_code1:
            print(err_code1)
            continue    
        with open(json_output_path, "w", encoding="utf-8") as f:
            json.dump(pdf_json, f, indent=4, ensure_ascii=False)        
                
        err_code2 = get_pdf_vpdf(pdf_path, vis_output_path,SERVICE_URL,REQUEST_TIMEOUT)
        if err_code2:
            print(err_code2)
            continue    

    end_time = time.time()  # 전체 종료 시간 기록
    total_elapsed_time = end_time - start_time

    print("\n--- 모든 PDF 파일 처리 완료 ---")
    print(f"총 소요 시간: {total_elapsed_time:.2f} 초")
    print(f"총 소요 시간: ", format_seconds(total_elapsed_time))
    if total_files > 0:
        avg_time_per_file = total_elapsed_time / total_files
        print(f"파일 당 평균 처리 시간: {avg_time_per_file:.2f} 초")


if __name__ == "__main__":
    main()
