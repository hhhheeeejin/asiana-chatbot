import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import io

# ─────────────────────────────────────────
# Supabase 설정
# ─────────────────────────────────────────
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}
HEADERS_WRITE = {**HEADERS, "Prefer": "return=representation"}

GOOGLE_FORM_URL = "https://forms.gle/pFe9sx2dMAQcB4j6A"
KAKAO_URL = "https://open.kakao.com/o/srqqCGki"

# ─────────────────────────────────────────
# 단시간조 시간대 정의
# ─────────────────────────────────────────
PART_TIME_SHIFTS = [
    {"id": "shift_1", "label": "06:45 ~ 10:45", "note": "06:20까지 인천공항 1터미널 검색대 도착 필요"},
    {"id": "shift_2", "label": "11:00 ~ 15:00", "note": None},
    {"id": "shift_3", "label": "16:00 ~ 20:00", "note": None},
    {"id": "shift_4", "label": "18:00 ~ 22:00", "note": None},
]

# ─────────────────────────────────────────
# Supabase 함수
# ─────────────────────────────────────────
def save_question_log(question_text: str, question_type: str, topic: str):
    try:
        requests.post(
            f"{SUPABASE_URL}/rest/v1/question_logs",
            headers=HEADERS_WRITE,
            json={"유형": question_type, "주제": topic, "질문내용": question_text},
            timeout=5
        )
    except Exception:
        pass

def get_question_logs() -> pd.DataFrame:
    try:
        res = requests.get(
            f"{SUPABASE_URL}/rest/v1/question_logs?select=*&order=created_at.desc",
            headers=HEADERS, timeout=5
        )
        if res.status_code != 200:
            return pd.DataFrame()
        data = res.json()
        return pd.DataFrame(data) if data else pd.DataFrame()
    except Exception:
        return pd.DataFrame()

def get_shift_settings() -> dict:
    """Supabase에서 단시간조 ON/OFF 상태 불러오기"""
    try:
        res = requests.get(
            f"{SUPABASE_URL}/rest/v1/shift_settings?select=*",
            headers=HEADERS, timeout=5
        )
        if res.status_code != 200:
            return {}
        data = res.json()
        return {row["shift_id"]: row["is_active"] for row in data}
    except Exception:
        return {}

def save_shift_setting(shift_id: str, is_active: bool):
    """Supabase에 단시간조 ON/OFF 상태 저장 (upsert)"""
    try:
        requests.post(
            f"{SUPABASE_URL}/rest/v1/shift_settings",
            headers={**HEADERS_WRITE, "Prefer": "resolution=merge-duplicates,return=minimal"},
            json={"shift_id": shift_id, "is_active": is_active},
            timeout=5
        )
    except Exception:
        pass

def df_to_excel_bytes(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    return buf.getvalue()

# ─────────────────────────────────────────
# 활성 단시간조 가져오기
# ─────────────────────────────────────────
def get_active_shifts():
    return [s for s in PART_TIME_SHIFTS
            if st.session_state.get(f"shift_active_{s['id']}", False)]

# ─────────────────────────────────────────
# AI 시스템 프롬프트 (활성 단시간조만 포함)
# ─────────────────────────────────────────
def build_system_prompt():
    active_shifts = get_active_shifts()
    part_time_section = ""

    if active_shifts:
        shift_list = "\n".join([
            f"  - {s['label']}" + (f" (⚠️ {s['note']})" if s['note'] else "")
            for s in active_shifts
        ])
        part_time_section = f"""

■ 단시간조 채용 (현재 모집 중)
- 근무지: 인천국제공항
- 급여: 월 1,700,000원
- 고용형태: 윌앤비전 정규직 (4대보험, 윌앤비전 기본 복리후생 적용)
- 모집 시간대:
{shift_list}
"""

    return f"""당신은 아시아나 에어포트 채용 담당 상담사입니다.
지원자의 채용 관련 질문에 친절하고 정확하게 답변하세요.

■ 정규조 채용 정보
- 회사명: 아시아나 에어포트 / 근무지: 인천국제공항
- 담당 업무: 아시아나 항공기 기내청소 (시트, 벽면, 주방 등), 정리정돈, 출발 전후 정비
- 소형기 청소 약 30분 / 팀 단위 (소형기 10~13명) / 초보자 가능 (교육 제공)
- 근무시간: 오전 05:45~14:45 / 오후 14:00~23:00 / 3일 근무 1일 휴무 반복
- 급여: 월 평균 289만원 이상 (기본급+식대+교통비+기타수당, 야간·시간외 수당 평균 10~30만원)
- 복리후생: 식비·교통비(일 12,000원, 새벽 +1만원)·유니폼 지급 / 셔틀버스(발산역·김포공항·부천 원종사거리·고강동 04:30) / 1년 근무 시 항공권 15만원 / 주차장 월 3만원
- 지원: 간편지원 바로가기 버튼 클릭 / 면접: 서류 합격자 개별 연락{part_time_section}

[답변 규칙]
1. 위 채용 정보를 바탕으로 정확하게 답변하세요.
2. 단시간조 모집 중인 시간대가 없으면 단시간조 관련 정보는 절대 언급하지 마세요.
3. 정보에 없는 내용은 "담당자에게 확인 후 안내드리겠습니다 😊"라고 하세요.
4. 지원 방법을 묻는 경우 왼쪽 '📝 간편지원 바로가기' 버튼을 안내하세요.
5. 말투는 친근하고 전문적으로, 이모지를 적절히 활용하세요.
6. 답변은 간결하게 유지하세요.
"""

# ─────────────────────────────────────────
# AI 답변 함수
# ─────────────────────────────────────────
def get_ai_reply(messages: list) -> str:
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=build_system_prompt(),
            messages=messages
        )
        return response.content[0].text
    except Exception as e:
        return f"일시적인 오류가 발생했습니다. 잠시 후 다시 시도하거나 카카오 오픈채팅으로 문의해 주세요 😊"

# ─────────────────────────────────────────
# FAQ 버튼 규칙 기반 답변
# ─────────────────────────────────────────
FAQ_ANSWERS = {
    "급여": """💰 **급여 안내**

**[정규조]**
- 월 평균 **289만원 이상**
- 기본급 + 식대지원비 + 교통지원비 + 기타수당
- 야간·시간외 수당: 평균 **10~30만원** 별도 지급""",

    "급여_단시간": """💰 **급여 안내**

**[정규조]**
- 월 평균 **289만원 이상**
- 기본급 + 식대지원비 + 교통지원비 + 기타수당
- 야간·시간외 수당: 평균 **10~30만원** 별도 지급

**[단시간조]**
- 월 **170만원**
- 윌앤비전 정규직 (4대보험 적용)""",

    "셔틀": """🚌 **셔틀버스 안내** (정규조)

| 출발지 | 출발 시간 |
|--------|----------|
| 발산역 / 김포공항 | **04:30** 출발 |
| 부천 원종사거리 | **04:30** 출발 |
| 고강동 | 지원 |

※ 셔틀 이용 시 교통비(일 12,000원)에서 셔틀비용 차감 후 지급""",

    "복리후생": """🎁 **복리후생 안내**

**[정규조]**
- 🍱 식비 지급
- 🚇 교통비 일 **12,000원** (새벽 근무 시 **+1만원**)
- 🚌 셔틀버스 지원
- 👔 유니폼 지급
- ✈️ 1년 근무 시 항공권 **15만원** 상당
- 🅿️ 주차장 월 3만원""",

    "복리후생_단시간": """🎁 **복리후생 안내**

**[정규조]**
- 🍱 식비 지급
- 🚇 교통비 일 **12,000원** (새벽 근무 시 **+1만원**)
- 🚌 셔틀버스 지원
- 👔 유니폼 지급
- ✈️ 1년 근무 시 항공권 **15만원** 상당
- 🅿️ 주차장 월 3만원

**[단시간조]**
- 윌앤비전 정규직 (4대보험)
- 윌앤비전 기본 복리후생 적용""",
}

KEYWORD_MAP = [
    (["급여", "월급", "돈", "페이", "연봉", "수당", "얼마", "임금"], "급여"),
    (["셔틀", "버스", "차량", "픽업", "발산", "부천", "원종", "고강"], "셔틀"),
    (["복리", "복지", "혜택", "항공권", "유니폼", "식비", "식대"], "복리후생"),
]

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
    color: #1a1a1a !important;
}
.info-card strong { color: #003580 !important; }
.info-card b { color: #003580 !important; }
.part-card {
    background: #fff8e1; border-left: 4px solid #f59e0b; border-radius: 10px;
    padding: 16px 20px; margin-bottom: 12px; font-size: 0.88rem; line-height: 1.7;
    color: #1a1a1a !important;
}
.part-card strong { color: #b45309 !important; }
.part-card b { color: #b45309 !important; }
.section-title {
    font-size: 0.78rem; font-weight: 700; letter-spacing: 0.05em;
    color: #6b7280; margin: 16px 0 8px;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# 세션 초기화
# ─────────────────────────────────────────
# 단시간조 토글 상태: Supabase에서 최초 1회 로드
if "shift_settings_loaded" not in st.session_state:
    settings = get_shift_settings()
    for shift in PART_TIME_SHIFTS:
        key = f"shift_active_{shift['id']}"
        st.session_state[key] = settings.get(shift["id"], False)
    st.session_state.shift_settings_loaded = True

if "admin_auth" not in st.session_state:
    st.session_state.admin_auth = False
if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant",
        "content": "안녕하세요! 아시아나 에어포트 채용 상담 챗봇입니다 ✈️\n\n아래 버튼을 누르거나 궁금한 점을 직접 입력해 주세요 😊\n\n지원을 원하시면 왼쪽 **📝 간편지원 바로가기** 버튼을 이용해 주세요!"
    }]
if "faq_trigger" not in st.session_state:
    st.session_state.faq_trigger = None
if "show_commute" not in st.session_state:
    st.session_state.show_commute = False

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

# ─────────────────────────────────────────
# 메인 레이아웃
# ─────────────────────────────────────────
col_info, col_chat = st.columns([1, 2])

# ── 왼쪽: 채용 정보 ──────────────────────
with col_info:
    # 정규조 아코디언
    st.markdown('<div class="section-title">🔵 정규조</div>', unsafe_allow_html=True)

    with st.expander("🏢 회사 · 근무지 · 업무"):
        st.markdown("""
        <div class="info-card"><strong>🏢 회사</strong><br>아시아나 에어포트</div>
        <div class="info-card"><strong>📍 근무지</strong><br>인천국제공항</div>
        <div class="info-card"><strong>🛠 업무</strong><br>아시아나 항공기 기내청소<br>정리정돈 · 출발 전후 정비<br>초보자 가능 (교육 제공)</div>
        """, unsafe_allow_html=True)

    with st.expander("⏰ 근무시간"):
        st.markdown("""
        <div class="info-card"><strong>⏰ 근무시간</strong><br>오전 05:45 ~ 14:45<br>오후 14:00 ~ 23:00<br>3일 근무 · 1일 휴무 반복</div>
        """, unsafe_allow_html=True)

    with st.expander("💰 급여"):
        st.markdown("""
        <div class="info-card"><strong>💰 급여</strong><br>월 평균 <b>289만원 이상</b><br>(기본급+식대+교통비+수당)<br><br>기타수당(야간·시간외): 평균 10~30만원 별도</div>
        """, unsafe_allow_html=True)

    with st.expander("🚌 셔틀버스"):
        st.markdown("""
        <div class="info-card"><strong>🚌 셔틀버스</strong><br>발산역 / 김포공항 04:30<br>부천 원종사거리 04:30<br>고강동 지원<br><br>※ 셔틀 이용 시 교통비에서 셔틀비용 차감 후 지급</div>
        """, unsafe_allow_html=True)

    with st.expander("🎁 복리후생"):
        st.markdown("""
        <div class="info-card"><strong>🎁 복리후생</strong><br>식비 지급<br>교통비 일 12,000원 (새벽 +1만원)<br>유니폼 지급<br>1년 근무 시 항공권 (15만원)<br>야외 주차장 월 3만원</div>
        """, unsafe_allow_html=True)

    # 단시간조 아코디언 (활성 시간대만)
    active_shifts = get_active_shifts()
    if active_shifts:
        st.markdown('<div class="section-title">🟡 단시간조 (모집 중)</div>', unsafe_allow_html=True)
        shift_html = ""
        for s in active_shifts:
            shift_html += f"· {s['label']}<br>"
            if s['note']:
                shift_html += f"<span style='font-size:0.82rem;color:#b45309;'>⚠️ {s['note']}</span><br>"
        shift_html += "<br>"

        with st.expander("⏰ 모집 시간대 · 급여 · 고용형태"):
            st.markdown(f"""
            <div class="part-card">
                <strong>📍 근무지</strong><br>인천국제공항<br><br>
                <strong>⏰ 모집 시간대</strong><br>{shift_html}
                <strong>💰 급여</strong><br>월 <b>170만원</b><br><br>
                <strong>🏢 고용형태</strong><br>윌앤비전 정규직<br>(4대보험, 기본 복리후생 적용)
            </div>
            """, unsafe_allow_html=True)

    # 간편지원 + 카카오 버튼
    st.markdown(f"""
    <a href="{GOOGLE_FORM_URL}" target="_blank" style="
        display:block; background:linear-gradient(135deg,#003580,#0057b8);
        color:white; text-align:center; padding:14px 16px; border-radius:10px;
        font-weight:700; font-size:1rem; text-decoration:none;
        margin-top:8px; margin-bottom:8px;">
        📝 간편지원 바로가기
    </a>
    <a href="{KAKAO_URL}" target="_blank" style="
        display:block; background:#FEE500; color:#3A1D1D;
        text-align:center; padding:12px 16px; border-radius:10px;
        font-weight:700; font-size:0.9rem; text-decoration:none;">
        💬 카카오 오픈채팅 문의
    </a>
    """, unsafe_allow_html=True)

# ── 오른쪽: 채팅 ─────────────────────────
with col_chat:
    st.markdown("#### 💬 채용 상담")
    st.caption("버튼은 빠른 안내 / 직접 입력 시 AI가 답변해드립니다 🤖")

    # 자주 묻는 질문 버튼
    st.markdown("**💡 자주 묻는 질문**")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("💰 급여 안내", use_container_width=True):
            has_part = bool(get_active_shifts())
            st.session_state.faq_trigger = "급여_단시간" if has_part else "급여"
            st.session_state.show_commute = False
            save_question_log("급여가 어떻게 되나요?", "버튼", "급여")
    with c2:
        if st.button("🚌 셔틀 시간", use_container_width=True):
            st.session_state.faq_trigger = "셔틀"
            st.session_state.show_commute = False
            save_question_log("셔틀버스 시간이 어떻게 되나요?", "버튼", "셔틀")
    with c3:
        if st.button("🎁 복리후생", use_container_width=True):
            has_part = bool(get_active_shifts())
            st.session_state.faq_trigger = "복리후생_단시간" if has_part else "복리후생"
            st.session_state.show_commute = False
            save_question_log("복리후생 혜택을 알려주세요.", "버튼", "복리후생")
    with c4:
        if st.button("🗺️ 출퇴근 소요시간", use_container_width=True):
            st.session_state.show_commute = not st.session_state.show_commute
            st.session_state.faq_trigger = None

    # 출퇴근 소요시간 입력창
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

    # FAQ 트리거 처리
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
            reply = FAQ_ANSWERS.get(trigger, "")
            labels = {
                "급여": "급여가 어떻게 되나요?",
                "급여_단시간": "급여가 어떻게 되나요?",
                "셔틀": "셔틀버스 시간이 어떻게 되나요?",
                "복리후생": "복리후생 혜택을 알려주세요.",
                "복리후생_단시간": "복리후생 혜택을 알려주세요.",
            }
            user_msg = labels.get(trigger, trigger)

        st.session_state.messages.append({"role": "user", "content": user_msg})
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()

    # 대화창
    chat_container = st.container(height=430)
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # 직접 입력 → AI 답변
    if user_input := st.chat_input("궁금한 점을 입력하세요. AI가 답변해드립니다 🤖"):
        matched_topic = "기타"
        for keywords, key in KEYWORD_MAP:
            if any(kw in user_input.replace(" ", "") for kw in keywords):
                matched_topic = key
                break
        save_question_log(user_input, "직접입력", matched_topic)
        st.session_state.messages.append({"role": "user", "content": user_input})

        with chat_container:
            with st.chat_message("user"):
                st.markdown(user_input)
            with st.chat_message("assistant"):
                with st.spinner("답변 생성 중..."):
                    reply = get_ai_reply(st.session_state.messages)
                    st.markdown(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply})

    # 초기화
    if st.button("🔄 대화 초기화", use_container_width=True):
        st.session_state.messages = [{
            "role": "assistant",
            "content": "안녕하세요! 아시아나 에어포트 채용 상담 챗봇입니다 ✈️\n\n아래 버튼을 누르거나 궁금한 점을 직접 입력해 주세요 😊\n\n지원을 원하시면 왼쪽 **📝 간편지원 바로가기** 버튼을 이용해 주세요!"
        }]
        st.session_state.show_commute = False
        st.rerun()

# ─────────────────────────────────────────
# 관리자 메뉴
# ─────────────────────────────────────────
st.markdown("---")
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "admin1234")

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

        # ── 단시간조 ON/OFF 토글 ─────────────
        st.markdown("##### 🟡 단시간조 모집 ON/OFF")
        st.caption("ON 시 해당 시간대 정보가 화면과 AI 답변에 공개됩니다. 변경 후 자동 저장됩니다.")

        for shift in PART_TIME_SHIFTS:
            key = f"shift_active_{shift['id']}"
            current_val = st.session_state.get(key, False)
            new_val = st.toggle(f"⏰ {shift['label']}", value=current_val, key=f"toggle_{shift['id']}")
            if new_val != current_val:
                st.session_state[key] = new_val
                save_shift_setting(shift["id"], new_val)
                st.rerun()

        active = get_active_shifts()
        if active:
            st.success(f"✅ 현재 모집 중: {', '.join([s['label'] for s in active])}")
        else:
            st.info("현재 모집 중인 단시간조 없음 (전체 OFF)")

        st.markdown("---")

        # ── 질문 로그 ────────────────────────
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
