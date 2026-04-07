import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
import base64
from io import BytesIO
from PIL import Image, ImageOps
import calendar
import plotly.graph_objects as go

# --- 1. 페이지 설정 및 모바일 강제 7열 디자인 ---
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
    
    /* [핵심] 모바일에서 st.columns가 세로로 꺾이는 현상 방지 */
    [data-testid="column"] {{
        flex: 1 1 0% !important;
        min-width: 0px !important;
    }}
    [data-testid="stHorizontalBlock"] {{
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 2px !important;
    }}

    /* 메뉴 탭 크기 */
    .stTabs [data-baseweb="tab-list"] button div {{ font-size: 1.4rem !important; }}

    /* 캘린더 칸 디자인 */
    .cal-box {{
        width: 100%;
        aspect-ratio: 1 / 1.2;
        background: white;
        border: 1px solid #F0F0F0;
        border-radius: 6px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: flex-start;
        padding: 2px;
        font-size: 0.7em;
        position: relative;
    }}
    .has-rec-box {{ background-color: #F9F5F2 !important; border: 1px solid #E6DED8 !important; }}
    .is-active-box {{ border: 2px solid {MAIN_COLOR} !important; background-color: #FFF9F8 !important; }}
    
    .cal-img {{ width: 90%; aspect-ratio: 1/1; object-fit: cover; border-radius: 4px; margin-top: 2px; }}
    .cal-num {{ font-size: 0.8em; color: #BBB; align-self: flex-start; padding-left: 2px; }}
    .cal-plus {{ position: absolute; bottom: 1px; right: 2px; font-size: 0.7em; color: {MAIN_COLOR}; font-weight: bold; }}

    .summary-box {{ background: #F9F5F2; padding: 15px; border-radius: 15px; border-left: 5px solid {MAIN_COLOR}; margin-top: 10px; line-height: 1.6; }}
    .title-text {{ font-size: 1.5em; font-weight: 800; color: #5D574F; margin-bottom: 10px; }}
    .stButton>button {{ width: 100%; border-radius: 12px; height: 3em; background-color: {MAIN_COLOR}; color: white; font-weight: bold; border: none; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. 데이터 및 세션 로직 ---
DATA_FILE = "pottery_diary_v4.csv"
MOOD_DICT = {"행복": "😊", "기쁨": "😄", "절망": "😱", "슬픔": "😢", "화이팅": "🔥", "실망": "😞", "감격": "😭"}

if 'sel_month_str' not in st.session_state: st.session_state.sel_month_str = "2026년 04월"
if 'active_date' not in st.session_state: st.session_state.active_date = datetime.now().date()

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

# 년월 리스트 (25년 01월 ~ 26년 04월)
month_opts = []
for y in [2025, 2026]:
    for m in range(1, 13):
        if y == 2026 and m > 4: break
        month_opts.append(f"{y}년 {m:02d}월")

# --- 3. 메뉴 구성 ---
tab_cal, tab_rec, tab_proj, tab_mood, tab_log = st.tabs(["📅", "📝", "🏺", "✨", "📊"])

# --- [TAB 1: 캘린더] ---
with tab_cal:
    # 네비게이션
    nav_c1, nav_c2, nav_c3 = st.columns([1, 5, 1])
    with nav_c2:
        st.session_state.sel_month_str = st.selectbox("월 선택", month_opts, index=month_opts.index(st.session_state.sel_month_str), label_visibility="collapsed")
    with nav_c1:
        if st.button("◀", key="p"):
            idx = month_opts.index(st.session_state.sel_month_str)
            if idx > 0: st.session_state.sel_month_str = month_opts[idx-1]; st.rerun()
    with nav_c3:
        if st.button("▶", key="n"):
            idx = month_opts.index(st.session_state.sel_month_str)
            if idx < len(month_opts)-1: st.session_state.sel_month_str = month_opts[idx+1]; st.rerun()

    view_y, view_m = int(st.session_state.sel_month_str[:4]), int(st.session_state.sel_month_str[6:8])
    st.markdown(f"<div class='title-text'>{view_m}월 모아보기</div>", unsafe_allow_html=True)
    
    # 요일 헤더
    h_cols = st.columns(7)
    for i, d in enumerate(["월", "화", "수", "목", "금", "토", "일"]):
        h_cols[i].markdown(f"<div style='text-align:center; font-size:0.7em; color:{MAIN_COLOR}; font-weight:bold;'>{d}</div>", unsafe_allow_html=True)

    # 캘린더 그리드
    cal_data = calendar.monthcalendar(view_y, view_m)
    for week in cal_data:
        w_cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0: w_cols[i].write("")
            else:
                curr_date = date(view_y, view_m, day)
                day_logs = df[df['날짜'] == curr_date]
                has_rec = not day_logs.empty
                is_active = curr_date == st.session_state.active_date
                
                box_cls = "has-rec-box" if has_rec else ""
                active_cls = "is-active-box" if is_active else ""
                
                img_html = ""
                plus_html = f'<div class="cal-plus">+{len(day_logs)-1}</div>' if len(day_logs) > 1 else ""
                if has_rec:
                    last_pic = day_logs.iloc[-1]['사진1']
                    if pd.notna(last_pic) and last_pic != "":
                        img_html = f'<img src="data:image/jpeg;base64,{last_pic}" class="cal-img">'
                
                # HTML과 버튼을 조합하여 클릭 가능하게 구성
                with w_cols[i]:
                    # 칸 전체를 감싸는 클릭 영역 (Streamlit 버튼 활용)
                    if st.button(f"{day}", key=f"d{curr_date}", help=f"{curr_date}"):
                        st.session_state.active_date = curr_date; st.rerun()
                    # 버튼 아래에 시각적 요소 배치
                    st.markdown(f"""
                        <div class="cal-box {box_cls} {active_cls}" style="margin-top:-35px; pointer-events:none;">
                            <div class="cal-num">{day}</div>
                            {img_html}
                            {plus_html}
                        </div>
                    """, unsafe_allow_html=True)

    # 상세 보기
    st.divider()
    active_logs = df[df['날짜'] == st.session_state.active_date]
    st.markdown(f"### 🏺 {st.session_state.active_date.strftime('%m월 %d일')} 기록")
    if not active_logs.empty:
        for _, row in active_logs.iterrows():
            st.markdown(f"<div class='summary-box'><b>{MOOD_DICT.get(row['기분'], '')} {row['작품명']}</b> | {row['단계']}<br>{row['내용']}</div>", unsafe_allow_html=True)
            p_cols = st.columns(3)
            for i, c in enumerate(['사진1', '사진2', '사진3']):
                if pd.notna(row[c]) and row[c] != "": p_cols[i].image(base64.b64decode(row[c]), use_container_width=True)
    else: st.caption("날짜를 눌러 상세 내용을 확인하세요.")

# --- 나머지 탭 (동일 유지) ---
with tab_rec:
    st.markdown("<div class='title-text'>오늘의 작업 기록</div>", unsafe_allow_html=True)
    with st.form("rec_f", clear_on_submit=True):
        mood = st.radio("기분", list(MOOD_DICT.keys()), horizontal=True, format_func=lambda x: MOOD_DICT[x], label_visibility="collapsed")
        c1, c2 = st.columns(2)
        with c1: r_date = st.date_input("날짜", datetime.now().date())
        with c2: r_title = st.text_input("작품명")
        c3, c4 = st.columns(2)
        with c3: r_type = st.selectbox("유형", ["물레", "핸드빌딩", "기타"])
        with c4: r_clay = st.selectbox("흙", ["백자토", "산백토", "조형토", "청자토", "옹기토", "기타"])
        r_obj = st.selectbox("기물", ["컵", "접시", "그릇", "항아리", "고블렛", "면기", "오브제", "기타"])
        r_step = st.select_slider("단계", options=["성형", "건조", "초벌", "시유", "완성"])
        r_imgs = st.file_uploader("사진(3장)", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
        r_note = st.text_area("메모")
        if st.form_submit_button("저장"):
            if r_title:
                img_l = [process_img(r_imgs[i]) if i < len(r_imgs) else "" for i in range(3)]
                new_r = pd.DataFrame([[r_date, r_title, r_clay, r_step, r_note, img_l[0], img_l[1], img_l[2], mood, r_type, r_obj]], columns=df.columns)
                df = pd.concat([df, new_r], ignore_index=True); save_data(df); st.balloons(); st.rerun()

with tab_proj:
    st.markdown("<div class='title-text'>작품 모아보기</div>", unsafe_allow_html=True)
    p_f = st.radio("필터", ["전체", "작업중", "완성"], horizontal=True, label_visibility="collapsed")
    if not df.empty:
        u_t = df['작품명'].unique()
        display_t = [t for t in u_t if (p_f=="전체") or (p_f=="작업중" and "완성" not in df[df['작품명']==t]['단계'].values) or (p_f=="완성" and "완성" in df[df['작품명']==t]['단계'].values)]
        cols = st.columns(2)
        for i, t in enumerate(display_t):
            p_l = df[df['작품명'] == t].sort_values(by='날짜')
            rep = p_l[p_l['사진1'] != ""].iloc[-1] if not p_l[p_l['사진1'] != ""].empty else None
            with cols[i%2]:
                src = f"data:image/jpeg;base64,{rep['사진1']}" if rep is not None else ""
                st.markdown(f'<div style="background:white; border-radius:12px; overflow:hidden; box-shadow:0 2px 8px rgba(0,0,0,0.05); margin-bottom:10px;"><div style="width:100%; aspect-ratio:1/1; overflow:hidden;">{"<img src=\'"+src+"\' style=\'width:100%; height:100%; object-fit:cover;\'>" if src else "No Photo"}</div><div style="padding:5px; font-weight:bold; font-size:0.8em;">🏺 {t}</div></div>', unsafe_allow_html=True)
                with st.expander("삭제"):
                    for ri, rw in p_l.iterrows():
                        if st.button(f"지우기 ({rw['단계']})", key=f"d{ri}"): df=df.drop(index=ri); save_data(df); st.rerun()

with tab_mood:
    st.markdown("<div class='title-text'>기분 조각들</div>", unsafe_allow_html=True)
    mode = st.radio("기준", ["월별", "작품별"], horizontal=True)
    if mode == "월별":
        m_v = int(st.session_state.sel_month_str[6:8])
        f_df = df[pd.to_datetime(df['날짜']).dt.month == m_v]; d_n = f"{m_v}월"
    else:
        p_v = st.selectbox("작품", sorted(df['작품명'].unique()) if not df.empty else ["없음"])
        f_df = df[df['작품명'] == p_v]; d_n = p_v
    if not f_df.empty:
        cnts = f_df['기분'].value_counts()
        st.markdown(f"<div class='summary-box'>✨ {d_n}은 주로 <b>'{cnts.idxmax()}'</b>였네요!</div>", unsafe_allow_html=True)

with tab_log:
    st.markdown("<div class='title-text'>DANA의 기록 요약</div>", unsafe_allow_html=True)
    if not df.empty:
        done = df[df['단계'] == "완성"]['작품명'].nunique()
        st.markdown(f"<div class='summary-box'>총 <b>{done}개</b> 완성!</div>", unsafe_allow_html=True)
        fig = go.Figure(data=[go.Pie(labels=df['기분'].value_counts().index, values=df['기분'].value_counts().values, hole=.6, marker=dict(colors=PASTEL_COLORS))])
        fig.update_layout(height=280, margin=dict(t=10, b=10, l=10, r=10), legend=dict(orientation="h", y=-0.2))
        st.plotly_chart(fig, use_container_width=True)

st.markdown("<br><br><br>", unsafe_allow_html=True)
