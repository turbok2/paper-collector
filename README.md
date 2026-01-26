# paper-collector 논문수집기
paper-collector (논문수집기)

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
