import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
import base64
from io import BytesIO
from PIL import Image, ImageOps
import calendar
import plotly.graph_objects as go

# --- 1. 페이지 설정 및 디자인 ---
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
    
    /* 탭 메뉴 디자인 */
    .stTabs [data-baseweb="tab-list"] {{ justify-content: space-around; border-bottom: none; }}
    .stTabs [data-baseweb="tab"] {{ font-size: 1.4rem !important; }}

    /* [핵심] 달력 전용 가로 7열 강제 고정 (다른 레이아웃에 영향 없음) */
    div[data-testid="stHorizontalBlock"]:has(button[key^="cal_"]) {{
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 2px !important;
    }}
    div[data-testid="stHorizontalBlock"]:has(button[key^="cal_"]) [data-testid="column"] {{
        flex: 1 1 0% !important;
        min-width: 0px !important;
    }}

    /* 달력 버튼 디자인 */
    .stButton > button[key^="cal_"] {{
        width: 100% !important;
        height: 55px !important;
        padding: 0px !important;
        background-color: white !important;
        color: #CCC !important;
        border: 1px solid #F0F0F0 !important;
        border-radius: 6px !important;
        font-size: 0.7rem !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center;
        justify-content: flex-start;
    }}
    
    /* 기록이 있는 날 버튼 */
    div.has-rec > div > button {{
        background-color: #F9F5F2 !important;
        border: 1px solid #E6DED8 !important;
        color: {MAIN_COLOR} !important;
    }}

    /* 클릭된(활성화된) 날짜 버튼 */
    div.is-active > div > button {{
        background-color: {MAIN_COLOR} !important;
        color: white !important;
        border: 1px solid {MAIN_COLOR} !important;
    }}

    /* 달력 내 아주 작은 썸네일 */
    .cal-img-tiny {{
        width: 25px; height: 25px; object-fit: cover; border-radius: 4px; margin-top: 2px;
    }}

    .summary-box {{ background: #F9F5F2; padding: 12px; border-radius: 12px; border-left: 5px solid {MAIN_COLOR}; margin-top: 10px; line-height: 1.5; font-size: 0.9rem; }}
    .title-text {{ font-size: 1.4em; font-weight: 800; color: #5D574F; margin: 10px 0; }}
    
    /* 상세 페이지 이미지 크기 고정 */
    .detail-img-box img {{ width: 85px !important; height: 85px !important; object-fit: cover; border-radius: 8px; margin-right: 4px; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. 데이터 및 세션 로직 ---
DATA_FILE = "pottery_diary_v4.csv"
MOOD_DICT = {"행복": "😊", "기쁨": "😄", "절망": "😱", "슬픔": "😢", "화이팅": "🔥", "실망": "😞", "감격": "😭"}

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

# 세션 관리
if 'sel_month_idx' not in st.session_state: st.session_state.sel_month_idx = len(month_opts) - 1
if 'active_date' not in st.session_state: st.session_state.active_date = datetime.now().date()

# --- 3. 메뉴 구성 ---
tab_cal, tab_rec, tab_proj, tab_mood, tab_log = st.tabs(["📅", "📝", "🏺", "✨", "📊"])

# --- [TAB 1: 캘린더] ---
with tab_cal:
    # 상단 네비게이션
    n1, n2, n3 = st.columns([1, 5, 1])
    with n1:
        if st.button("◀", key="nav_prev"):
            if st.session_state.sel_month_idx > 0: st.session_state.sel_month_idx -= 1; st.rerun()
    with n2:
        month_str = st.selectbox("달력 선택", month_opts, index=st.session_state.sel_month_idx, label_visibility="collapsed", key="nav_select")
        st.session_state.sel_month_idx = month_opts.index(month_str)
    with n3:
        if st.button("▶", key="nav_next"):
            if st.session_state.sel_month_idx < len(month_opts) - 1: st.session_state.sel_month_idx += 1; st.rerun()

    view_y, view_m = int(month_str[:4]), int(month_str[6:8])
    st.markdown(f"<div class='title-text'>{view_m}월 모아보기</div>", unsafe_allow_html=True)
    
    # 요일 헤더 (가로 고정용 별도 처리)
    h_cols = st.columns(7)
    for i, d in enumerate(["월", "화", "수", "목", "금", "토", "일"]):
        h_cols[i].markdown(f"<div style='text-align:center; font-size:0.7em; color:{MAIN_COLOR}; font-weight:bold;'>{d}</div>", unsafe_allow_html=True)

    # 달력 그리드
    cal_data = calendar.monthcalendar(view_y, view_m)
    work_count = 0
    for week_idx, week in enumerate(cal_data):
        w_cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                w_cols[i].write("")
            else:
                curr_date = date(view_y, view_m, day)
                day_logs = df[df['날짜'] == curr_date]
                has_rec = not day_logs.empty
                if has_rec: work_count += 1
                
                # 버튼 속 이미지 및 뱃지
                label = f"{day}"
                thumb_html = ""
                if has_rec:
                    last_pic = day_logs.iloc[-1]['사진1']
                    if pd.notna(last_pic) and last_pic != "":
                        thumb_html = f'<img src="data:image/jpeg;base64,{last_pic}" class="cal-img-tiny">'
                
                # 스타일 클래스
                cls = ""
                if curr_date == st.session_state.active_date: cls = "is-active"
                elif has_rec: cls = "has-rec"

                with w_cols[i]:
                    st.markdown(f'<div class="{cls}">', unsafe_allow_html=True)
                    if st.button(label, key=f"cal_btn_{curr_date}"):
                        st.session_state.active_date = curr_date
                        st.rerun()
                    # 버튼 내부에 이미지를 넣을 수 없으므로 버튼 아래에 HTML로 썸네일 표시 (클릭은 버튼이 담당)
                    st.markdown(f'<div style="margin-top:-38px; text-align:center; pointer-events:none;">{thumb_html}</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(f"<div class='summary-box'>💡 이번 달은 {work_count}일 작업했어요!</div>", unsafe_allow_html=True)

    # 하단 상세 기록
    st.divider()
    active_logs = df[df['날짜'] == st.session_state.active_date]
    st.markdown(f"### 🏺 {st.session_state.active_date.strftime('%m월 %d일')} 기록")
    if not active_logs.empty:
        for idx, row in active_logs.iterrows():
            st.markdown(f"<div class='summary-box'><b>{MOOD_DICT.get(row['기분'], '')} {row['작품명']}</b> | {row['단계']}<br>{row['내용']}</div>", unsafe_allow_html=True)
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
                new_data = pd.DataFrame([[r_date, r_title, "백자토", "성형", r_note, img_l[0], img_l[1], img_l[2], mood, "물레", "컵"]], columns=df.columns)
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
    if not df.empty: st.write(f"주로 느끼는 기분은 **{df['기분'].mode()[0]}** 입니다.")

with tab_log:
    st.markdown("<div class='title-text'>Dana's Log</div>", unsafe_allow_html=True)
    if not df.empty:
        fig = go.Figure(data=[go.Pie(labels=df['기분'].value_counts().index, values=df['기분'].value_counts().values, hole=.6, marker=dict(colors=PASTEL_COLORS))])
        fig.update_layout(height=280, margin=dict(t=10, b=10, l=10, r=10)); st.plotly_chart(fig, use_container_width=True)

st.markdown("<br><br><br>", unsafe_allow_html=True)
