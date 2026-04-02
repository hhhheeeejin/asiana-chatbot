import streamlit as st
import pandas as pd
import openai
import os
import datetime
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from collections import Counter
import re

# --- 1. 초기 설정 및 페이지 구성 ---
st.set_page_config(page_title="아시아나 에어포트 채용 비서", layout="wide")

# [보안 주의] 실제 운영 시 본인의 OpenAI API 키를 입력하세요.
client = openai.OpenAI(api_key=st.secrets["AIzaSyDowXmHrD3-NeWM90ZnROo3RX3F269gZGc"])
DATA_FILE = "applicant_data.csv"

# 한글 폰트 설정 (Windows 기준: Malgun Gothic)
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# --- 2. 학습용 채용 공고 지식 베이스 ---
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

# --- 3. 핵심 기능 함수 ---

def save_application(name, gender, age, phone, transport, duration, arrival_ok):
    """지원자 정보 저장 및 중복 체크 (연락처 기준)"""
    phone = phone.replace("-", "").strip()
    
    if os.path.exists(DATA_FILE):
        df_existing = pd.read_csv(DATA_FILE)
        if str(phone) in df_existing['연락처'].astype(str).values:
            return "duplicate"
            
    new_data = {
        "신청시간": [datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        "이름": [name], "성별": [gender], "나이": [age], "연락처": [phone],
        "교통방법": [transport], "소요시간": [duration], "05:20도착가능": [arrival_ok]
    }
    df_new = pd.DataFrame(new_data)
    df_new.to_csv(DATA_FILE, mode='a', header=not os.path.exists(DATA_FILE), index=False, encoding='utf-8-sig')
    return "success"

def render_apply_form(form_key):
    """간편 지원 양식 렌더링 함수 (재사용 가능)"""
    with st.form(key=form_key, clear_on_submit=True):
        st.write("📋 **기본 정보**")
        c1, c2 = st.columns(2)
        with c1: name = st.text_input("이름")
        with c2: gender = st.radio("성별", ["남성", "여성"], horizontal=True)
        
        c3, c4 = st.columns(2)
        with c3: age = st.number_input("나이", min_value=19, max_value=70, value=30)
        with c4: phone = st.text_input("연락처", placeholder="01012345678")
        
        st.write("🚗 **출퇴근 및 근무 확인**")
        transport = st.selectbox("출퇴근 교통방법", ["셔틀버스", "대중교통", "자차"])
        duration = st.text_input("출퇴근 소요시간 (예: 40분)")
        arrival_ok = st.radio("오전 05:20까지 공항 도착이 가능하신가요?", ["O", "X"], horizontal=True)
        
        if st.form_submit_button("지원서 최종 제출"):
            if name and phone and duration:
                res = save_application(name, gender, age, phone, transport, duration, arrival_ok)
                if res == "duplicate": st.error("⚠️ 이미 지원된 연락처입니다.")
                else: st.success(f"✅ {name}님, 지원이 정상적으로 완료되었습니다!")
            else: st.warning("모든 항목을 입력해주세요.")

# --- 4. 메인 레이아웃 구성 ---

# 사이드바 (PC용)
with st.sidebar:
    st.header("📝 빠른 간편 지원")
    render_apply_form("sidebar_form")

# 메인 화면 탭
st.title("✈️ 아시아나 에어포트 채용 통합 시스템")
tab1, tab2, tab3 = st.tabs(["💬 AI 상담 챗봇", "📋 모바일 간편지원", "📊 관리 데이터 분석"])

# [탭 1: AI 상담]
with tab1:
    st.subheader("궁금한 점을 물어보세요!")
    # FAQ 버튼
    cols = st.columns(4)
    faq_list = ["💰 급여안내", "🚌 셔틀시간", "🎁 복리후생", "🏠 소요시간"]
    selected_faq = ""
    for i, faq in enumerate(faq_list):
        if cols[i].button(faq): selected_faq = faq

    if "messages" not in st.session_state: st.session_state.messages = []
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    prompt = st.chat_input("질문을 입력하세요...")
    if selected_faq: prompt = f"{selected_faq}에 대해 자세히 알려줘."

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            # 진짜 AI에게 물어보는 과정입니다.
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system", 
                        "content": f"너는 아시아나 에어포트의 다정한 채용 담당자야. 아래 [채용 정보]를 바탕으로 친절하게 답변해줘. \n\n[채용 정보]:\n{COMPANY_KNOWLEDGE}"
                    }
                ] + st.session_state.messages
            )
            # AI가 생성한 진짜 답변 내용을 가져옵니다.
            full_response = response.choices[0].message.content
            st.markdown(full_response)

# [탭 2: 모바일 지원]
with tab2:
    st.subheader("모바일 지원 양식")
    render_apply_form("main_form")

# [탭 3: 관리자 분석]
with tab3:
    st.subheader("📈 실시간 채용 데이터 분석")
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        st.write(f"현재 총 지원자 수: **{len(df)}명**")
        
        c1, c2 = st.columns(2)
        with c1: 
            st.write("📅 최근 지원 현황")
            st.dataframe(df.tail())
        with c2:
            if st.button("📊 통계 그래프 업데이트"):
                fig, ax = plt.subplots(1, 2, figsize=(12, 5))
                # 05:20 도착 가능 여부 비율
                df['05:20도착가능'].value_counts().plot.pie(ax=ax[0], autopct='%1.1f%%', startangle=90)
                ax[0].set_title("05:20 도착 가능 비율")
                # 교통방법 빈도
                df['교통방법'].value_counts().plot.bar(ax=ax[1], color='skyblue')
                ax[1].set_title("주요 교통수단")
                st.pyplot(fig)
    else: st.info("아직 수집된 지원 데이터가 없습니다.")