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
