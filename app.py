import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
import base64
from io import BytesIO
from PIL import Image
import calendar
import plotly.graph_objects as go

# --- 1. 페이지 설정 및 파스텔 디자인 ---
st.set_page_config(page_title="Dana's Pottery Log", layout="centered")

PASTEL_COLORS = ['#FFB7B2', '#FFDAC1', '#E2F0CB', '#B5EAD7', '#C7CEEA', '#F3FFE3', '#F9E2AF']
MAIN_COLOR = '#B09B90'

st.markdown(f"""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    html, body, [data-testid="stAppViewContainer"] {{
        font-family: 'Pretendard', sans-serif !important;
        letter-spacing: -0.05em !important;
        background-color: #FDFBF9;
    }}
    .stTabs [data-baseweb="tab-list"] {{ justify-content: space-around; border-bottom: none; }}
    .stTabs [data-baseweb="tab"] {{ font-size: 1.3em !important; }}
    .dana-card {{ background: white; padding: 20px; border-radius: 20px; box-shadow: 0px 8px 20px rgba(0,0,0,0.03); margin-bottom: 20px; }}
    .summary-box {{ background: #F9F5F2; padding: 15px; border-radius: 15px; border-left: 5px solid {MAIN_COLOR}; margin-top: 10px; }}
    .highlight {{ color: #D4A373; font-weight: 800; font-size: 1.1em; }}
    .title-text {{ font-size: 1.5em; font-weight: 800; color: #5D574F; margin-bottom: 20px; }}
    .cal-day {{ min-height: 60px; padding: 5px; border-radius: 12px; background-color: white; border: 1px solid #F0F0F0; display: flex; flex-direction: column; align-items: center; }}
    .today {{ border: 2px solid {MAIN_COLOR} !important; background-color: #FFF9F8 !important; }}
    .stButton>button {{ width: 100%; border-radius: 15px; height: 3.5em; background-color: {MAIN_COLOR}; color: white; font-weight: bold; border: none; }}
    /* 삭제 버튼 전용 스타일 */
    .delete-btn button {{ background-color: #FFB7B2 !important; height: 2em !important; font-size: 0.8em !important; margin-top: 10px !important; }}
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

# --- [TAB 1: 0월 모아보기] ---
with tab_cal:
    col_y, col_m = st.columns([1, 1])
    with col_y: sel_year = st.selectbox("년도", [2024, 2025, 2026], index=2)
    with col_m: sel_month = st.selectbox("월", list(range(1, 13)), index=datetime.now().month-1)
    st.markdown(f"<div class='title-text'>{sel_month}월 모아보기</div>", unsafe_allow_html=True)
    cal = calendar.monthcalendar(sel_year, sel_month)
    cols = st.columns(7)
    for i, d in enumerate(["월", "화", "수", "목", "금", "토", "일"]):
        cols[i].markdown(f"<div style='text-align:center; font-size:0.8em; color:#999;'>{d}</div>", unsafe_allow_html=True)
    month_moods, work_days = [], 0
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0: cols[i].write("")
            else:
                curr_date = date(sel_year, sel_month, day)
                day_logs = df[df['날짜'] == curr_date]
                sticker = MOOD_DICT.get(day_logs.iloc[-1]['기분'], "") if not day_logs.empty else ""
                if not day_logs.empty:
                    month_moods.append(day_logs.iloc[-1]['기분'])
                    work_days += 1
                is_today = "today" if curr_date == datetime.now().date() else ""
                cols[i].markdown(f"""<div class="cal-day {is_today}"><div style="font-size:0.7em; color:#ccc;">{day}</div><div style="font-size:1.4em;">{sticker}</div></div>""", unsafe_allow_html=True)
    st.markdown("<div class='summary-box'>", unsafe_allow_html=True)
    st.markdown(f"**💡 {sel_month}월 요약**")
    if work_days > 0:
        top_m = max(set(month_moods), key=month_moods.count)
        st.write(f"이번 달은 총 **{work_days}일** 흙을 만졌어요. 가장 많이 느낀 기분은 **'{top_m}' {MOOD_DICT[top_m]}**이네요!")
    else: st.write("아직 이번 달 기록이 없어요.")
    st.markdown("</div>", unsafe_allow_html=True)

# --- [TAB 2: 오늘의 작업 기록] ---
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
        r_img = st.file_uploader("사진 촬영/업로드", type=["jpg", "png", "jpeg"])
        r_note = st.text_area("메모", placeholder="어떤 작업을 했나요?")
        if st.form_submit_button("기록 저장하기"):
            if r_title:
                img_s = img_to_base(Image.open(r_img).convert("RGB").resize((800, 800))) if r_img else ""
                new_row = pd.DataFrame([[r_date, r_title, r_clay, r_step, r_note, img_s, sel_mood, r_type, r_obj]], columns=df.columns)
                df = pd.concat([df, new_row], ignore_index=True); save_data(df)
                st.balloons(); st.success("Dana의 소중한 기록이 저장되었습니다!"); st.rerun()
            else: st.error("작품명을 적어주세요!")

# --- [TAB 3: 작품 모아보기 (삭제 기능 추가)] ---
with tab_proj:
    st.markdown("<div class='title-text'>작품 모아보기</div>", unsafe_allow_html=True)
    p_filter = st.radio("상태 구분", ["전체", "작업중", "완성"], horizontal=True)
    if not df.empty:
        unique_titles = df['작품명'].unique()
        display_titles = []
        for t in unique_titles:
            p_logs = df[df['작품명'] == t]
            is_done = "완성" in p_logs['단계'].values
            if (p_filter == "작업중" and is_done) or (p_filter == "완성" and not is_done): continue
            display_titles.append(t)
        cols = st.columns(2)
        for idx, t in enumerate(display_titles):
            p_logs = df[df['작품명'] == t].sort_values(by=['날짜'], ascending=True)
            rep_row = p_logs[p_logs['사진'] != ""].iloc[-1] if not p_logs[p_logs['사진'] != ""].empty else None
            with cols[idx % 2]:
                with st.expander(f"{'✅' if '완성' in p_logs['단계'].values else '🏺'} {t}"):
                    if rep_row is not None: st.image(base64.b64decode(rep_row['사진']), use_container_width=True)
                    st.write("---")
                    for r_idx, row in p_logs.iterrows():
                        st.caption(f"{row['날짜']} | {row['단계']}")
                        if row['내용']: st.write(f"💬 {row['내용']}")
                        if row['사진']: st.image(base64.b64decode(row['사진']), width=100)
                        
                        # --- 삭제 기능 구현 ---
                        with st.popover("🗑️ 삭제"):
                            st.warning("정말 삭제할까요?")
                            if st.button("예, 삭제합니다", key=f"del_{r_idx}"):
                                df = df.drop(index=r_idx)
                                save_data(df)
                                st.rerun()
                    st.write("---")
    else: st.info("아직 등록된 작품이 없습니다.")

# --- [TAB 4: 기분 조각들] ---
with tab_mood:
    st.markdown("<div class='title-text'>기분 조각들</div>", unsafe_allow_html=True)
    col_m1, col_m2 = st.columns(2)
    with col_m1: m_month = st.selectbox("월 선택", list(range(1, 13)), index=datetime.now().month-1)
    with col_m2: m_proj = st.selectbox("작품별", ["전체보기"] + list(df['작품명'].unique()))
    m_df = df.copy(); m_df['월'] = pd.to_datetime(m_df['날짜']).dt.month
    m_df = m_df[m_df['월'] == m_month]
    if m_proj != "전체보기": m_df = m_df[m_df['작품명'] == m_proj]
    if not m_df.empty:
        mood_counts = m_df['기분'].value_counts()
        m_cols = st.columns(4)
        for i, (m, emoji) in enumerate(MOOD_DICT.items()):
            count = mood_counts.get(m, 0)
            with m_cols[i % 4]: st.markdown(f"<div style='text-align:center;'><div style='font-size:1.5em;'>{emoji}</div><div style='font-size:0.7em;'>{m}</div><div style='font-weight:bold;'>{count}</div></div>", unsafe_allow_html=True)
    else: st.info("기록이 없습니다.")

# --- [TAB 5: DANA의 기록 요약] ---
with tab_log:
    st.markdown("<div class='title-text'>DANA의 기록 요약</div>", unsafe_allow_html=True)
    if not df.empty:
        total_p = df['작품명'].nunique(); done_p = df[df['단계'] == "완성"]['작품명'].nunique(); ing_p = total_p - done_p
        top_m = df['기분'].mode()[0] if not df['기분'].empty else "-"; top_o = df['기물종류'].mode()[0] if not df['기물종류'].empty else "-"
        st.markdown(f"""<div class="dana-card"><p style='line-height:2; font-size:1.1em;'>지금까지 Dana님은...<br>총 <span class="highlight">{done_p}개</span>의 작품을 완성하고,<br>지금은 <span class="highlight">{ing_p}개</span>의 아이들을 빚고 있어요. 🕊️<br>기분 좋은 흙의 기운 속에 주로 <span class="highlight">'{top_m}' {MOOD_DICT.get(top_m, '')}</span> 마음이었고,<br>가장 애정을 담아 만든 기물은 <span class="highlight">'{top_o}'</span>이에요!</p></div>""", unsafe_allow_html=True)
        def draw_pastel_donut(labels, values, title):
            fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.6, marker=dict(colors=PASTEL_COLORS))])
            fig.update_layout(showlegend=True, margin=dict(t=30, b=0, l=0, r=0), height=300, legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
            st.plotly_chart(fig, use_container_width=True)
        draw_pastel_donut(df['기분'].value_counts().index, df['기분'].value_counts().values, "기분 비중")
        draw_pastel_donut(df['기물종류'].value_counts().index, df['기물종류'].value_counts().values, "기물 비중")
    else: st.info("데이터가 쌓이면 리포트가 생성됩니다.")

st.markdown("<br><br><br>", unsafe_allow_html=True)
