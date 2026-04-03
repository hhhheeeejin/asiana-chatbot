import streamlit as st
import pandas as pd
import os
import requests
import json

# 1. 설정 (API 키)
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    API_KEY = "AIzaSyDowXmHrD3-NeWM90ZnROo3RX3F269gZGc"

APPLICANT_FILE = "applicants.xlsx"

# 2. AI 상담 함수
def ask_gemini_direct(prompt):
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key={API_KEY}"
    headers = {'Content-Type': 'application/json'}
    job_info = """
[채용 공고 내용]- 회사명: 아시아나 에어포트(인천공항)

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
    data = {"contents": [{"parts": [{"text": f"친절한 채용 담당자로서 답해줘: {prompt}\n정보: {job_info}"}]}]}
    try:
        res = requests.post(url, headers=headers, data=json.dumps(data), timeout=10)
        return res.json()['candidates'][0]['content']['parts'][0]['text']
    except: return "잠시 후 다시 질문해주세요."

# 3. 지원서 저장 함수 (추가된 항목 반영)
def save_application(data_dict):
    try:
        new_row = pd.DataFrame([data_dict])
        if os.path.exists(APPLICANT_FILE):
            df_old = pd.read_excel(APPLICANT_FILE)
            if str(data_dict["연락처"]) in df_old['연락처'].astype(str).values:
                return "duplicate"
            df_final = pd.concat([df_old, new_row], ignore_index=True)
        else: df_final = new_row
        df_final.to_excel(APPLICANT_FILE, index=False)
        return "success"
    except: return "error"

# 4. 지원서 UI 함수 (소요시간, 도착가능여부 추가)
def apply_form_ui(id_suffix):
    st.subheader("📝 1분 간편 지원서")
    with st.form(key=f"apply_form_{id_suffix}", clear_on_submit=True):
        name = st.text_input("이름", key=f"name_{id_suffix}")
        gender = st.radio("성별", ["남성", "여성"], horizontal=True, key=f"gender_{id_suffix}")
        age = st.number_input("나이", 19, 70, 25, key=f"age_{id_suffix}")
        phone = st.text_input("연락처 (숫자만)", key=f"phone_{id_suffix}")
        address = st.text_input("주소 (OO동)", key=f"addr_{id_suffix}")
        
        st.divider()
        # [신규 추가 항목]
        transport = st.selectbox("교통방법", ["셔틀버스", "대중교통", "자차"], key=f"trans_{id_suffix}")
        travel_time = st.text_input("소요시간 (예: 40분)", key=f"time_{id_suffix}")
        can_arrive = st.radio("05:20까지 도착 가능여부", ["가능", "불가능"], horizontal=True, key=f"arrive_{id_suffix}")
        
        submitted = st.form_submit_button("지원서 최종 제출")
        if submitted:
            if name and phone:
                app_data = {
                    "신청시간": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"), 
                    "이름": name, "성별": gender, "나이": age, "연락처": phone, 
                    "주소": address, "교통방법": transport, 
                    "소요시간": travel_time, "새벽도착가능": can_arrive # 데이터 저장
                }
                res = save_application(app_data)
                if res == "success": st.balloons(); st.success("접수 완료!")
                elif res == "duplicate": st.warning("이미 지원된 번호입니다.")
            else: st.error("이름과 연락처를 입력해주세요.")

# --- 화면 구성 ---
st.set_page_config(page_title="아시아나 에어포트 채용", layout="wide")
st.title("✈️ 아시아나 에어포트 채용 통합 시스템")

# [사이드바]
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/0/00/Asiana_Airports_logo.svg/1200px-Asiana_Airports_logo.svg.png", width=150)
    apply_form_ui("sidebar")

# [메인 탭]
tab1, tab2, tab3 = st.tabs(["💬 AI 상담원", "📝 간편 지원", "📊 관리자 분석"])

with tab1:
    if "messages" not in st.session_state: st.session_state.messages = []
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
    if prompt := st.chat_input("채용에 대해 물어보세요!"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            ans = ask_gemini_direct(prompt)
            st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})

with tab2:
    apply_form_ui("main")

with tab3:
    st.subheader("📈 실시간 지원 현황")
    if os.path.exists(APPLICANT_FILE):
        df_admin = pd.read_excel(APPLICANT_FILE)
        c1, c2, c3 = st.columns(3)
        c1.metric("총 지원자", f"{len(df_admin)}명")
        c2.metric("평균 연령", f"{round(df_admin['나이'].mean(), 1)}세")
        # 새벽 출근 가능자 비율 계산
        if "새벽도착가능" in df_admin.columns:
            possible_count = len(df_admin[df_admin["새벽도착가능"] == "가능"])
            c3.metric("새벽출근 가능자", f"{possible_count}명")
            
        st.dataframe(df_admin, use_container_width=True)
        with open(APPLICANT_FILE, "rb") as f:
            st.download_button("📥 엑셀 다운로드", f, file_name="applicants.xlsx")
    else: st.info("데이터가 아직 없습니다.")
