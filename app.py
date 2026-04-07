import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from io import BytesIO
from PIL import Image

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="도자기 로그", layout="centered")

st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Pretendard', sans-serif !important;
        letter-spacing: -0.03em !important;
        background-color: #fcfcfc;
    }

    h1, h2, h3, p, div, b, strong, label, input, button, select, textarea {
        font-family: 'Pretendard', sans-serif !important;
        letter-spacing: -0.03em !important;
    }
    
    /* 하단 탭 스타일 수정 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background-color: white;
        padding: 10px;
        z-index: 1000;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.05);
        justify-content: space-around;
    }

    /* 기록 카드 스타일 */
    .log-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 20px;
        border: 1px solid #f0f0f0;
        margin-bottom: 20px;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.04);
    }
    
    /* 기분 스티커 스타일 */
    .mood-sticker {
        font-size: 24px;
        background: #f8f9fa;
        padding: 5px 10px;
        border-radius: 12px;
        display: inline-block;
    }

    /* 완성 태그 */
    .complete-tag {
        background-color: #4CAF50;
        color: white;
        padding: 2px 8px;
        border-radius: 5px;
        font-size: 0.7em;
        font-weight: bold;
    }
    
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 3.5em;
        background-color: #8d6e63;
        color: white;
        font-weight: bold;
        border: none;
    }

    .stImage > img {
        border-radius: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

# 데이터 설정
DATA_FILE = "pottery_diary_v2.csv"
MOOD_DICT = {
    "행복": "😊", "기쁨": "😄", "절망": "😱", 
    "슬픔": "😢", "화이팅": "🔥", "실망": "😞", "감격": "😭"
}

# 유틸리티 함수
def img_to_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="JPEG", quality=70)
    return base64.b64encode(buffered.getvalue()).decode()

def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df['날짜'] = pd.to_datetime(df['날짜']).dt.date
        return df
    return pd.DataFrame(columns=["날짜", "작품명", "흙", "단계", "내용", "사진", "기분", "작업유형", "기물종류"])

# --- 앱 메인 로직 ---
df = load_data()

# 상단 탭 구성
tab_home, tab_record, tab_project = st.tabs(["📅 캘린더", "📝 기록하기", "🏺 작품별"])

# --- [TAB 1: 캘린더 홈] ---
with tab_home:
    st.subheader("나의 도자기 달력")
    
    # 캘린더 날짜 선택
    selected_date = st.date_input("날짜를 선택하세요", datetime.now().date())
    
    # 해당 날짜의 기록 찾기
    day_records = df[df['날짜'] == selected_date]
    
    if not day_records.empty:
        for _, row in day_records.iterrows():
            st.markdown(f"""
            <div class="log-card">
                <div style="font-size: 1.5em; margin-bottom:10px;">{MOOD_DICT.get(row['기분'], '😶')}</div>
                <div style="font-weight:700; font-size:1.2em;">{row['작품명']}</div>
                <div style="color:#8d6e63; font-size:0.9em;">{row['작업유형']} | {row['기물종류']} | {row['단계']}</div>
                <div style="margin-top:10px; font-size:0.95em;">{row['내용']}</div>
            </div>
            """, unsafe_allow_html=True)
            if pd.notna(row['사진']) and row['사진'] != "":
                st.image(base64.b64decode(row['사진']))
    else:
        st.info(f"{selected_date}에는 아직 기록이 없습니다.")
        if st.button(f"➕ {selected_date} 기록 추가하기"):
            st.session_state.target_date = selected_date
            # 실제 이동은 Streamlit 특성상 다음 리런 시 반영되도록 유도하거나 탭 전환 안내

    st.divider()
    st.write("📅 이번 달 스티커 현황")
    # 간단한 월간 스티커 뷰 (리스트 형태)
    month_data = df.sort_values(by='날짜', ascending=False).head(10)
    cols = st.columns(5)
    for i, (_, row) in enumerate(month_data.iterrows()):
        with cols[i % 5]:
            st.markdown(f"<div style='text-align:center;'>{MOOD_DICT.get(row['기분'], '😶')}<br><small>{row['날짜'].day}일</small></div>", unsafe_allow_html=True)

# --- [TAB 2: 기록하기] ---
with tab_record:
    st.subheader("오늘의 작업 기록")
    
    with st.form("record_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            rec_date = st.date_input("작업 날짜", datetime.now().date())
        with col2:
            rec_mood = st.selectbox("오늘의 기분", list(MOOD_DICT.keys()))
            
        rec_title = st.text_input("작품명", placeholder="예: 달항아리 1호")
        
        col3, col4 = st.columns(2)
        with col3:
            rec_type = st.selectbox("작업 유형", ["물레", "핸드빌딩", "기타"])
        with col4:
            rec_clay = st.selectbox("흙 종류", ["백자토", "산백토", "조형토", "청자토", "옹기토", "기타"])
            
        rec_obj = st.selectbox("기물 종류", ["컵", "접시", "그릇", "항아리", "고블렛", "면기", "오브제", "기타"])
        rec_step = st.select_slider("현재 단계", options=["성형", "건조", "초벌", "시유", "완성"])
        
        rec_img = st.file_uploader("작업 사진", type=["jpg", "png", "jpeg"])
        rec_note = st.text_area("작업 메모")
        
        submit = st.form_submit_button("기록 저장하기")
        
        if submit:
            if rec_title:
                img_str = ""
                if rec_img:
                    img = Image.open(rec_img)
                    img.thumbnail((800, 800))
                    img_str = img_to_base64(img)
                
                new_data = pd.DataFrame([[rec_date, rec_title, rec_clay, rec_step, rec_note, img_str, rec_mood, rec_type, rec_obj]], 
                                        columns=["날짜", "작품명", "흙", "단계", "내용", "사진", "기분", "작업유형", "기물종류"])
                df = pd.concat([df, new_data], ignore_index=True)
                df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
                st.success("기록되었습니다!")
                st.rerun()
            else:
                st.warning("작품명은 필수입니다.")

# --- [TAB 3: 작품별 모아보기] ---
with tab_project:
    st.subheader("🏺 작품별 히스토리")
    
    if not df.empty:
        # 상태 필터링
        filter_status = st.radio("보기 설정", ["전체", "작업 중", "완성된 작품"], horizontal=True)
        
        # 작품명으로 그룹화
        project_names = df['작품명'].unique()
        
        for name in project_names:
            p_df = df[df['작품명'] == name].sort_values(by='날짜')
            is_finished = "완성" in p_df['단계'].values
            
            # 필터링 조건
            if filter_status == "작업 중" and is_finished: continue
            if filter_status == "완성된 작품" and not is_finished: continue
            
            with st.expander(f"{'✅ ' if is_finished else '🏺 '}{name}"):
                if is_finished:
                    st.markdown("<span class='complete-tag'>완성됨</span>", unsafe_allow_html=True)
                
                st.write(f"**유형:** {p_df['작업유형'].iloc[0]} | **기물:** {p_df['기물종류'].iloc[0]}")
                
                # 해당 작품의 타임라인 표시
                for _, r in p_df.iterrows():
                    st.markdown(f"**{r['날짜']} ({r['단계']})**")
                    if r['내용']: st.caption(r['내용'])
                    if pd.notna(r['사진']) and r['사진'] != "":
                        st.image(base64.b64decode(r['사진']), width=150)
                    st.divider()
    else:
        st.info("기록된 작품이 없습니다.")

# 모바일 하단 여백 (탭 메뉴 때문)
st.markdown("<br><br><br>", unsafe_allow_html=True)
