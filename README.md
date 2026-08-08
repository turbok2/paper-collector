# paper-collector 논문수집기
paper-collector (논문수집기)

(260703) 1.0.10 ISSN, IF 추출 추가 및 NO 가 있으면 로그 남기기
1) DB 스키마 추가
   - c_info 테이블에 issn_print / issn_electronic 컬럼 추가 
   - c_info 테이블에 is_scie, is_scopus, is_kci, impact 컬럼 추가 
   - pdf 처리시 ISSN, IF 도 처리하기
   - ISSN 일괄등록
   - IF 연도별 일괄등록
2) PDF 등록시 NO 가 있으면 로그 남기기
   - pdf  읽어서 파싱하고, LLM에 문의 결과에 "NO_TEXT", "ERROR", NO로 시작하는 게 있으면 해당컬럼과 값을 로그파일에 저장
3) 논문검색 에서 검색조건으로 파일이름  추가
4) '참여','저자구분' 컬럼에 보여주기 & 검색기능 추가
   - 발행년도,부서명, 저널명 : 다중 선택

(260607) 1.0.9 논문 확정 기능 및 활동 로그 추가, 삭제 처리 버그 수정
1) DB 스키마 추가
   - a_info 테이블에 CONFIRM_STATUS / CONFIRM_DT / CONFIRM_ID 컬럼 추가 (UNCONFIRMED / USER_CLAIMED / ADMIN_CONFIRMED)
   - activity_log 테이블 신규 생성 (ACTION_DT, ACTION_TYPE, ACTOR_ID, TARGET_TABLE, TARGET_KEY, OLD_VALUE, NEW_VALUE, MEMO)
   - 기존 직원번호가 있는 a_info 행 → USER_CLAIMED 일괄 마이그레이션
2) 논문 확정 기능
   - 사용자 업로드: 저자 선택 시 USER_CLAIMED 상태 자동 설정
   - 관리자 업로드: 선택한 영문이름으로 직원 조회 후 ADMIN_CONFIRMED 설정, 미조회 시 경고
   - 나의논문 목록에 확정상태 컬럼 표시 (사용자확정 / 관리자확정 / 미확정)
   - 나의논문 편집 모드에 [확정취소] 버튼 추가 (직원번호 해제, 미확정 전환)
   - 관리자 접수처리 저장 시 ADMIN_CONFIRMED 자동 적용
   - 관리자 접수처리 뷰 모드에 저자별 [확정] / [확정 해제] 버튼 추가
   - 내정보 페이지: 확정상태 뱃지 표시, ADMIN_CONFIRMED 행 잠금, [지정 해제] 버튼 추가
3) 활동 로그 기능
   - 업로드(UPLOAD), 서지정보 편집(EDIT_C_INFO), 사용자 지정(USER_CLAIM/UNCLAIM), 관리자 확정(ADMIN_CONFIRM/UNCONFIRM), 삭제 승인(DELETE_APPROVE) 이벤트 기록
   - 설정 페이지 관리자 전용 [활동 로그] 탭 추가 (액션 유형/수행자/PDF명/날짜 필터, 변경 전/후 값 상세 보기)
4) 버그 수정
   - 삭제 승인: with 컨텍스트 매니저로 자동 commit 보장, c_info/a_info 삭제 추가, 파일 삭제는 DB commit 후 실행
   - 접수처리 [선택된 항목 삭제]: DELETE FROM u_info → UPDATE DONE=1 로 변경 (처리완료 목록 유지), c_info/a_info 삭제 추가
   - 나의논문/전체논문 삭제 신청: ORI_FILE_NAME 미전달 문제 수정 (get_my_papers 컬럼 추가 + DB 직접 조회 보강)

(260606) pdf 파서 선택 순서 지정
1) 기본으로 병원내 파서 이용, 그 다음에 외부 파서 이용으로 순서 지정


(260118-01) add database audit columns (REG_DT/ID, MOD_DT/ID) and update data handling logic to track creation and modification history
1) a_ino, c_info, user_info 에 REG_DT REG_ID MOD_DT MOD_ID 컬럼이 없으면 추가
2) REG_DT REG_ID 컬럼이 비어 있으면 현재날짜, AD00000 으로 채우기
3) 추가된 컬럼에 맞게 신규입력시  REG_DT REG_ID 컬럼을 입력한 시간과 입력한 ID로 채우기
4) 추가된 컬럼에 맞게 수정시  MOD_DT MOD_ID 컬럼을 수정한 시간과 수정한 ID로 채우기
맨 마지막에 커밋용 제목을 한 줄로 작성해줘.

(260121-01) 내 논문으로 지정, 주요연구키워드, 최근7년 비중 개선
1) 내 논문으로 지정 버튼 누르면 직원번호만 채워지는데 이름도 채워지게
2) 주요연구키워드-불용어 추가, 표현 방식 개선
3) 최근7년 비중 -파이챠트 : 연도 순으로 표시

(260126-01) 내정보 페이지 진입 시 논문 실적 기반 영어 이름 자동 동기화 및 UI 개선
1) 2522 라인에서  hname1 에 값이 있으면 영어이름이 파악된 걸로 간주하고 [불러오기]를 
없으면 [변환]버튼으로 가게 되는데.  
2522 라인 앞부분에 
a_info 에  사용자 ID로 '직원번호' 컬럼을 필터링해서,  'AUTHOR'컬럼값의 유니크한 리스트를 구하고,
user_info의 hname1, hname2, hname3, hname4 에 차례로 기록하는 코드 작성.
그런데, 이미 hname1, hname2, hname3, hname4에 값이 있다면 거기에 없는 값만 기록하도록.
2) [불러오기] 버튼이 보이게 되면, 사용자가 안 눌러도 기능이 작동해서 영어이름 불러오게 수정
  내정보 메뉴로 들어갈 때 1번만 작동하게
3) 영어이름관리에 [삭제] 누르면 입력창에 값이 바로 삭제되기

(260215-01) 1.0.1  전체논문(관리자) 메뉴에서 논문정보편집/삭제 개선
1) 전체논문(관리자) 메뉴에서 논문정보편집/삭제 에서 불필요한 컬럼 안 보이게
2) 전체논문(관리자) 메뉴에서 논문정보편집/삭제 에서 편집가능하게, 저장

(260410-01) 1.0.2  PDF 교체, 삭제
1) PDF 교체 신청시, ADMIN에서 기존 DB삭제 후 신규 내용 입력
2) 잘못된 건 삭제 기능

(260411-01) 1.0.3  PDF 교체, 삭제
1) 사용자가 pdf 업로드시 pdf가 달라도 TITLE 이 같은 경우 : PDF파일 변경 신청 기능 추가
2) 함수화 : PDF 뷰어, PDF파일 변경, uploaded, resolved 폴더 내 관련 파일을 삭제

(260412-01) 1.0.4  uploaded 폴더에 동일 hash 포함한 파일 있으면 지우는 기능
1) uploaded 폴더에 동일 hash 포함한 파일 있으면 지우는 기능:관리자
2) uploaded 폴더에 저장시 동일 hash 포함한 파일 있으면 지우는 기능 추가

(260412-02) 1.0.5 초록 전부 업데이트
1) c_info에서 논문에 대해 초록 업데이트

(260414-01) 1.0.6 PDF 파일변경 신청
1) 사용자 : PDF 파일변경 신청 - 기존 정보 이용하기
2) 관리자 : 파일변경 신청 기능 추가
3) 관리자,사용자 : 삭제신청 기능
4) 사용자 : 편집 기능, 인명검색 기능

(260415-01) 1.0.7 관리기능 추가
1) 관리자 : 설정 - 중복논문검사, 폴더별 파일 무결성검사 기능 추가
2) 전체논문 - 편집 - 인명검색 추가, 소속에 chonnam  있으면 해당 셀 강조, CSV 다운로드 