import requests # requests 라이브러리 임포트
import json # json 라이브러리 임포트
import os
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
    error=''
    try:
        with open(pdf_path, 'rb') as f:
            files = {'file': (os.path.basename(pdf_path), f, 'application/pdf')}
            # st.info(f"PDF 분석 서비스 ({service_url})로 파일을 전송 중입니다. 잠시 기다려 주세요...")
            response = requests.post(service_url, files=files, timeout=request_timeout)

        response.raise_for_status() # HTTP 오류가 발생하면 예외를 발생시킵니다.
        return response.json(),error
    except requests.exceptions.Timeout:
        error =f"요청 시간 초과: PDF 분석 서비스가 {request_timeout}초 내에 응답하지 않았습니다."
        return None,error
    except requests.exceptions.ConnectionError:
        error="연결 오류: PDF 분석 서비스에 연결할 수 없습니다. 서비스 URL을 확인하거나 네트워크 상태를 확인해주세요."
        return None,error
    except requests.exceptions.RequestException as e:
        error=f"PDF 분석 요청 중 오류 발생: {e}"
        return None,error
    except json.JSONDecodeError:
        error="서비스에서 유효한 JSON 응답을 받지 못했습니다."
        return None,error
    except Exception as e:
        error=f"예상치 못한 오류 발생: {e}"
        return None,error