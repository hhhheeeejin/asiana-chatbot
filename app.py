import streamlit as st
import pandas as pd
import os
import requests
import json

# 1. 설정 (희희진님의 API 키)
API_KEY = st.secrets["GEMINI_API_KEY"]
APPLICANT_FILE = "applicants.xlsx"
QUESTION_LOG_FILE = "questions_log.xlsx"

# 2. 채용 공고 정보
job_info = """
[아시아나 에어포트 채용 정보]
- 회사명: 아시아나 에어포트(인천공항)
– 하는 업무: 아시아나 항공기 기내청소, 정리정돈, 시트, 벽면, 주방 등 청소업무, 항공기 출발 전후 정비
- 근무시간: 오전 05:45~14:45, 오후 14:00~23:00 스케줄 근무 / 3일 근무 1일 휴무 반복
- 근무지: 인천국제공항, 셔틀버스 지원(발산역, 부천 원종사거리, 고강동 지원)
- 급여: 기본급+식대지원비+교통지원비+기타수당 포함 월 평균 289만원 이상 *기타수당: 시간외 근무 + 야간근무 수당 등 발생 시 지급, 평균 10~30만원 
- 복리후생: 식비지급, 교통비 일 1,2000원 지원(새벽근무 시 1만원 추가지급, 셔틀 이용 시 셔틀비용 차감하여 지급), 유니폼 지급, 셔틀버스 지원, 1년 이상 근무 시 아시아나 항공권 지급(15만원)
- 지원 방법: 왼쪽 '간편 지원서 작성' 양식을 이용해 주세요.
- 면접 일정: 서류 합격자에 한해 개별 연락 드립니다. 
- 기타: 초보자 가능(교육 진행), 팀 단위 업무(소형기 10~13명 등), 소형기 청소 약 30분 소요
- 셔틀 시간: 발산 및 김포공항 04:30, 부천 원종사거리 04:30
- 주차: 야외 주차장 이용 가능, 월 3만원 별도 비용 발생 
"""

# 3. AI 상담 함수 (안정적인 v1 주소 사용)
def ask_gemini_direct(prompt):
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key={API_KEY}"
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{
            "parts": [{"text": f"너는 아시아나 에어포트 채용 담당자야. 다음 정보를 바탕으로 답해줘.\n정보: {job_info}\n질문: {prompt}"}]
        }]
    }
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data), timeout=10)
        result = response.json()
        if 'candidates' in result:
            return result['candidates'][0]['content']['parts'][0]['text']
        return "죄송합니다. 답변을 생성할 수 없습니다."
    except:
        return "AI 연결에 일시적인 오류가 있습니다. 잠시 후 다시 시도해주세요."

# --- 화면 구성 ---
st.set_page_config(page_title="아시아나 에어포트 채용", layout="wide")

# [지원서 저장 함수 - 에러 해결 핵심]
def save_application(data_dict):
    try:
        # 데이터프레임 생성 (에러가 나던 암호화 과정 생략)
        new_row = pd.DataFrame([data_dict])
        
        if os.path.exists(APPLICANT_FILE):
            df_old = pd.read_excel(APPLICANT_FILE)
            # 연락처 중복 체크
            if str(data_dict["연락처"]) in df_old['연락처'].astype(str).values:
                return "duplicate"
            df_final = pd.concat([df_old, new_row], ignore_index=True)
        else:
            df_final = new_row
            
        df_final.to_excel(APPLICANT_FILE, index=False)
        return "success"
    except Exception as e:
        st.error(f"엑셀 저장 중 오류 발생: {e}")
        return "error"

# --- 메인 레이아웃 ---
st.title("✈️ 아시아나 에어포트 채용 시스템")

# [사이드바 지원서]
with st.sidebar:
    st.subheader("📝 모바일 간편 지원")
    with st.form("apply_form", clear_on_submit=True):
        name = st.text_input("이름")
        gender = st.radio("성별", ["남성", "여성"], horizontal=True)
        age = st.number_input("나이", min_value=19, max_value=70, value=25)
        phone = st.text_input("연락처 (숫자만)")
        address = st.text_input("주소 (OO동까지)")
        transport = st.selectbox("출퇴근 교통방법", ["셔틀버스", "대중교통", "자차"])
        
        submitted = st.form_submit_button("지원서 최종 제출")
        if submitted:
            if name and phone:
                app_data = {
                    "신청시간": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "이름": name, "성별": gender, "나이": age, 
                    "연락처": phone, "주소": address, "교통방법": transport
                }
                result = save_application(app_data)
                if result == "success":
                    st.balloons()
                    st.success(f"{name}님, 지원이 완료되었습니다!")
                elif result == "duplicate":
                    st.warning("이미 지원된 연락처입니다.")
            else:
                st.error("이름과 연락처는 필수입니다.")

# [AI 상담 탭]
tab1, = st.tabs(["💬 AI 상담원"])
with tab1:
    if "messages" not in st.session_state: st.session_state.messages = []
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    if prompt := st.chat_input("채용에 대해 궁금한 점을 물어보세요!"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            answer = ask_gemini_direct(prompt)
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
