import streamlit as st
import pandas as pd
import google.generativeai as genai
import os
import datetime
import matplotlib.pyplot as plt

# --- 1. 구글 제미나이 설정 ---
# 관리를 위해 Secrets에서 키를 가져오도록 설정합니다.
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error("API 키 설정에 문제가 있습니다. Secrets 설정을 확인해주세요.")

DATA_FILE = "applicant_data.csv"

# --- 2. 채용 정보 지식 베이스 ---
COMPANY_KNOWLEDGE = """
[아시아나 에어포트(인천공항) 채용 상세 정보]
- 업무: 아시아나 항공기 기내청소, 정리정돈, 시트/벽면/주방 청소, 항공기 출발 전후 정비.
- 특징: 초보자 가능(교육 진행), 팀 단위 업무(소형기 10~13명 투입, 약 30분 소요).
- 근무시간: 오전(05:45~14:45), 오후(14:00~23:00) 스케줄 근무 / 3일 근무 1일 휴무 반복.
- 급여: 월 평균 297만원 이상(기본급+식대+교통비+기타수당 포함). 시간외/야간수당 발생 시 추가 지급(평균 10~30만원).
- 복리후생: 식비지급, 교통비 일 12,000원(새벽근무 시 1만원 추가), 유니폼 지급, 셔틀버스 지원, 1년 이상 근무시 아시아나 항공권 지급 (약 15만원 상당)
- 셔틀노선: 발산역, 김포공항, 부천 원종사거리, 고강동 지원.
- 셔틀시간: 발산 및 김포공항 04:30, 부천 원종사거리 04:30 출발.
- 야외주차장 이용가능, 월비용 약 3만원 가량 별도 발생
"""

# --- 3. 기본 기능 함수 ---
def save_application(name, phone, arrival_ok):
    """지원자 정보 저장 및 중복 체크"""
    phone = phone.replace("-", "").strip()
    if os.path.exists(DATA_FILE):
        df_existing = pd.read_csv(DATA_FILE)
        if str(phone) in df_existing['연락처'].astype(str).values:
            return "duplicate"
            
    new_data = {
        "신청시간": [datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        "이름": [name], "연락처": [phone], "05:20도착가능": [arrival_ok]
    }
    df_new = pd.DataFrame(new_data)
    df_new.to_csv(DATA_FILE, mode='a', header=not os.path.exists(DATA_FILE), index=False, encoding='utf-8-sig')
    return "success"

# --- 4. 화면 레이아웃 ---
st.set_page_config(page_title="아시아나 에어포트 채용비서", layout="wide")
st.title("✈️ 아시아나 에어포트 채용 통합 시스템")

tab1, tab2, tab3 = st.tabs(["💬 AI 상담 챗봇", "📋 모바일 간편지원", "📊 관리 데이터 분석"])

# [탭 1: AI 상담]
with tab1:
    st.subheader("궁금한 점을 물어보세요!")
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input("급여는 얼마인가요?")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            # 제미나이에게 지시 및 답변 생성
            full_instruction = f"너는 다정한 채용 담당자야. 아래 정보를 바탕으로 답해줘:\n{COMPANY_KNOWLEDGE}\n\n질문: {prompt}"
            response = model.generate_content(full_instruction)
            full_response = response.text
            st.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})

# [탭 2: 모바일 지원]
with tab2:
    st.subheader("간편 지원 양식")
    with st.form("main_form", clear_on_submit=True):
        name = st.text_input("이름")
        phone = st.text_input("연락처 (숫자만 입력)")
        arrival_ok = st.radio("오전 05:20까지 공항 도착이 가능하신가요?", ["O", "X"], horizontal=True)
        
        if st.form_submit_button("지원서 최종 제출"):
            if name and phone:
                res = save_application(name, phone, arrival_ok)
                if res == "duplicate": st.error("⚠️ 이미 지원된 연락처입니다.")
                else: st.success(f"✅ {name}님, 지원이 완료되었습니다!")
            else:
                st.warning("이름과 연락처를 모두 입력해주세요.")

# [탭 3: 관리자 분석]
with tab3:
    st.subheader("📈 실시간 데이터 분석")
    password = st.text_input("관리자 비밀번호", type="password")
    if password == "heejin1234": # 비밀번호 설정
        if os.path.exists(DATA_FILE):
            df = pd.read_csv(DATA_FILE)
            st.write(f"총 지원자: {len(df)}명")
            st.dataframe(df)
            
            # 간단한 그래프 예시
            if st.button("차트 업데이트"):
                fig, ax = plt.subplots()
                df['05:20도착가능'].value_counts().plot.pie(autopct='%1.1f%%', ax=ax)
                st.pyplot(fig)
        else:
            st.info("아직 지원 데이터가 없습니다.")
