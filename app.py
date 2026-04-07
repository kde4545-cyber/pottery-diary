import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
import base64
from io import BytesIO
from PIL import Image, ImageOps
import calendar
import plotly.graph_objects as go

# --- 1. 페이지 설정 및 모바일 7열 고정 레이아웃 ---
st.set_page_config(page_title="Dana's Pottery Log", layout="centered")

MAIN_COLOR = '#B09B90'
PASTEL_COLORS = ['#FFB7B2', '#FFDAC1', '#E2F0CB', '#B5EAD7', '#C7CEEA', '#F3FFE3', '#F9E2AF']

st.markdown(f"""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    html, body, [data-testid="stAppViewContainer"] {{
        font-family: 'Pretendard', sans-serif !important;
        letter-spacing: -0.03em !important;
        background-color: #FDFBF9;
    }}
    
    /* [핵심] 모바일에서 7개의 컬럼이 세로로 꺾이지 않게 강제 고정 */
    [data-testid="stHorizontalBlock"] {{
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 2px !important;
    }}
    [data-testid="column"] {{
        flex: 1 1 0% !important;
        min-width: 0px !important;
    }}

    /* 캘린더 날짜 버튼 스타일 */
    .stButton > button {{
        width: 100% !important;
        padding: 5px 0 !important;
        height: 55px !important;
        background-color: white !important;
        color: #BBB !important;
        border: 1px solid #F0F0F0 !important;
        border-radius: 6px !important;
        font-size: 0.75rem !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
    }}
    
    /* 기록 있는 날 음영 처리 */
    div.has-rec-btn > div > button {{
        background-color: #F9F5F2 !important;
        border-color: #E6DED8 !important;
        color: {MAIN_COLOR} !important;
        font-weight: bold !important;
    }}

    /* 선택된 날짜 강조 */
    div.active-date-btn > div > button {{
        border: 2px solid {MAIN_COLOR} !important;
        background-color: #FFF9F8 !important;
    }}

    .summary-box {{ background: #F9F5F2; padding: 12px; border-radius: 15px; border-left: 5px solid {MAIN_COLOR}; margin-top: 10px; line-height: 1.6; font-size: 0.9rem; }}
    .title-text {{ font-size: 1.4em; font-weight: 800; color: #5D574F; margin: 10px 0; }}
    
    /* 상세 보기 썸네일 */
    .detail-thumb {{ width: 80px; height: 80px; object-fit: cover; border-radius: 8px; margin: 2px; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. 데이터 및 세션 로직 ---
DATA_FILE = "pottery_diary_v4.csv"
MOOD_DICT = {"행복": "😊", "기쁨": "😄", "절망": "😱", "슬픔": "😢", "화이팅": "🔥", "실망": "😞", "감격": "😭"}

# 데이터 로드
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE); df['날짜'] = pd.to_datetime(df['날짜']).dt.date
        return df
    return pd.DataFrame(columns=["날짜", "작품명", "흙", "단계", "내용", "사진1", "사진2", "사진3", "기분", "작업유형", "기물종류"])

def save_data(df): df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')

def process_img(upload_file):
    if upload_file is None: return ""
    img = Image.open(upload_file).convert("RGB")
    img = ImageOps.fit(img, (800, 800), Image.Resampling.LANCZOS)
    buf = BytesIO(); img.save(buf, format="JPEG", quality=80)
    return base64.b64encode(buf.getvalue()).decode()

df = load_data()

# 년월 리스트 생성 (25년 01월 ~ 26년 04월)
month_opts = []
for y in [2025, 2026]:
    for m in range(1, 13):
        if y == 2026 and m > 4: break
        month_opts.append(f"{y}년 {m:02d}월")

# 세션 상태 초기화
if 'sel_month_idx' not in st.session_state: 
    st.session_state.sel_month_idx = len(month_opts) - 1 # 현재 달(26년 4월)
if 'clicked_date' not in st.session_state: 
    st.session_state.clicked_date = datetime.now().date()

# --- 3. 메뉴 구성 ---
tab_cal, tab_rec, tab_proj, tab_mood, tab_log = st.tabs(["📅", "📝", "🏺", "✨", "📊"])

# --- [TAB 1: 캘린더 모아보기] ---
with tab_cal:
    # 1. 상단 네비게이션 (화살표 + 드롭다운)
    nav_c1, nav_c2, nav_c3 = st.columns([1, 6, 1])
    
    with nav_c1:
        if st.button("◀", key="prev_btn"):
            if st.session_state.sel_month_idx > 0:
                st.session_state.sel_month_idx -= 1; st.rerun()
                
    with nav_c2:
        selected_month_str = st.selectbox("월", month_opts, index=st.session_state.sel_month_idx, label_visibility="collapsed")
        st.session_state.sel_month_idx = month_opts.index(selected_month_str)
        
    with nav_c3:
        if st.button("▶", key="next_btn"):
            if st.session_state.sel_month_idx < len(month_opts) - 1:
                st.session_state.sel_month_idx += 1; st.rerun()

    view_y = int(selected_month_str[:4])
    view_m = int(selected_month_str[6:8])
    st.markdown(f"<div class='title-text'>{view_m}월 모아보기</div>", unsafe_allow_html=True)
    
    # 2. 요일 헤더
    h_cols = st.columns(7)
    for i, d_n in enumerate(["월", "화", "수", "목", "금", "토", "일"]):
        h_cols[i].markdown(f"<div style='text-align:center; font-size:0.7em; color:{MAIN_COLOR}; font-weight:bold;'>{d_n}</div>", unsafe_allow_html=True)

    # 3. 캘린더 인터랙티브 그리드
    cal_data = calendar.monthcalendar(view_y, view_m)
    for week in cal_data:
        w_cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                w_cols[i].write("")
            else:
                curr_date = date(view_y, view_m, day)
                day_logs = df[df['날짜'] == curr_date]
                has_rec = not day_logs.empty
                is_active = curr_date == st.session_state.clicked_date
                
                # 버튼 레이블 (날짜 + 이모지)
                label = f"{day}"
                if has_rec:
                    last_mood = day_logs.iloc[-1]['기분']
                    label = f"{day}\n{MOOD_DICT.get(last_mood, '🏺')}"

                # 스타일링 클래스
                cls = ""
                if is_active: cls = "active-date-btn"
                elif has_rec: cls = "has-rec-btn"

                with w_cols[i]:
                    st.markdown(f'<div class="{cls}">', unsafe_allow_html=True)
                    if st.button(label, key=f"d_{curr_date}"):
                        st.session_state.clicked_date = curr_date
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

    # 4. 하단 상세 보기 (날짜 클릭 시 자동으로 갱신)
    st.divider()
    detail_logs = df[df['날짜'] == st.session_state.clicked_date]
    st.markdown(f"### 🏺 {st.session_state.clicked_date.strftime('%m월 %d일')} 기록")
    
    if not detail_logs.empty:
        for idx, row in detail_logs.iterrows():
            st.markdown(f"""
            <div class="summary-box">
                <b>{MOOD_DICT.get(row['기분'], '')} {row['작품명']}</b> | {row['단계']}<br>
                <small>{row['작업유형']} · {row['기물종류']} · {row['흙']}</small><br>
                {row['내용']}
            </div>
            """, unsafe_allow_html=True)
            # 이미지 크기 제한 (너비 100px)
            img_cols = st.columns(3)
            for i, c in enumerate(['사진1', '사진2', '사진3']):
                if pd.notna(row[c]) and row[c] != "":
                    img_cols[i].image(base64.b64decode(row[c]), use_container_width=True)
    else:
        st.caption("기록이 없는 날짜입니다. 달력의 날짜를 클릭해 보세요.")

# --- 나머지 탭 (안정화 버전 유지) ---
with tab_rec:
    st.markdown("<div class='title-text'>오늘의 작업 기록</div>", unsafe_allow_html=True)
    with st.form("rec_form", clear_on_submit=True):
        mood = st.radio("기분", list(MOOD_DICT.keys()), horizontal=True, format_func=lambda x: MOOD_DICT[x], label_visibility="collapsed")
        c1, c2 = st.columns(2)
        with c1: r_date = st.date_input("날짜", datetime.now().date())
        with c2: r_title = st.text_input("작품명")
        r_imgs = st.file_uploader("사진(3장)", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
        r_note = st.text_area("메모")
        if st.form_submit_button("저장하기"):
            if r_title:
                img_l = [process_img(r_imgs[i]) if i < len(r_imgs) else "" for i in range(3)]
                # 기본값 채우기 위해 df 로드 후 결합
                new_data = pd.DataFrame([[r_date, r_title, "백자토", "성형", r_note, img_l[0], img_l[1], img_l[2], mood, "물레", "컵"]], 
                                        columns=df.columns)
                df = pd.concat([df, new_data], ignore_index=True); save_data(df); st.balloons(); st.rerun()

with tab_proj:
    st.markdown("<div class='title-text'>작품 모아보기</div>", unsafe_allow_html=True)
    if not df.empty:
        u_t = df['작품명'].unique()
        cols = st.columns(2)
        for i, t in enumerate(u_t):
            p_l = df[df['작품명'] == t].sort_values(by='날짜')
            rep = p_l[p_l['사진1'] != ""].iloc[-1] if not p_l[p_l['사진1'] != ""].empty else None
            with cols[i%2]:
                src = f"data:image/jpeg;base64,{rep['사진1']}" if rep is not None else ""
                st.markdown(f'<div style="background:white; border-radius:12px; overflow:hidden; box-shadow:0 2px 8px rgba(0,0,0,0.05); margin-bottom:10px;"><div style="width:100%; aspect-ratio:1/1; overflow:hidden;">{"<img src=\'"+src+"\' style=\'width:100%; height:100%; object-fit:cover;\'>" if src else "No Photo"}</div><div style="padding:5px; font-weight:bold; font-size:0.85em;">🏺 {t}</div></div>', unsafe_allow_html=True)
                if st.button("삭제", key=f"del_{i}"): df = df[df['작품명'] != t]; save_data(df); st.rerun()

with tab_mood:
    st.markdown("<div class='title-text'>기분 조각들</div>", unsafe_allow_html=True)
    if not df.empty: st.write(f"가장 많이 느낀 기분은 **{df['기분'].mode()[0]}**입니다.")

with tab_log:
    st.markdown("<div class='title-text'>Dana's Log</div>", unsafe_allow_html=True)
    if not df.empty:
        fig = go.Figure(data=[go.Pie(labels=df['기분'].value_counts().index, values=df['기분'].value_counts().values, hole=.6, marker=dict(colors=PASTEL_COLORS))])
        fig.update_layout(height=280, margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig, use_container_width=True)

st.markdown("<br><br><br>", unsafe_allow_html=True)
