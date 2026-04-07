import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
import base64
from io import BytesIO
from PIL import Image, ImageOps
import calendar
import plotly.graph_objects as go

# --- 1. 페이지 설정 및 디자인 (안정적인 Pretendard) ---
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
    
    /* 상단 메뉴바 균등 분할 */
    .stTabs [data-baseweb="tab-list"] {{
        display: flex !important;
        justify-content: space-around !important;
        width: 100% !important;
        border-bottom: none !important;
    }}
    .stTabs [data-baseweb="tab"] {{
        flex-grow: 1 !important;
        text-align: center !important;
    }}
    .stTabs [data-baseweb="tab-list"] button div {{
        font-size: 1.4rem !important;
    }}

    /* 7열 고정 달력 디자인 (모바일 절대 고정) */
    .cal-table {{
        width: 100%; border-collapse: collapse; table-layout: fixed; margin-bottom: 10px;
    }}
    .cal-table th {{
        text-align: center; font-size: 0.75em; color: {MAIN_COLOR}; padding: 8px 0; font-weight: bold;
    }}
    .cal-table td {{ 
        border: 1px solid #F2F2F2; background: white; height: 65px; 
        vertical-align: top; padding: 4px; text-align: center; position: relative;
    }}
    .cal-date-num {{ font-size: 0.7em; color: #CCC; display: block; text-align: left; padding-left: 2px; }}
    .has-rec {{ background-color: #F9F5F2 !important; }}
    .cal-thumb {{ width: 32px; height: 32px; object-fit: cover; border-radius: 4px; margin-top: 2px; }}
    .cal-plus {{ position: absolute; bottom: 2px; right: 2px; font-size: 0.6em; color: {MAIN_COLOR}; font-weight: bold; }}

    /* 카드 및 요약 박스 */
    .summary-box {{ background: #F9F5F2; padding: 15px; border-radius: 15px; border-left: 5px solid {MAIN_COLOR}; margin-top: 10px; line-height: 1.6; }}
    .dana-card {{ background: white; padding: 20px; border-radius: 20px; box-shadow: 0px 8px 20px rgba(0,0,0,0.03); margin-bottom: 20px; }}
    .title-text {{ font-size: 1.5em; font-weight: 800; color: #5D574F; margin-bottom: 15px; }}
    .highlight {{ color: #D4A373; font-weight: 800; font-size: 1.15em; }}

    /* 이미지 갤러리 정방형 그리드 (작품 모아보기용) */
    .proj-grid-container {{
        width: 100%; aspect-ratio: 1/1; overflow: hidden; border-radius: 8px; background-color: #F8F8F8; margin-top: 5px;
    }}
    .proj-grid-container img {{ width: 100%; height: 100%; object-fit: cover; }}
    
    .stButton>button {{ width: 100%; border-radius: 12px; height: 3.5em; background-color: {MAIN_COLOR}; color: white; font-weight: bold; border: none; }}
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

# 년월 리스트 (25년 01월 ~ 26년 04월)
month_opts = [f"{y}년 {m:02d}월" for y in [2025, 2026] for m in range(1, 13) if not (y == 2026 and m > 4)]
if 'sel_month_idx' not in st.session_state: st.session_state.sel_month_idx = len(month_opts) - 1

# --- 3. 메뉴 구성 ---
tabs = st.tabs(["📅", "📜", "📝", "🏺", "✨", "📊"])
tab_cal, tab_list, tab_rec, tab_proj, tab_mood, tab_log = tabs

# --- [TAB 1: 📅 월간 모아보기] ---
with tab_cal:
    # 수정 1: 네비게이션 버튼을 드롭다운 양옆으로 배치
    nav_col1, nav_col2, nav_col3 = st.columns([1, 4, 1])
    with nav_col1:
        if st.button("◀", key="cal_prev"):
            if st.session_state.sel_month_idx > 0:
                st.session_state.sel_month_idx -= 1; st.rerun()
    with nav_col2:
        month_str = st.selectbox("월", month_opts, index=st.session_state.sel_month_idx, label_visibility="collapsed")
        st.session_state.sel_month_idx = month_opts.index(month_str)
    with nav_col3:
        if st.button("▶", key="cal_next"):
            if st.session_state.sel_month_idx < len(month_opts) - 1:
                st.session_state.sel_month_idx += 1; st.rerun()

    view_y, view_m = int(month_str[:4]), int(month_str[6:8])
    st.markdown(f"<div class='title-text'>{view_m}월 모아보기</div>", unsafe_allow_html=True)
    
    cal_data = calendar.monthcalendar(view_y, view_m)
    html_cal = '<table class="cal-table"><thead><tr>'
    for d_n in ["월", "화", "수", "목", "금", "토", "일"]: html_cal += f'<th>{d_n}</th>'
    html_cal += '</tr></thead><tbody>'
    for week in cal_data:
        html_cal += '<tr>'
        for day in week:
            if day == 0: html_cal += '<td></td>'
            else:
                curr_date = date(view_y, view_m, day)
                logs = df[df['날짜'] == curr_date]
                td_cls = "has-rec" if not logs.empty else ""
                thumb = f'<img src="data:image/jpeg;base64,{logs.iloc[-1]["사진1"]}" class="cal-thumb">' if not logs.empty and pd.notna(logs.iloc[-1]['사진1']) else ""
                plus = f'<span class="cal-plus">+{len(logs)-1}</span>' if len(logs) > 1 else ""
                html_cal += f'<td class="{td_cls}"><span class="cal-date-num">{day}</span>{thumb}{plus}</td>'
        html_cal += '</tr>'
    st.markdown(html_cal + '</tbody></table>', unsafe_allow_html=True)

# --- [TAB 2: 📜 기록 모아보기] ---
with tab_list:
    st.markdown("<div class='title-text'>기록 모아보기</div>", unsafe_allow_html=True)
    if not df.empty:
        sorted_df = df.sort_values(by='날짜', ascending=False)
        for idx, row in sorted_df.iterrows():
            # 수정 2: 이미지는 클릭 시 펼쳐지는 expander 형태로 변경
            with st.expander(f"🏺 {row['날짜']} | {row['작품명']} ({row['단계']})"):
                st.write(f"**기분:** {MOOD_DICT.get(row['기분'], '')} | **유형:** {row['작업유형']} | **기물:** {row['기물종류']}")
                st.write(f"**메모:** {row['내용']}")
                i_cols = st.columns(3)
                for i, c in enumerate(['사진1', '사진2', '사진3']):
                    if pd.notna(row[c]) and row[c] != "": i_cols[i].image(base64.b64decode(row[c]), use_container_width=True)
                if st.button("🗑️ 삭제", key=f"del_list_{idx}"): df = df.drop(index=idx); save_data(df); st.rerun()
    else: st.info("기록이 없습니다.")

# --- [TAB 3: 📝 오늘의 작업 기록] ---
with tab_rec:
    st.markdown("<div class='title-text'>오늘의 작업 기록</div>", unsafe_allow_html=True)
    with st.form("rec_form", clear_on_submit=True):
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

# --- [TAB 4: 🏺 작품 모아보기] ---
with tab_proj:
    st.markdown("<div class='title-text'>작품 모아보기</div>", unsafe_allow_html=True)
    # 수정 3: 제목 상단, 3x3 그리드 형태로 변경
    if not df.empty:
        u_t = df['작품명'].unique()[::-1] # 최근 작업 순
        cols = st.columns(3)
        for i, t in enumerate(u_t):
            p_l = df[df['작품명'] == t].sort_values(by='날짜')
            rep = p_l[p_l['사진1'] != ""].iloc[-1] if not p_l[p_l['사진1'] != ""].empty else None
            with cols[i % 3]:
                st.markdown(f"<div style='text-align:center; font-weight:bold; font-size:0.8em; white-space:nowrap; overflow:hidden;'>{t}</div>", unsafe_allow_html=True)
                src = f"data:image/jpeg;base64,{rep['사진1']}" if rep is not None else ""
                st.markdown(f'<div class="proj-grid-container">{"<img src=\'"+src+"\'>" if src else "<div style=\'padding:35% 0; color:#ccc; font-size:0.7em;\'>No Pic</div>"}</div>', unsafe_allow_html=True)
                st.write("") # 간격
    else: st.info("기록이 없습니다.")

# --- [TAB 5: ✨ 기분 조각들] ---
with tab_mood:
    st.markdown("<div class='title-text'>기분 조각들</div>", unsafe_allow_html=True)
    # 수정 4: 월별 기준에서도 월 선택 복원
    mood_mode = st.radio("기준", ["월별", "작품별"], horizontal=True)
    if mood_mode == "월별":
        m_val = st.selectbox("기분 분석 월 선택", list(range(1, 13)), index=view_m-1)
        f_df = df[pd.to_datetime(df['날짜']).dt.month == m_val]; d_n = f"{m_val}월"
    else:
        p_val = st.selectbox("작품 선택", sorted(df['작품명'].unique()))
        f_df = df[df['작품명'] == p_val]; d_n = p_val
        # 작품별 대표 이미지 복원
        if not f_df.empty and f_df.iloc[-1]['사진1'] != "":
            st.markdown(f'<div style="width:120px; margin:0 auto 10px;"><div class="proj-grid-container"><img src="data:image/jpeg;base64,{f_df.iloc[-1]["사진1"]}"></div></div>', unsafe_allow_html=True)

    if not f_df.empty:
        mood_counts = f_df['기분'].value_counts()
        st.markdown(f"<div class='summary-box'>✨ {d_n}은 주로 <b>'{mood_counts.idxmax()}'</b> 기분이 많았네요!</div>", unsafe_allow_html=True)

# --- [TAB 6: 📊 기록 요약] ---
with tab_log:
    # 수정 5: 요약 멘트 및 그래프 복원
    st.markdown("<div class='title-text'>DANA의 기록 요약</div>", unsafe_allow_html=True)
    if not df.empty:
        total_p = df['작품명'].nunique(); done_p = df[df['단계'] == "완성"]['작품명'].nunique(); ing_p = total_p - done_p
        top_m = df['기분'].mode()[0] if not df['기분'].empty else "-"
        st.markdown(f"""
        <div class="dana-card">
            <p style='line-height:1.8;'>지금까지 Dana님은...<br>총 <span class="highlight">{done_p}개</span>를 완성하고,<br>지금은 <span class="highlight">{ing_p}개</span>를 빚고 있어요. 🕊️<br>주로 <span class="highlight">'{top_m}' {MOOD_DICT.get(top_m, '')}</span> 마음이었네요!</p>
        </div>
        """, unsafe_allow_html=True)
        fig = go.Figure(data=[go.Pie(labels=df['기분'].value_counts().index, values=df['기분'].value_counts().values, hole=.6, marker=dict(colors=PASTEL_COLORS))])
        fig.update_layout(height=280, margin=dict(t=10, b=10, l=10, r=10), legend=dict(orientation="h", y=-0.2))
        st.plotly_chart(fig, use_container_width=True)

st.markdown("<br><br><br>", unsafe_allow_html=True)
