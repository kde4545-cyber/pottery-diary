import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
import base64
from io import BytesIO
from PIL import Image, ImageOps
import calendar
import plotly.graph_objects as go

# --- 1. 페이지 설정 및 디자인 (가장 안정적인 Pretendard) ---
st.set_page_config(page_title="Dana's Pottery Log", layout="centered")

PASTEL_COLORS = ['#FFB7B2', '#FFDAC1', '#E2F0CB', '#B5EAD7', '#C7CEEA', '#F3FFE3', '#F9E2AF']
MAIN_COLOR = '#B09B90'

st.markdown(f"""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    html, body, [data-testid="stAppViewContainer"] {{
        font-family: 'Pretendard', sans-serif !important;
        letter-spacing: -0.03em !important;
        background-color: #FDFBF9;
    }}
    .stTabs [data-baseweb="tab-list"] {{ justify-content: space-around; border-bottom: none; }}
    .stTabs [data-baseweb="tab"] {{ font-size: 1.3em !important; padding: 10px 0px; }}

    /* [고정] 7열 달력 디자인 (Table 방식은 절대 깨지지 않음) */
    .cal-table {{
        width: 100%;
        border-collapse: collapse;
        table-layout: fixed; /* 모든 칸 너비 강제 고정 */
    }}
    .cal-table th {{
        text-align: center; font-size: 0.7em; color: {MAIN_COLOR}; padding: 8px 0; font-weight: bold;
    }}
    .cal-table td {{
        border: 1px solid #F2F2F2;
        background: white;
        height: 65px;
        vertical-align: top;
        padding: 2px;
        text-align: center;
        position: relative;
    }}
    .cal-date-num {{ font-size: 0.6em; color: #CCC; display: block; text-align: left; padding-left: 2px; }}
    
    /* 기록 있는 날 음영 및 썸네일 */
    .has-rec {{ background-color: #F9F5F2 !important; }}
    .cal-thumb {{ width: 35px; height: 35px; object-fit: cover; border-radius: 5px; margin-top: 2px; }}
    .cal-plus {{ position: absolute; bottom: 2px; right: 2px; font-size: 0.5em; color: {MAIN_COLOR}; font-weight: bold; }}
    
    .summary-box {{ background: #F9F5F2; padding: 15px; border-radius: 15px; border-left: 5px solid {MAIN_COLOR}; margin-top: 10px; line-height: 1.6; }}
    .title-text {{ font-size: 1.5em; font-weight: 800; color: #5D574F; margin-bottom: 10px; }}
    .stButton>button {{ width: 100%; border-radius: 12px; height: 3.5em; background-color: {MAIN_COLOR}; color: white; font-weight: bold; border: none; }}
    
    /* 갤러리 정방형 디자인 */
    .gallery-img-container {{ width: 100%; aspect-ratio: 1/1; overflow: hidden; border-radius: 12px; background-color: #F8F8F8; }}
    .gallery-img-container img {{ width: 100%; height: 100%; object-fit: cover; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. 데이터 및 네비게이션 로직 ---
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

# 년월 리스트 (25년 1월 ~ 26년 4월)
month_opts = []
for y in [2025, 2026]:
    for m in range(1, 13):
        if y == 2026 and m > 4: break
        month_opts.append(f"{y}년 {m:02d}월")

if 'sel_month_idx' not in st.session_state: st.session_state.sel_month_idx = len(month_opts) - 1
if 'active_date' not in st.session_state: st.session_state.active_date = datetime.now().date()

# --- 3. 메뉴 구성 ---
tab_cal, tab_rec, tab_proj, tab_mood, tab_log = st.tabs(["📅", "📝", "🏺", "✨", "📊"])

# --- [TAB 1: 0월 모아보기] ---
with tab_cal:
    # 1. 상단 네비게이션 (화살표 + 통합 드롭다운)
    nav_c1, nav_c2, nav_c3 = st.columns([1, 6, 1])
    with nav_c1:
        if st.button("◀", key="prev"):
            if st.session_state.sel_month_idx > 0:
                st.session_state.sel_month_idx -= 1; st.rerun()
    with nav_c2:
        month_str = st.selectbox("월", month_opts, index=st.session_state.sel_month_idx, label_visibility="collapsed")
        st.session_state.sel_month_idx = month_opts.index(month_str)
    with nav_c3:
        if st.button("▶", key="next"):
            if st.session_state.sel_month_idx < len(month_opts) - 1:
                st.session_state.sel_month_idx += 1; st.rerun()

    view_y, view_m = int(month_str[:4]), int(month_str[6:8])
    st.markdown(f"<div class='title-text'>{view_m}월 모아보기</div>", unsafe_allow_html=True)
    
    # 2. 캘린더 (Table 방식 - 모바일에서 절대 안 깨짐)
    cal_data = calendar.monthcalendar(view_y, view_m)
    html = '<table class="cal-table"><thead><tr>'
    for d_n in ["월", "화", "수", "목", "금", "토", "일"]: html += f'<th>{d_n}</th>'
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
                thumb_html = ""
                if has_rec:
                    last_pic = day_logs.iloc[-1]['사진1']
                    if pd.notna(last_pic) and last_pic != "":
                        thumb_html = f'<img src="data:image/jpeg;base64,{last_pic}" class="cal-thumb">'
                    if len(day_logs) > 1: thumb_html += f'<span class="cal-plus">+{len(day_logs)-1}</span>'
                
                html += f'<td class="{td_cls}"><span class="cal-date-num">{day}</span>{thumb_html}</td>'
        html += '</tr>'
    st.markdown(html + '</tbody></table>', unsafe_allow_html=True)

    # 3. 하단 상세 보기 (날짜 선택은 여기서!)
    st.divider()
    st.write("🔍 **기록을 볼 날짜를 선택하세요**")
    st.session_state.active_date = st.date_input("날짜 선택", st.session_state.active_date, label_visibility="collapsed")
    
    active_logs = df[df['날짜'] == st.session_state.active_date]
    st.markdown(f"### 🏺 {st.session_state.active_date.strftime('%m월 %d일')} 기록")
    if not active_logs.empty:
        for idx, row in active_logs.iterrows():
            st.markdown(f"<div class='summary-box'><b>{MOOD_DICT.get(row['기분'], '')} {row['작품명']}</b> | {row['단계']}<br>{row['내용']}</div>", unsafe_allow_html=True)
            img_cols = st.columns(3)
            for i, c in enumerate(['사진1', '사진2', '사진3']):
                if pd.notna(row[c]) and row[c] != "": img_cols[i].image(base64.b64decode(row[c]), use_container_width=True)
            with st.popover("🗑️ 기록 삭제"):
                if st.button("정말 삭제할까요?", key=f"del_{idx}"): df = df.drop(index=idx); save_data(df); st.rerun()
    else: st.caption("기록이 없습니다. 달력에서 음영 처리된 날짜를 골라보세요.")

# --- 나머지 탭 (기존 안정화된 기능 유지) ---
with tab_rec:
    st.markdown("<div class='title-text'>오늘의 작업 기록</div>", unsafe_allow_html=True)
    with st.form("rec_f", clear_on_submit=True):
        mood = st.radio("기분", list(MOOD_DICT.keys()), horizontal=True, format_func=lambda x: MOOD_DICT[x], label_visibility="collapsed")
        c1, c2 = st.columns(2)
        with c1: r_date = st.date_input("날짜", datetime.now().date())
        with c2: r_title = st.text_input("작품명")
        r_imgs = st.file_uploader("사진(최대 3장)", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
        r_note = st.text_area("메모")
        if st.form_submit_button("기록 저장하기"):
            if r_title:
                img_l = [process_img(r_imgs[i]) if i < len(r_imgs) else "" for i in range(3)]
                new_data = pd.DataFrame([[r_date, r_title, "백자토", "성형", r_note, img_l[0], img_l[1], img_l[2], mood, "물레", "컵"]], columns=df.columns)
                df = pd.concat([df, new_data], ignore_index=True); save_data(df); st.balloons(); st.rerun()

with tab_proj:
    st.markdown("<div class='title-text'>작품 모아보기</div>", unsafe_allow_html=True)
    if not df.empty:
        u_t = df['작품명'].unique(); cols = st.columns(2)
        for i, t in enumerate(u_t):
            p_l = df[df['작품명'] == t].sort_values(by='날짜')
            rep = p_l[p_l['사진1'] != ""].iloc[-1] if not p_l[p_l['사진1'] != ""].empty else None
            with cols[i%2]:
                src = f"data:image/jpeg;base64,{rep['사진1']}" if rep is not None else ""
                st.markdown(f'<div style="background:white; border-radius:12px; overflow:hidden; box-shadow:0 2px 8px rgba(0,0,0,0.05); margin-bottom:10px;"><div style="width:100%; aspect-ratio:1/1; overflow:hidden;">{"<img src=\'"+src+"\' style=\'width:100%; height:100%; object-fit:cover;\'>" if src else "No Photo"}</div><div style="padding:5px; font-weight:bold; font-size:0.85em;">🏺 {t}</div></div>', unsafe_allow_html=True)

with tab_mood:
    st.markdown("<div class='title-text'>기분 조각들</div>", unsafe_allow_html=True)
    if not df.empty:
        cnts = df['기분'].value_counts()
        st.write(f"가장 많이 느낀 기분은 **{cnts.idxmax()}** 입니다!")

with tab_log:
    st.markdown("<div class='title-text'>Dana's Log</div>", unsafe_allow_html=True)
    if not df.empty:
        done = df[df['단계'] == "완성"]['작품명'].nunique()
        st.markdown(f"<div class='summary-box'>총 <b>{done}개</b> 완성! ✨</div>", unsafe_allow_html=True)
        fig = go.Figure(data=[go.Pie(labels=df['기분'].value_counts().index, values=df['기분'].value_counts().values, hole=.6, marker=dict(colors=PASTEL_COLORS))])
        fig.update_layout(height=280, margin=dict(t=10, b=10, l=10, r=10), legend=dict(orientation="h", y=-0.2))
        st.plotly_chart(fig, use_container_width=True)

st.markdown("<br><br><br>", unsafe_allow_html=True)
