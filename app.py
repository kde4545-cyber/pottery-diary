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

    /* 모바일 고정 7열 캘린더 (Table 방식) */
    .cal-table {{
        width: 100%;
        table-layout: fixed;
        border-collapse: collapse;
        margin-bottom: 10px;
    }}
    .cal-table th {{
        text-align: center; font-size: 0.7em; color: {MAIN_COLOR}; padding: 5px 0;
    }}
    .cal-table td {{
        border: 1px solid #F2F2F2;
        background: white;
        height: 55px;
        vertical-align: top;
        text-align: center;
        padding: 2px;
        position: relative;
    }}
    .cal-date-num {{ font-size: 0.6em; color: #CCC; display: block; text-align: left; }}
    .has-rec {{ background-color: #F9F5F2 !important; }}
    .cal-thumb {{ width: 30px; height: 30px; object-fit: cover; border-radius: 4px; margin-top: 2px; }}
    .cal-plus {{ position: absolute; bottom: 2px; right: 2px; font-size: 0.5em; color: {MAIN_COLOR}; font-weight: bold; }}
    .is-active-date {{ border: 2px solid {MAIN_COLOR} !important; }}

    .summary-box {{ background: #F9F5F2; padding: 15px; border-radius: 15px; border-left: 5px solid {MAIN_COLOR}; margin-top: 10px; line-height: 1.6; font-size: 0.9rem; }}
    .title-text {{ font-size: 1.4em; font-weight: 800; color: #5D574F; margin-bottom: 10px; }}
    
    /* 상세 페이지 이미지 크기 제한 */
    .detail-img {{ width: 100px; border-radius: 8px; margin-right: 5px; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. 데이터 및 세션 로직 ---
DATA_FILE = "pottery_diary_v4.csv"
MOOD_DICT = {"행복": "😊", "기쁨": "😄", "절망": "😱", "슬픔": "😢", "화이팅": "🔥", "실망": "😞", "감격": "😭"}

if 'sel_month_str' not in st.session_state: st.session_state.sel_month_str = "2026년 04월"
if 'active_day' not in st.session_state: st.session_state.active_day = datetime.now().day

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

# --- [TAB 1: 캘린더 모아보기] ---
with tab_cal:
    # 1. 월 선택 (단일 드롭다운)
    st.session_state.sel_month_str = st.selectbox("달력 이동", month_opts, index=month_opts.index(st.session_state.sel_month_str))
    
    view_y = int(st.session_state.sel_month_str[:4])
    view_m = int(st.session_state.sel_month_str[6:8])
    st.markdown(f"<div class='title-text'>{view_m}월 모아보기</div>", unsafe_allow_html=True)
    
    # 2. 캘린더 (Table 방식 - 깨짐 없음)
    cal_data = calendar.monthcalendar(view_y, view_m)
    html = '<table class="cal-table"><thead><tr>'
    for d in ["월", "화", "수", "목", "금", "토", "일"]: html += f'<th>{d}</th>'
    html += '</tr></thead><tbody>'
    
    for week in cal_data:
        html += '<tr>'
        for day in week:
            if day == 0: html += '<td></td>'
            else:
                curr_date = date(view_y, view_m, day)
                day_logs = df[df['날짜'] == curr_date]
                has_rec = not day_logs.empty
                
                td_cls = "has-rec" if has_rec else ""
                if day == st.session_state.active_day: td_cls += " is-active-date"
                
                img_html = ""
                if has_rec:
                    last_pic = day_logs.iloc[-1]['사진1']
                    if pd.notna(last_pic) and last_pic != "":
                        img_html = f'<img src="data:image/jpeg;base64,{last_pic}" class="cal-thumb">'
                    if len(day_logs) > 1: img_html += f'<span class="cal-plus">+{len(day_logs)-1}</span>'
                
                html += f'<td class="{td_cls}"><span class="cal-date-num">{day}</span>{img_html}</td>'
        html += '</tr>'
    st.markdown(html + '</tbody></table>', unsafe_allow_html=True)

    # 3. 상세 보기 날짜 선택 (숫자로 입력받아 레이아웃 보호)
    st.divider()
    st.write("🔍 **기록을 볼 날짜를 입력하세요**")
    st.session_state.active_day = st.number_input("날짜(일) 선택", min_value=1, max_value=31, value=st.session_state.active_day)
    
    active_date = date(view_y, view_m, st.session_state.active_day)
    active_logs = df[df['날짜'] == active_date]
    
    st.markdown(f"### 🏺 {view_m}월 {st.session_state.active_day}일 기록")
    if not active_logs.empty:
        for _, row in active_logs.iterrows():
            st.markdown(f"<div class='summary-box'><b>{MOOD_DICT.get(row['기분'], '')} {row['작품명']}</b> | {row['단계']}<br>{row['내용']}</div>", unsafe_allow_html=True)
            # 이미지 크기 제한해서 띄우기
            img_cols = st.columns(3)
            for i, c in enumerate(['사진1', '사진2', '사진3']):
                if pd.notna(row[c]) and row[c] != "":
                    img_cols[i].image(base64.b64decode(row[c]), width=100) # 너비 100px로 제한
    else:
        st.caption("기록이 없습니다. 날짜 숫자를 바꿔보세요.")

# --- 나머지 탭은 안정화된 이전 코드 유지 ---
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
        r_imgs = st.file_uploader("사진(최대 3장)", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
        r_note = st.text_area("메모")
        if st.form_submit_button("기록 저장하기"):
            if r_title:
                img_l = [process_img(r_imgs[i]) if i < len(r_imgs) else "" for i in range(3)]
                new_r = pd.DataFrame([[r_date, r_title, r_clay, r_step, r_note, img_l[0], img_l[1], img_l[2], mood, r_type, r_obj]], columns=df.columns)
                df = pd.concat([df, new_r], ignore_index=True); save_data(df); st.balloons(); st.rerun()

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
                if st.button(f"기록 삭제", key=f"del_{i}"): df = df[df['작품명'] != t]; save_data(df); st.rerun()

with tab_mood:
    st.markdown("<div class='title-text'>기분 조각들</div>", unsafe_allow_html=True)
    m_v = int(st.session_state.sel_month_str[6:8])
    f_df = df[pd.to_datetime(df['날짜']).dt.month == m_v]
    if not f_df.empty:
        st.write(f"이번 달은 **{f_df['기분'].mode()[0]}** 기분이 가장 많았어요!")

with tab_log:
    st.markdown("<div class='title-text'>Dana's Log</div>", unsafe_allow_html=True)
    if not df.empty:
        mood_counts = df['기분'].value_counts()
        fig = go.Figure(data=[go.Pie(labels=mood_counts.index, values=mood_counts.values, hole=.6, marker=dict(colors=PASTEL_COLORS))])
        fig.update_layout(height=280, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)

st.markdown("<br><br><br>", unsafe_allow_html=True)
