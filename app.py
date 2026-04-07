import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
import base64
from io import BytesIO
from PIL import Image
import calendar
import plotly.graph_objects as go

# --- 1. 페이지 설정 및 디자인 ---
st.set_page_config(page_title="Dana's Pottery Log", layout="centered")

PASTEL_COLORS = ['#FFB7B2', '#FFDAC1', '#E2F0CB', '#B5EAD7', '#C7CEEA', '#F3FFE3', '#F9E2AF']
MAIN_COLOR = '#B09B90'

# CSS 스타일 정의
st.markdown(f"""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    html, body, [data-testid="stAppViewContainer"] {{
        font-family: 'Pretendard', sans-serif !important;
        letter-spacing: -0.05em !important;
        background-color: #FDFBF9;
    }}
    .stTabs [data-baseweb="tab-list"] {{ justify-content: space-around; border-bottom: none; }}
    .stTabs [data-baseweb="tab"] {{ font-size: 1.3em !important; padding: 10px 0px; }}

    /* 캘린더 전용 스타일 */
    .calendar-container {{
        width: 100%;
        margin: 0 auto;
    }}
    .calendar-grid {{
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 5px;
        width: 100%;
    }}
    .cal-header-item {{
        text-align: center;
        font-size: 0.8em;
        font-weight: bold;
        color: {MAIN_COLOR};
        padding: 5px 0;
    }}
    .cal-cell {{
        background: white;
        border: 1px solid #F0F0F0;
        border-radius: 8px;
        aspect-ratio: 1 / 1.2;
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 4px 2px;
        min-height: 55px;
    }}
    .cal-date-num {{
        font-size: 0.7em;
        color: #CCC;
        margin-bottom: 2px;
    }}
    .cal-mood-sticker {{
        font-size: 1.3em;
    }}
    .is-today {{
        border: 1.5px solid {MAIN_COLOR} !important;
        background-color: #FFF9F8 !important;
    }}

    .dana-card {{ background: white; padding: 20px; border-radius: 20px; box-shadow: 0px 8px 20px rgba(0,0,0,0.03); margin-bottom: 20px; }}
    .summary-box {{ background: #F9F5F2; padding: 15px; border-radius: 15px; border-left: 5px solid {MAIN_COLOR}; margin-top: 10px; }}
    .highlight {{ color: #D4A373; font-weight: 800; font-size: 1.1em; }}
    .title-text {{ font-size: 1.5em; font-weight: 800; color: #5D574F; margin-bottom: 20px; }}
    .stButton>button {{ width: 100%; border-radius: 15px; height: 3.5em; background-color: {MAIN_COLOR}; color: white; font-weight: bold; border: none; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. 데이터 로직 ---
DATA_FILE = "pottery_diary_v3.csv"
MOOD_DICT = {"행복": "😊", "기쁨": "😄", "절망": "😱", "슬픔": "😢", "화이팅": "🔥", "실망": "😞", "감격": "😭"}

def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df['날짜'] = pd.to_datetime(df['날짜']).dt.date
        return df
    return pd.DataFrame(columns=["날짜", "작품명", "흙", "단계", "내용", "사진", "기분", "작업유형", "기물종류"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')

def img_to_base(image):
    buffered = BytesIO()
    image.save(buffered, format="JPEG", quality=70)
    return base64.b64encode(buffered.getvalue()).decode()

df = load_data()

# --- 3. 메뉴 구성 ---
tab_cal, tab_rec, tab_proj, tab_mood, tab_log = st.tabs(["📅", "📝", "🏺", "✨", "📊"])

# --- [TAB 1: 캘린더] ---
with tab_cal:
    col_y, col_m = st.columns([1, 1])
    with col_y: sel_year = st.selectbox("년도", [2024, 2025, 2026], index=2)
    with col_m: sel_month = st.selectbox("월", list(range(1, 13)), index=datetime.now().month-1)
    
    st.markdown(f"<div class='title-text'>{sel_month}월 모아보기</div>", unsafe_allow_html=True)
    
    # 캘린더 HTML 생성 시작
    cal_html = '<div class="calendar-container"><div class="calendar-grid">'
    
    # 헤더
    for d in ["월", "화", "수", "목", "금", "토", "일"]:
        cal_html += f'<div class="cal-header-item">{d}</div>'
    
    # 날짜 채우기
    cal_data = calendar.monthcalendar(sel_year, sel_month)
    month_moods, work_days = [], 0
    today_date = datetime.now().date()

    for week in cal_data:
        for day in week:
            if day == 0:
                cal_html += '<div></div>'
            else:
                curr_date = date(sel_year, sel_month, day)
                day_logs = df[df['날짜'] == curr_date]
                sticker = MOOD_DICT.get(day_logs.iloc[-1]['기분'], "") if not day_logs.empty else ""
                if not day_logs.empty:
                    month_moods.append(day_logs.iloc[-1]['기분'])
                    work_days += 1
                
                today_class = "is-today" if curr_date == today_date else ""
                cal_html += f'''
                    <div class="cal-cell {today_class}">
                        <div class="cal-date-num">{day}</div>
                        <div class="cal-mood-sticker">{sticker}</div>
                    </div>
                '''
    cal_html += '</div></div>'
    
    # 완성된 달력 HTML 출력 (매우 중요: unsafe_allow_html=True)
    st.markdown(cal_html, unsafe_allow_html=True)

    # 요약 박스
    st.markdown("<div class='summary-box'>", unsafe_allow_html=True)
    st.markdown(f"**💡 {sel_month}월 요약**")
    if work_days > 0:
        top_m = max(set(month_moods), key=month_moods.count)
        st.write(f"이번 달은 총 **{work_days}일** 흙을 만졌어요. 가장 많이 느낀 기분은 **'{top_m}' {MOOD_DICT[top_m]}**이네요!")
    else: st.write("아직 이번 달 기록이 없어요.")
    st.markdown("</div>", unsafe_allow_html=True)

# --- 나머지 탭은 이전과 동일 (코드 중략 가능하나 확인을 위해 포함) ---

# --- [TAB 2: 기록하기] ---
with tab_rec:
    st.markdown("<div class='title-text'>오늘의 작업 기록</div>", unsafe_allow_html=True)
    with st.form("record_form", clear_on_submit=True):
        sel_mood = st.radio("오늘 기분", list(MOOD_DICT.keys()), horizontal=True, format_func=lambda x: MOOD_DICT[x], label_visibility="collapsed")
        c1, c2 = st.columns(2)
        with c1: r_date = st.date_input("날짜", datetime.now().date())
        with c2: r_title = st.text_input("작품명", placeholder="작품 이름")
        c3, c4 = st.columns(2)
        with c3: r_type = st.selectbox("유형", ["물레", "핸드빌딩", "기타"])
        with c4: r_clay = st.selectbox("흙", ["백자토", "산백토", "조형토", "청자토", "옹기토", "기타"])
        r_obj = st.selectbox("기물", ["컵", "접시", "그릇", "항아리", "고블렛", "면기", "오브제", "기타"])
        r_step = st.select_slider("단계", options=["성형", "건조", "초벌", "시유", "완성"])
        r_img = st.file_uploader("사진", type=["jpg", "png", "jpeg"])
        r_note = st.text_area("메모")
        if st.form_submit_button("기록 저장하기"):
            if r_title:
                img_s = img_to_base(Image.open(r_img).convert("RGB").resize((800, 800))) if r_img else ""
                new_row = pd.DataFrame([[r_date, r_title, r_clay, r_step, r_note, img_s, sel_mood, r_type, r_obj]], columns=df.columns)
                df = pd.concat([df, new_row], ignore_index=True); save_data(df)
                st.balloons(); st.success("기록 완료!"); st.rerun()
            else: st.error("작품명을 적어주세요!")

# --- [TAB 3: 작품 모아보기] ---
with tab_proj:
    st.markdown("<div class='title-text'>작품 모아보기</div>", unsafe_allow_html=True)
    p_filter = st.radio("상태 구분", ["전체", "작업중", "완성"], horizontal=True)
    if not df.empty:
        unique_titles = df['작품명'].unique()
        display_titles = [t for t in unique_titles if (p_filter=="전체") or (p_filter=="작업중" and "완성" not in df[df['작품명']==t]['단계'].values) or (p_filter=="완성" and "완성" in df[df['작품명']==t]['단계'].values)]
        
        proj_cols = st.columns(2)
        for idx, t in enumerate(display_titles):
            p_logs = df[df['작품명'] == t].sort_values(by=['날짜'])
            rep_row = p_logs[p_logs['사진'] != ""].iloc[-1] if not p_logs[p_logs['사진'] != ""].empty else None
            with proj_cols[idx % 2]:
                with st.expander(f"{'✅' if '완성' in p_logs['단계'].values else '🏺'} {t}"):
                    if rep_row is not None: st.image(base64.b64decode(rep_row['사진']), use_container_width=True)
                    for r_idx, row in p_logs.iterrows():
                        st.caption(f"{row['날짜']} | {row['단계']}")
                        if row['사진']: st.image(base64.b64decode(row['사진']), width=80)
                        if st.button("삭제", key=f"del_{r_idx}"):
                            df = df.drop(index=r_idx); save_data(df); st.rerun()
    else: st.info("기록이 없습니다.")

# --- [TAB 4: 기분 조각들] ---
with tab_mood:
    st.markdown("<div class='title-text'>기분 조각들</div>", unsafe_allow_html=True)
    m_month = st.selectbox("월 선택", list(range(1, 13)), index=datetime.now().month-1, key="mood_month")
    m_df = df.copy(); m_df['월'] = pd.to_datetime(m_df['날짜']).dt.month
    m_df = m_df[m_df['월'] == m_month]
    if not m_df.empty:
        mood_counts = m_df['기분'].value_counts()
        m_grid = st.columns(4)
        for i, (m, emoji) in enumerate(MOOD_DICT.items()):
            count = mood_counts.get(m, 0)
            with m_grid[i % 4]: st.markdown(f"<div style='text-align:center;'>{emoji}<br><small>{m}</small><br><b>{count}</b></div>", unsafe_allow_html=True)
    else: st.info("기록이 없습니다.")

# --- [TAB 5: 요약 리포트] ---
with tab_log:
    st.markdown("<div class='title-text'>DANA의 기록 요약</div>", unsafe_allow_html=True)
    if not df.empty:
        total_p = df['작품명'].nunique(); done_p = df[df['단계'] == "완성"]['작품명'].nunique()
        st.markdown(f'<div class="dana-card">총 <span class="highlight">{done_p}개</span> 완성!</div>', unsafe_allow_html=True)
        mood_counts = df['기분'].value_counts()
        fig = go.Figure(data=[go.Pie(labels=mood_counts.index, values=mood_counts.values, hole=.6, marker=dict(colors=PASTEL_COLORS))])
        fig.update_layout(showlegend=True, margin=dict(t=10, b=10, l=10, r=10), height=300)
        st.plotly_chart(fig, use_container_width=True)
