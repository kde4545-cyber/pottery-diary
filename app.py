import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from io import BytesIO
from PIL import Image
import calendar
import plotly.graph_objects as go

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="Dana's Pottery Log", layout="centered")

st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Pretendard', sans-serif !important;
        letter-spacing: -0.05em !important;
        background-color: #fcfaf8;
    }

    /* 감성적인 요약 카드 디자인 */
    .dana-report-card {
        background: white;
        padding: 25px;
        border-radius: 25px;
        border: none;
        box-shadow: 0px 10px 30px rgba(141, 110, 99, 0.08);
        margin-bottom: 25px;
        text-align: center;
    }
    .dana-highlight { color: #8d6e63; font-weight: 800; font-size: 1.2em; }
    .dana-sentence { font-size: 1.1em; line-height: 1.8; color: #444; word-break: keep-all; }

    /* 캘린더 디자인 */
    .cal-day {
        min-height: 55px; padding: 5px; border-radius: 12px;
        background-color: #ffffff; border: 1px solid #f2f2f2;
        display: flex; flex-direction: column; align-items: center;
    }
    .cal-date { font-size: 0.7em; color: #ccc; }
    .cal-sticker { font-size: 1.3em; margin-top: 2px; }
    .today { border: 1.5px solid #8d6e63 !important; background-color: #fff9f8 !important; }

    /* 메뉴(탭) 디자인 */
    .stTabs [data-baseweb="tab-list"] { justify-content: space-around; border-bottom: none; gap: 5px; }
    .stTabs [data-baseweb="tab"] { font-size: 0.85em !important; font-weight: 600 !important; color: #999; }
    .stTabs [aria-selected="true"] { color: #8d6e63 !important; border-bottom: 2px solid #8d6e63 !important; }

    .stButton>button { width: 100%; border-radius: 15px; height: 3.5em; background-color: #8d6e63; color: white; font-weight: bold; border: none; box-shadow: 0 4px 10px rgba(141, 110, 99, 0.2); }
    .log-card { background-color: #ffffff; padding: 20px; border-radius: 20px; border: 1px solid #f5f5f5; margin-top: 15px; }
    </style>
    """, unsafe_allow_html=True)

# 데이터 및 설정
DATA_FILE = "pottery_diary_v2.csv"
MOOD_DICT = {"행복": "😊", "기쁨": "😄", "절망": "😱", "슬픔": "😢", "화이팅": "🔥", "실망": "😞", "감격": "😭"}
POTTERY_COLORS = ['#D5BDAF', '#E3D5CA', '#F5EBE0', '#D6CCC2', '#EDEDE9', '#A28B78', '#E6BAA3']

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

df = load_data()

# 탭 메뉴명 통일
tab_cal, tab_rec, tab_proj, tab_mood, tab_log = st.tabs(["📅 Dana's Calendar", "📝 Dana's Record", "🏺 Dana's Project", "✨ Dana's Mood", "📊 Dana's Log"])

# --- [TAB 1: Dana's Calendar] ---
with tab_cal:
    st.subheader(f"🏺 {datetime.now().year}년 {datetime.now().month}월")
    today = datetime.now().date()
    cal_month = calendar.monthcalendar(today.year, today.month)
    cols = st.columns(7)
    for i, d in enumerate(["월", "화", "수", "목", "금", "토", "일"]):
        cols[i].markdown(f"<div style='text-align:center; color:#8d6e63; font-weight:bold; font-size:0.7em;'>{d}</div>", unsafe_allow_html=True)
    for week in cal_month:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0: cols[i].write("")
            else:
                this_date = datetime(today.year, today.month, day).date()
                day_records = df[df['날짜'] == this_date]
                sticker = MOOD_DICT.get(day_records.iloc[-1]['기분'], "") if not day_records.empty else ""
                is_today = "today" if this_date == today else ""
                cols[i].markdown(f"""<div class="cal-day {is_today}"><div class="cal-date">{day}</div><div class="cal-sticker">{sticker}</div></div>""", unsafe_allow_html=True)
    st.divider()
    view_date = st.date_input("선택 날짜 상세", today)
    logs = df[df['날짜'] == view_date]
    for _, row in logs.iterrows():
        st.markdown(f"""<div class="log-card"><b>{MOOD_DICT.get(row['기분'], '')} {row['작품명']}</b> | {row['단계']}<p style='margin-top:10px; font-size:0.9em;'>{row['내용']}</p></div>""", unsafe_allow_html=True)
        if pd.notna(row['사진']) and row['사진'] != "": st.image(base64.b64decode(row['사진']), use_container_width=True)

# --- [TAB 2: Dana's Record] ---
with tab_rec:
    st.subheader("오늘의 작업 기록")
    with st.form("record_form"):
        selected_mood = st.radio("기분 선택", options=list(MOOD_DICT.keys()), format_func=lambda x: f"{MOOD_DICT[x]} {x}", horizontal=True, label_visibility="collapsed")
        c1, c2 = st.columns(2)
        with c1: rec_date = st.date_input("날짜", datetime.now().date())
        with c2: rec_title = st.text_input("작품명")
        c3, c4 = st.columns(2)
        with c3: rec_type = st.selectbox("유형", ["물레", "핸드빌딩", "기타"])
        with c4: rec_clay = st.selectbox("흙", ["백자토", "산백토", "조형토", "청자토", "옹기토", "기타"])
        rec_obj = st.selectbox("기물", ["컵", "접시", "그릇", "항아리", "고블렛", "면기", "오브제", "기타"])
        rec_step = st.select_slider("단계", options=["성형", "건조", "초벌", "시유", "완성"])
        rec_img = st.file_uploader("사진", type=["jpg", "png", "jpeg"])
        rec_note = st.text_area("작업 메모")
        if st.form_submit_button("기록 저장하기"):
            if rec_title:
                img_str = img_to_base64(Image.open(rec_img).convert("RGB").resize((800,800))) if rec_img else ""
                new_data = pd.DataFrame([[rec_date, rec_title, rec_clay, rec_step, rec_note, img_str, selected_mood, rec_type, rec_obj]], columns=["날짜", "작품명", "흙", "단계", "내용", "사진", "기분", "작업유형", "기물종류"])
                df = pd.concat([df, new_data], ignore_index=True)
                df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
                st.success("Dana의 기록이 저장되었습니다!"); st.rerun()

# --- [TAB 3: Dana's Project] ---
with tab_proj:
    st.subheader("🏺 작품별 히스토리")
    if not df.empty:
        filter_status = st.radio("필터", ["전체", "작업 중", "완성됨"], horizontal=True)
        for name in df['작품명'].unique():
            p_df = df[df['작품명'] == name].sort_values(by='날짜')
            finished = "완성" in p_df['단계'].values
            if (filter_status == "작업 중" and finished) or (filter_status == "완성됨" and not finished): continue
            with st.expander(f"{'✅' if finished else '🏺'} {name}"):
                for _, r in p_df.iterrows():
                    st.write(f"**{r['날짜']}** [{r['단계']}]\n\n{r['내용']}")
                    if pd.notna(r['사진']) and r['사진'] != "": st.image(base64.b64decode(r['사진']), use_container_width=True)
    else: st.info("기록이 없습니다.")

# --- [TAB 4: Dana's Mood] ---
with tab_mood:
    st.subheader("✨ 기분 조각들")
    if not df.empty:
        counts = df['기분'].value_counts()
        m_cols = st.columns(3)
        for i, (m, e) in enumerate(MOOD_DICT.items()):
            c = counts.get(m, 0)
            with m_cols[i % 3]:
                st.markdown(f"""<div style="text-align:center; padding:15px; background:white; border-radius:15px; border:1px solid #f0f0f0; margin-bottom:10px;"><div style="font-size:2em;">{e}</div><div style="font-size:0.8em; color:#666;">{m}</div><div style="font-weight:800; color:#8d6e63;">{c}개</div></div>""", unsafe_allow_html=True)

# --- [TAB 5: Dana's Log (통계 요약)] ---
with tab_log:
    st.subheader("📊 Dana's Analysis Report")
    
    if not df.empty:
        # 데이터 계산
        total_projects = df['작품명'].nunique()
        finished_projects = df[df['단계'] == "완성"]['작품명'].nunique()
        ongoing_projects = total_projects - finished_projects
        
        top_mood = df['기분'].mode()[0] if not df['기분'].empty else "-"
        top_obj = df['기물종류'].mode()[0] if not df['기물종류'].empty else "-"

        # 감성 요약 카드
        st.markdown(f"""
        <div class="dana-report-card">
            <p class="dana-sentence">
                지금까지 Dana는...<br>
                총 <span class="dana-highlight">{finished_projects}개</span>의 작품을 완성했고,<br>
                지금은 <span class="dana-highlight">{ongoing_projects}개</span>의 작품을 정성껏 만드는 중이에요. ✨<br><br>
                주로 흙을 만질 때 <span class="dana-highlight">'{top_mood}' {MOOD_DICT.get(top_mood, '')}</span> 기분이고,<br>
                제일 만들기 좋아하는 건 <span class="dana-highlight">'{top_obj}'</span>이에요! 🏺
            </p>
        </div>
        """, unsafe_allow_html=True)

        # 도넛 그래프 함수
        def draw_donut(labels, values, title):
            fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.5, 
                                        textinfo='label+value',
                                        marker=dict(colors=POTTERY_COLORS))])
            fig.update_layout(showlegend=False, margin=dict(t=30, b=0, l=0, r=0), height=250, 
                              annotations=[dict(text=title, x=0.5, y=0.5, font_size=12, showarrow=False)])
            st.plotly_chart(fig, use_container_width=True)

        # 그래프 섹션
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            mood_counts = df['기분'].value_counts()
            draw_donut(mood_counts.index, mood_counts.values, "기분 비중")
        
        with col_g2:
            type_counts = df['작업유형'].value_counts()
            draw_donut(type_counts.index, type_counts.values, "작업 유형")
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        obj_counts = df['기물종류'].value_counts()
        draw_donut(obj_counts.index, obj_counts.values, "기물 종류")
        
    else:
        st.info("데이터가 충분히 쌓이면 Dana만의 리포트가 완성됩니다.")

st.markdown("<br><br><br>", unsafe_allow_html=True)
