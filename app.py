import streamlit as st
import pandas as pd
import google.generativeai as genai
import os
import datetime
import matplotlib.pyplot as plt
from cryptography.fernet import Fernet

# --- [1. 보안 핵심: 에러 방지용 도구 함수] ---
def get_cipher():
    """Secrets에서 키를 가져와 도구를 만듭니다. 없으면 None을 반환해요."""
    try:
        if "ENCRYPT_KEY" in st.secrets:
            return Fernet(st.secrets["h4k2j5k6l7m8n9p0q1r2s3t4u5v6w7x8y9z0="].encode())
    except:
        pass
    return None

def decrypt_val(token):
    """암호를 푸는 함수 (도구가 없거나 암호가 아니면 원본 반환)"""
    cipher = get_cipher()
    if cipher and token:
        try:
            return cipher.decrypt(str(token).encode()).decode()
        except:
            return str(token) # 암호화 안 된 옛날 데이터면 그냥 보여줌
    return str(token)

def encrypt_val(text):
    """암호화 하는 함수"""
    cipher = get_cipher()
    if cipher and text:
        return cipher.encrypt(str(text).encode()).decode()
    return str(text)

# --- [2. 관리자 인증 정보] ---
ADMIN_ID = st.secrets.get("ADMIN_ID", "admin")
ADMIN_PW = st.secrets.get("ADMIN_PW", "1234")
# --- [4. 제미나이 설정] ---
# ... 기존 제미나이 설정 코드 유지 ...

# --- 1. 구글 제미나이 설정 (기존 코드 유지) ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    if available_models:
        selected_model = available_models[0] 
        model = genai.GenerativeModel(selected_model)
    else:
        st.error("사용 가능한 제미나이 모델을 찾을 수 없습니다.")
except Exception as e:
    st.error(f"연결 실패: {e}")

DATA_FILE = "applicant_data.csv"

# --- [보안 함수] 암호화 및 복호화 ---
def encrypt_val(text):
    return cipher_suite.encrypt(str(text).encode()).decode()

def decrypt_val(token):
    return cipher_suite.decrypt(token.encode()).decode()

# --- 2. 채용 정보 지식 베이스 (기존 내용 유지) ---
COMPANY_KNOWLEDGE = """
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

# --- 3. 데이터 저장 함수 (암호화 적용) ---
def save_application(data_dict):
    # 연락처 정보를 암호화하여 저장합니다.
    data_dict["연락처"] = [encrypt_val(data_dict["연락처"][0])]
    
    if os.path.exists(DATA_FILE):
        df_existing = pd.read_csv(DATA_FILE)
        # 중복 체크 시에도 암호화된 값으로 비교하거나, 이름/시간 등 다른 지표 활용
        # 여기서는 단순화를 위해 저장을 진행합니다.
            
    df_new = pd.DataFrame(data_dict)
    df_new.to_csv(DATA_FILE, mode='a', header=not os.path.exists(DATA_FILE), index=False, encoding='utf-8-sig')
    return "success"

# --- 4. 메인 화면 레이아웃 ---
st.set_page_config(page_title="아시아나 에어포트 채용비서", layout="wide")

# [왼쪽 사이드바: 기존 질문 항목 100% 동일]
with st.sidebar:
    st.header("📋 모바일 간편지원")
    st.write("아래 항목을 모두 입력해 주세요.")
    
    with st.form("sidebar_form", clear_on_submit=True):
        name = st.text_input("이름")
        gender = st.radio("성별", ["남성", "여성"], horizontal=True)
        age = st.number_input("나이", min_value=19, max_value=70, value=30)
        phone = st.text_input("연락처 (숫자만)")
        address = st.text_input("주소 (OO동까지)")
        
        st.write("---")
        transport = st.selectbox("출퇴근 교통방법", ["셔틀버스", "자차", "대중교통"])
        travel_time = st.text_input("출퇴근 소요시간 (예: 40분)")
        arrival_ok = st.radio("오전 05:20까지 도착 가능여부", ["O", "X"], horizontal=True)
        
        if st.form_submit_button("지원서 최종 제출"):
            if name and phone and travel_time:
                app_data = {
                    "신청시간": [datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                    "이름": [name], "성별": [gender], "나이": [age],
                    "연락처": [phone], "주소": [address], "교통방법": [transport],
                    "소요시간": [travel_time], "05:20도착가능": [arrival_ok]
                }
                res = save_application(app_data)
                st.success(f"✅ {name}님, 접수가 완료되었습니다!")
                st.balloons()
            else:
                st.warning("모든 필수 항목을 입력해주세요.")

# [오른쪽 메인]
st.title("✈️ 아시아나 에어포트 스마트 채용 시스템")
tab1, tab2 = st.tabs(["💬 AI 실시간 상담", "📊 관리 데이터 분석"])

# [탭 1: AI 상담 - 기존 로직 유지]
with tab1:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    prompt = st.chat_input("채용에 대해 궁금한 점을 물어보세요!")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant"):
            full_instruction = f"너는 다정한 채용 담당자야. 아래 정보를 바탕으로 답해줘:\n{COMPANY_KNOWLEDGE}\n\n질문: {prompt}"
            response = model.generate_content(full_instruction)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})

# [탭 2: 관리자 분석 - 보안 강화 버전]
with tab2:
    st.subheader("🔐 보안 관리자 로그인")
    c1, c2 = st.columns(2)
    in_id = c1.text_input("아이디", key="admin_id_login")
    in_pw = c2.text_input("비밀번호", type="password", key="admin_pw_login")

    if in_id == ADMIN_ID and in_pw == ADMIN_PW:
        st.success("🔓 인증 성공!")
        
        if os.path.exists(DATA_FILE):
            # --- 에러가 나기 전에 '초기화 버튼'부터 배치합니다 ---
            st.warning("⚠️ 데이터 형식이 맞지 않으면 에러가 날 수 있습니다.")
            if st.button("🚫 모든 데이터 초기화 (파기)"):
                os.remove(DATA_FILE)
                st.success("데이터가 삭제되었습니다. 새로고침 후 다시 이용하세요.")
                st.rerun()
            
            st.divider()

            # 에러가 나더라도 화면이 멈추지 않게 보호막(try-except)을 쳤습니다.
            try:
                df = pd.read_csv(DATA_FILE)
                # '연락처' 컬럼이 있으면 암호를 풀어봅니다.
                if '연락처' in df.columns:
                    df['연락처'] = df['연락처'].apply(decrypt_val)
                
                st.write(f"총 지원자: **{len(df)}명**")
                st.dataframe(df.sort_values(by="신청시간", ascending=False))
                
                # 엑셀 다운로드
                csv = df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 엑셀 다운로드", data=csv, file_name='applicants.csv')
            except Exception as e:
                st.error(f"데이터 로딩 중 오류 발생: {e}")
                st.info("위의 '초기화' 버튼을 눌러 데이터를 비우고 새로 시작해보세요.")
        else:
            st.info("저장된 데이터가 없습니다.")
