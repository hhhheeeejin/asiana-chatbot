import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import io

# ─────────────────────────────────────────
# Supabase 설정 (secrets.toml에서 읽어옴)
# ─────────────────────────────────────────
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}
HEADERS_WRITE = {**HEADERS, "Prefer": "return=representation"}

# ─────────────────────────────────────────
# Supabase 저장 함수
# ─────────────────────────────────────────
def save_applicant(data: dict):
    """지원자 데이터를 Supabase에 저장"""
    res = requests.post(
        f"{SUPABASE_URL}/rest/v1/applicants",
        headers=HEADERS_WRITE,
        json=data
    )
    return res.status_code in [200, 201]

def save_question_log(question_text: str, question_type: str, topic: str):
    """질문 로그를 Supabase에 저장"""
    requests.post(
        f"{SUPABASE_URL}/rest/v1/question_logs",
        headers=HEADERS_WRITE,
        json={"유형": question_type, "주제": topic, "질문내용": question_text}
    )

def get_applicants() -> pd.DataFrame:
    """지원자 목록 불러오기"""
    try:
        res = requests.get(
            f"{SUPABASE_URL}/rest/v1/applicants?select=*&order=created_at.desc",
            headers=HEADERS
        )
        if res.status_code != 200:
            st.error(f"Supabase 오류 ({res.status_code}): {res.text}")
            return pd.DataFrame()
        data = res.json()
        return pd.DataFrame(data) if data else pd.DataFrame()
    except Exception as e:
        st.error(f"연결 오류: {e}")
        return pd.DataFrame()

def get_question_logs() -> pd.DataFrame:
    """질문 로그 불러오기"""
    try:
        res = requests.get(
            f"{SUPABASE_URL}/rest/v1/question_logs?select=*&order=created_at.desc",
            headers=HEADERS
        )
        if res.status_code != 200:
            return pd.DataFrame()
        data = res.json()
        return pd.DataFrame(data) if data else pd.DataFrame()
    except Exception:
        return pd.DataFrame()

def check_duplicate(phone: str) -> bool:
    """연락처 중복 확인"""
    try:
        res = requests.get(
            f"{SUPABASE_URL}/rest/v1/applicants?연락처=eq.{phone}&select=연락처",
            headers=HEADERS
        )
        return len(res.json()) > 0
    except Exception:
        return False

def df_to_excel_bytes(df: pd.DataFrame) -> bytes:
    """DataFrame을 엑셀 바이트로 변환 (다운로드용)"""
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    return buf.getvalue()

# ─────────────────────────────────────────
# 규칙 기반 답변 사전
# ─────────────────────────────────────────
FAQ_ANSWERS = {
    "급여": """💰 **급여 안내**

- 월 평균 **289만원 이상**
- 구성: 기본급 + 식대지원비 + 교통지원비 + 기타수당
- 기타수당(시간외·야간 근무): 평균 **10~30만원** 별도 지급

궁금한 점이 더 있으시면 편하게 물어보세요 😊""",

    "셔틀": """🚌 **셔틀버스 안내**

| 출발지 | 출발 시간 |
|--------|----------|
| 발산역 / 김포공항 | **04:30** 출발 |
| 부천 원종사거리 | **04:30** 출발 |
| 고강동 | 지원 |

※ 셔틀 이용 시 교통비(일 12,000원)에서 셔틀비용 차감 후 지급""",

    "복리후생": """🎁 **복리후생 안내**

- 🍱 식비 지급
- 🚇 교통비 일 **12,000원** 지원 (새벽 근무 시 **+1만원** 추가)
- 🚌 셔틀버스 운행 지원
- 👔 유니폼 지급
- ✈️ 1년 이상 근무 시 아시아나 항공권 지급 (**15만원** 상당)
- 🅿️ 야외 주차장 이용 가능 (월 3만원 별도)""",

    "근무시간": """⏰ **근무시간 안내**

- 오전 근무: **05:45 ~ 14:45**
- 오후 근무: **14:00 ~ 23:00**
- 스케줄: **3일 근무 → 1일 휴무** 반복

※ 오전 근무 시 05:45까지 인천국제공항 도착 필요""",

    "업무": """🛠 **담당 업무 안내**

- 아시아나 항공기 기내청소 (시트, 벽면, 주방 등)
- 기내 정리정돈
- 항공기 출발 전후 정비
- 소형기 청소 약 30분 소요
- 팀 단위 업무 (소형기 기준 10~13명)

✅ **초보자 가능** — 입사 후 교육 진행""",

    "근무지": """📍 **근무지 안내**

- 근무지: **인천국제공항**
- 🅿️ 야외 주차장 이용 가능 (월 3만원 별도)
- 셔틀버스: 발산역·부천 원종사거리·고강동 지원""",

    "지원": """📝 **지원 방법**

오른쪽 **'📝 간편 지원서 작성' 탭**을 이용해 주세요!

지원 후 서류 합격자에 한해 개별 연락 드립니다.""",

    "면접": """📋 **면접 안내**

- 서류 합격자에 한해 **개별 연락** 드립니다.
- 면접 일정은 연락 시 안내 드릴 예정입니다.

지원은 **'📝 간편 지원서 작성' 탭**을 이용해 주세요!""",

    "주차": """🅿️ **주차 안내**

- 야외 주차장 이용 가능
- 비용: 월 **3만원** 별도 발생""",

    "교통비": """🚇 **교통비 안내**

- 기본: 일 **12,000원** 지원
- 새벽 근무 시: **+10,000원** 추가 지급
- 셔틀버스 이용 시: 교통비에서 셔틀비용 차감 후 지급""",

    "초보": """✅ **초보자도 지원 가능합니다!**

- 입사 후 체계적인 교육 진행
- 팀 단위 업무로 함께 배우며 시작
- 소형기 청소 약 30분 소요 (팀 10~13명)

경력 없어도 걱정 마세요 😊""",
}

KEYWORD_MAP = [
    (["급여", "월급", "돈", "페이", "연봉", "수당", "얼마", "임금"], "급여"),
    (["셔틀", "버스", "차량", "픽업", "발산", "부천", "원종", "고강"], "셔틀"),
    (["복리", "복지", "혜택", "항공권", "유니폼", "식비", "식대"], "복리후생"),
    (["근무시간", "시간", "출근", "퇴근", "스케줄", "일정", "몇시", "오전", "오후", "휴무"], "근무시간"),
    (["업무", "하는일", "청소", "정비", "기내", "내용", "직무", "일이"], "업무"),
    (["근무지", "위치", "어디", "공항", "인천"], "근무지"),
    (["지원", "신청", "어떻게", "방법", "접수"], "지원"),
    (["면접", "합격", "서류", "연락"], "면접"),
    (["주차", "자차", "주차장"], "주차"),
    (["교통비", "교통", "지원비"], "교통비"),
    (["초보", "경력", "처음", "가능", "무경력", "배우"], "초보"),
]

DEFAULT_REPLY = """죄송합니다, 해당 내용은 담당자에게 직접 문의해 주세요 😊

아래 버튼으로 자주 묻는 질문을 빠르게 확인하실 수 있어요!
- 💰 급여 안내  /  🚌 셔틀 시간  /  🎁 복리후생  /  🗺️ 출퇴근 소요시간"""

def get_reply(user_input: str) -> str:
    text = user_input.replace(" ", "")
    for keywords, key in KEYWORD_MAP:
        if any(kw in text for kw in keywords):
            return FAQ_ANSWERS[key]
    return DEFAULT_REPLY

# ─────────────────────────────────────────
# 스타일
# ─────────────────────────────────────────
st.set_page_config(page_title="아시아나 에어포트 채용", page_icon="✈️", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');
html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
.main-header {
    background: linear-gradient(135deg, #003580 0%, #0057b8 60%, #1a73e8 100%);
    color: white; padding: 28px 32px; border-radius: 16px;
    margin-bottom: 24px; display: flex; align-items: center; gap: 16px;
}
.main-header h1 { margin: 0; font-size: 1.6rem; font-weight: 700; }
.main-header p  { margin: 4px 0 0; font-size: 0.92rem; opacity: 0.85; }
.info-card {
    background: #f0f4ff; border-left: 4px solid #0057b8; border-radius: 10px;
    padding: 16px 20px; margin-bottom: 12px; font-size: 0.88rem; line-height: 1.7;
}
.info-card strong { color: #003580; }
div[data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(135deg, #003580, #0057b8) !important;
    color: white !important; border: none !important; border-radius: 10px !important;
    font-weight: 700 !important; font-size: 1rem !important; padding: 12px !important;
}
.stDownloadButton > button {
    background: #1a7a4a !important; color: white !important;
    border: none !important; border-radius: 8px !important; font-weight: 600 !important;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# 헤더
# ─────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <div style="font-size:2.8rem;">✈️</div>
    <div>
        <h1>아시아나 에어포트 채용 안내</h1>
        <p>기내청소 · 인천국제공항 근무 · 채용 상담 및 간편지원</p>
    </div>
</div>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["💬 채용 상담", "📝 간편 지원서 작성"])

# ══════════════════════════════════════════
# 탭 1: 채용 상담
# ══════════════════════════════════════════
with tab1:
    col_info, col_chat = st.columns([1, 2])

    with col_info:
        st.markdown("#### 📋 채용 핵심 정보")
        st.markdown("""
        <div class="info-card"><strong>🏢 회사</strong><br>아시아나 에어포트</div>
        <div class="info-card"><strong>📍 근무지</strong><br>인천국제공항</div>
        <div class="info-card"><strong>🛠 업무</strong><br>아시아나 항공기 기내청소<br>정리정돈 · 출발 전후 정비<br>초보자 가능 (교육 제공)</div>
        <div class="info-card"><strong>⏰ 근무시간</strong><br>오전 05:45 ~ 14:45<br>오후 14:00 ~ 23:00<br>3일 근무 · 1일 휴무 반복</div>
        <div class="info-card"><strong>💰 급여</strong><br>월 평균 <b>289만원 이상</b><br>(기본급+식대+교통비+수당)</div>
        <div class="info-card"><strong>🚌 셔틀버스</strong><br>발산역 / 김포공항 04:30<br>부천 원종사거리 04:30<br>고강동 지원</div>
        <div class="info-card"><strong>🎁 복리후생</strong><br>식비 · 교통비 · 유니폼 지급<br>1년 근무 시 항공권 (15만원)</div>
        """, unsafe_allow_html=True)

    with col_chat:
        st.markdown("#### 💬 채용 상담")
        st.caption("버튼을 누르거나 질문을 직접 입력하세요. (외부 서버 연결 없음 🔒)")

        if "messages" not in st.session_state:
            st.session_state.messages = [{
                "role": "assistant",
                "content": "안녕하세요! 아시아나 에어포트 채용 상담 챗봇입니다 ✈️\n\n아래 버튼을 누르거나 궁금한 점을 직접 입력해 주세요 😊\n\n지원을 원하시면 **'📝 간편 지원서 작성' 탭**을 이용해 주세요!"
            }]
        if "faq_trigger" not in st.session_state:
            st.session_state.faq_trigger = None
        if "show_commute" not in st.session_state:
            st.session_state.show_commute = False

        st.markdown("**💡 자주 묻는 질문**")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            if st.button("💰 급여 안내", use_container_width=True):
                st.session_state.faq_trigger = "급여"
                st.session_state.show_commute = False
                save_question_log("급여가 어떻게 되나요?", "버튼", "급여")
        with c2:
            if st.button("🚌 셔틀 시간", use_container_width=True):
                st.session_state.faq_trigger = "셔틀"
                st.session_state.show_commute = False
                save_question_log("셔틀버스 시간이 어떻게 되나요?", "버튼", "셔틀")
        with c3:
            if st.button("🎁 복리후생", use_container_width=True):
                st.session_state.faq_trigger = "복리후생"
                st.session_state.show_commute = False
                save_question_log("복리후생 혜택을 알려주세요.", "버튼", "복리후생")
        with c4:
            if st.button("🗺️ 출퇴근 소요시간", use_container_width=True):
                st.session_state.show_commute = not st.session_state.show_commute
                st.session_state.faq_trigger = None

        if st.session_state.show_commute:
            with st.container(border=True):
                st.markdown("##### 🗺️ 집에서 근무지까지 소요시간")
                st.caption("출발 지역명을 입력하시면 셔틀 탑승 여부와 예상 안내를 드립니다.")
                addr_col, btn_col = st.columns([3, 1])
                with addr_col:
                    home_addr = st.text_input("출발지", placeholder="예) 부천 원종동, 발산역, 강남구 등",
                                              label_visibility="collapsed", key="home_addr")
                with btn_col:
                    if st.button("확인 🔍", use_container_width=True):
                        if home_addr.strip():
                            save_question_log(f"출발지: {home_addr.strip()}", "버튼", "출퇴근소요시간")
                            st.session_state.faq_trigger = f"__commute__{home_addr.strip()}"
                            st.session_state.show_commute = False
                            st.rerun()

        if st.session_state.faq_trigger:
            trigger = st.session_state.faq_trigger
            st.session_state.faq_trigger = None

            if trigger.startswith("__commute__"):
                region = trigger.replace("__commute__", "")
                if any(k in region for k in ["발산", "김포"]):
                    shuttle = "발산역 / 김포공항 **04:30** 출발 셔틀 이용 가능 ✅"
                elif any(k in region for k in ["부천", "원종", "고강"]):
                    shuttle = "부천 원종사거리 **04:30** 출발 셔틀 이용 가능 ✅"
                else:
                    shuttle = "해당 지역 셔틀 정보 없음 (담당자 문의 권장)"

                reply = f"""🗺️ **{region} → 인천국제공항 출퇴근 안내**

🚌 **셔틀버스**: {shuttle}
🚗 **자차**: 야외 주차장 이용 가능 (월 3만원)
🚇 **대중교통**: 공항철도 이용 (서울역 기준 약 43분)

오전 05:45 근무 기준 **04:30 이전 출발**을 권장드립니다 😊"""
                user_msg = f"집에서 근무지까지 소요시간이 궁금합니다. (출발지: {region})"
            else:
                reply = FAQ_ANSWERS[trigger]
                labels = {"급여": "급여가 어떻게 되나요?", "셔틀": "셔틀버스 시간이 어떻게 되나요?", "복리후생": "복리후생 혜택을 알려주세요."}
                user_msg = labels.get(trigger, trigger)

            st.session_state.messages.append({"role": "user", "content": user_msg})
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.rerun()

        chat_container = st.container(height=400)
        with chat_container:
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        if user_input := st.chat_input("질문을 입력하세요. 예) 초보자도 지원 가능한가요?"):
            reply = get_reply(user_input)
            matched_topic = "기타"
            for keywords, key in KEYWORD_MAP:
                if any(kw in user_input.replace(" ", "") for kw in keywords):
                    matched_topic = key
                    break
            save_question_log(user_input, "직접입력", matched_topic)
            st.session_state.messages.append({"role": "user", "content": user_input})
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.rerun()

        if st.button("🔄 대화 초기화", use_container_width=True):
            st.session_state.messages = []
            st.session_state.show_commute = False
            st.rerun()


# ══════════════════════════════════════════
# 탭 2: 간편 지원서
# ══════════════════════════════════════════
with tab2:
    col_form, col_guide = st.columns([2, 1])

    with col_guide:
        st.markdown("#### 📌 지원 안내")
        st.info("""
**지원 절차**

1️⃣ 아래 양식 작성 후 제출
2️⃣ 서류 검토 (담당자)
3️⃣ 합격자 개별 연락
4️⃣ 면접 일정 안내

---
**문의사항**은 왼쪽
💬 채용 상담 탭을 이용해 주세요!
        """)
        st.markdown("#### ⚠️ 유의사항")
        st.warning("""
- 오전 근무 시 **05:45 도착** 필요
- 모든 항목 필수 입력
- 중복 지원 불가 (연락처 기준)
        """)

    with col_form:
        st.markdown("#### 📝 간편 지원서")

        with st.form("apply_form", clear_on_submit=True):
            st.markdown("**기본 정보**")
            col1, col2, col3 = st.columns(3)
            with col1:
                name = st.text_input("이름 *")
            with col2:
                gender = st.selectbox("성별 *", ["선택", "남", "여"])
            with col3:
                age = st.number_input("나이 *", min_value=15, max_value=80, step=1, value=None)

            phone = st.text_input("연락처 * (예: 010-1234-5678)")

            st.markdown("---")
            st.markdown("**출퇴근 정보**")
            col4, col5 = st.columns(2)
            with col4:
                transport = st.selectbox("출퇴근 교통수단 *", ["선택", "자차", "대중교통", "셔틀버스"])
            with col5:
                commute_time = st.number_input("출퇴근 소요시간 (분) *", min_value=0, max_value=300, step=5, value=None)

            st.markdown("---")
            arrive_ok = st.radio("⏰ 오전 05:20까지 근무지 도착 가능 여부 *",
                                 ["O (가능)", "X (불가능)"], horizontal=True)

            st.markdown("")
            submitted = st.form_submit_button("✅ 지원서 제출하기", use_container_width=True)

            if submitted:
                errors = []
                if not name.strip():     errors.append("이름을 입력해 주세요.")
                if gender == "선택":      errors.append("성별을 선택해 주세요.")
                if age is None:          errors.append("나이를 입력해 주세요.")
                if not phone.strip():    errors.append("연락처를 입력해 주세요.")
                if transport == "선택":  errors.append("교통수단을 선택해 주세요.")
                if commute_time is None: errors.append("출퇴근 소요시간을 입력해 주세요.")

                if errors:
                    for e in errors:
                        st.error(e)
                else:
                    if check_duplicate(phone.strip()):
                        st.warning(f"⚠️ 해당 연락처({phone})로 이미 지원하셨습니다. 담당자에게 문의해 주세요.")
                    else:
                        save_applicant({
                            "이름": name.strip(),
                            "성별": gender,
                            "나이": int(age),
                            "연락처": phone.strip(),
                            "교통수단": transport,
                            "출퇴근소요시간": int(commute_time),
                            "도착가능여부": arrive_ok[0],
                        })
                        st.success(f"🎉 {name}님, 지원서가 성공적으로 접수되었습니다!\n\n서류 검토 후 합격자에 한해 개별 연락 드립니다.")
                        st.balloons()

        # ── 관리자 메뉴 ──────────────────────
        st.markdown("---")
        ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "admin1234")

        if "admin_auth" not in st.session_state:
            st.session_state.admin_auth = False

        if not st.session_state.admin_auth:
            with st.expander("🔒 관리자 로그인"):
                pw_input = st.text_input("관리자 비밀번호", type="password", key="pw_input")
                if st.button("로그인", use_container_width=True):
                    if pw_input == ADMIN_PASSWORD:
                        st.session_state.admin_auth = True
                        st.rerun()
                    else:
                        st.error("비밀번호가 올바르지 않습니다.")
        else:
            with st.expander("🔓 관리자 메뉴 (로그인됨)", expanded=True):
                col_logout, _ = st.columns([1, 3])
                with col_logout:
                    if st.button("🚪 로그아웃", use_container_width=True):
                        st.session_state.admin_auth = False
                        st.rerun()

                st.markdown("---")
                st.markdown("##### 👤 지원자 목록")
                df_applicants = get_applicants()
                if not df_applicants.empty:
                    # 보기 편하게 컬럼 정리
                    show_cols = ["이름", "성별", "나이", "연락처", "교통수단", "출퇴근소요시간", "도착가능여부", "created_at"]
                    show_cols = [c for c in show_cols if c in df_applicants.columns]
                    st.markdown(f"**총 지원자: {len(df_applicants)}명**")
                    st.dataframe(df_applicants[show_cols], use_container_width=True)
                    st.download_button(
                        label="📥 지원자 목록 엑셀 다운로드",
                        data=df_to_excel_bytes(df_applicants[show_cols]),
                        file_name=f"지원자목록_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                else:
                    st.info("아직 접수된 지원자가 없습니다.")

                st.markdown("---")
                st.markdown("##### 💬 질문 로그")
                df_questions = get_question_logs()
                if not df_questions.empty:
                    st.markdown(f"**총 질문 수: {len(df_questions)}건**")
                    topic_counts = df_questions["주제"].value_counts().reset_index()
                    topic_counts.columns = ["주제", "질문수"]
                    st.markdown("**주제별 관심도**")
                    st.dataframe(topic_counts, use_container_width=True, hide_index=True)
                    st.markdown("**전체 질문 내역**")
                    st.dataframe(df_questions, use_container_width=True)
                    st.download_button(
                        label="📥 질문 로그 엑셀 다운로드",
                        data=df_to_excel_bytes(df_questions),
                        file_name=f"질문로그_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                else:
                    st.info("아직 기록된 질문이 없습니다.")
