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
    
    /* 상단 메뉴바 균등 분할 */
    .stTabs [data-baseweb="tab-list"] {{ justify-content: space-around; border-bottom: none; }}
    .stTabs [data-baseweb="tab"] {{ flex-grow: 1; text-align: center; }}
    .stTabs [data-baseweb="tab-list"] button div {{ font-size: 1.4rem !important; }}

    /* 7열 고정 달력 디자인 */
    .cal-table {{ width: 100%; border-collapse: collapse; table-layout: fixed; margin-bottom: 10px; }}
    .cal-table th {{ text-align: center; font-size: 0.75em; color: {MAIN_COLOR}; padding: 8px 0; font-weight: bold; }}
    .cal-table td {{ border: 1px solid #F2F2F2; background: white; height: 65px; vertical-align: top; padding: 4px; text-align: center; position: relative; }}
    .cal-date-num {{ font-size: 0.7em; color: #CCC; display: block; text-align: left; }}
    .has-rec {{ background-color: #F9F5F2 !important; }}
    .cal-thumb {{ width: 32px; height: 32px; object-fit: cover; border-radius: 4px; margin-top: 2px; }}

    /* 작품 모아보기 3x3 그리드 */
    .proj-grid-box {{
        width: 100%; aspect-ratio: 1/1; overflow: hidden; border-radius: 10px; background-color: #F0F0F0; border: 1px solid #EEE; margin-bottom: 5px;
        display: flex; align-items: center; justify-content: center;
    }}
    .proj-grid-box img {{ width: 100%; height: 100%; object-fit: cover; }}
    .proj-empty-box {{ background-color: #F8F8F8; border: 1px dashed #DDD; }}

    /* 기분 통계 표 */
    .mood-stat-table {{ width: 100%; table-layout: fixed; border-collapse: collapse; margin-top: 10px; }}
    .mood-stat-table td {{ text-align: center; padding: 10px 2px; background: white; border: 1px solid #F8F8F8; border-radius: 12px; }}

    .summary-box {{ background: #F9F5F2; padding: 15px; border-radius: 15px; border-left: 5px solid {MAIN_COLOR}; margin-top: 10px; line-height: 1.6; }}
    .dana-card {{ background: white; padding: 20px; border-radius: 20px; box-shadow: 0px 8px 20px rgba(0,0,0,0.03); margin-bottom: 20px; }}
    .title-text {{ font-size: 1.5em; font-weight: 800; color: #5D574F; margin-bottom: 15px; }}
    .highlight {{ color: #D4A373; font-weight: 800; font-size: 1.1em; }}
    .stButton>button {{ width: 100%; border-radius: 12px; height: 3.5em; background-color: {MAIN_COLOR}; color: white; font-weight: bold; border: none; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. 데이터 및 공통 로직 ---
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

# 공통 년월 리스트 (25년 01월 ~ 26년 04월)
month_opts = [f"{y}년 {m:02d}월" for y in [2025, 2026] for m in range(1, 13) if not (y == 2026 and m > 4)]

# 세션 상태
if 'sel_month_idx' not in st.session_state: st.session_state.sel_month_idx = len(month_opts) - 1

# --- 3. 메뉴 구성 (6단 탭) ---
tabs = st.tabs(["📅", "📜", "📝", "🏺", "✨", "📊"])
tab_cal, tab_list, tab_rec, tab_proj, tab_mood, tab_log = tabs

# --- [TAB 1: 📅 월간 모아보기] ---
with tab_cal:
    nav_c1, nav_c2, nav_c3 = st.columns([1, 6, 1])
    with nav_c1:
        if st.button("◀", key="cal_p"):
            if st.session_state.sel_month_idx > 0: st.session_state.sel_month_idx -= 1; st.rerun()
    with nav_c2:
        month_str = st.selectbox("월", month_opts, index=st.session_state.sel_month_idx, label_visibility="collapsed", key="cal_sel")
        st.session_state.sel_month_idx = month_opts.index(month_str)
    with nav_c3:
        if st.button("▶", key="cal_n"):
            if st.session_state.sel_month_idx < len(month_opts) - 1: st.session_state.sel_month_idx += 1; st.rerun()

    y_val, m_val = int(month_str[:4]), int(month_str[6:8])
    st.markdown(f"<div class='title-text'>{m_val}월 모아보기</div>", unsafe_allow_html=True)
    cal_data = calendar.monthcalendar(y_val, m_val)
    html_cal = '<table class="cal-table"><thead><tr>'
    for d_n in ["월", "화", "수", "목", "금", "토", "일"]: html_cal += f'<th>{d_n}</th>'
    html_cal += '</tr></thead><tbody>'
    for week in cal_data:
        html_cal += '<tr>'
        for day in week:
            if day == 0: html_cal += '<td></td>'
            else:
                logs = df[df['날짜'] == date(y_val, m_val, day)]
                td_cls = "has-rec" if not logs.empty else ""
                thumb = f'<img src="data:image/jpeg;base64,{logs.iloc[-1]["사진1"]}" class="cal-thumb">' if not logs.empty and pd.notna(logs.iloc[-1]['사진1']) else ""
                html_cal += f'<td class="{td_cls}"><span class="cal-date-num">{day}</span>{thumb}</td>'
        html_cal += '</tr>'
    st.markdown(html_cal + '</tbody></table>', unsafe_allow_html=True)

# --- [TAB 2: 📜 기록 모아보기] ---
with tab_list:
    st.markdown("<div class='title-text'>기록 모아보기</div>", unsafe_allow_html=True)
    if not df.empty:
        for idx, row in df.sort_values(by='날짜', ascending=False).iterrows():
            with st.expander(f"🏺 {row['날짜']} | {row['작품명']} ({row['단계']})"):
                st.write(f"**기분:** {MOOD_DICT.get(row['기분'], '')} | **유형:** {row['작업유형']} | **기물:** {row['기물종류']}")
                st.write(f"**메모:** {row['내용']}")
                i_cols = st.columns(3)
                for i, c in enumerate(['사진1', '사진2', '사진3']):
                    if pd.notna(row[c]) and row[c] != "": i_cols[i].image(base64.b64decode(row[c]), use_container_width=True)
                if st.button("🗑️ 삭제", key=f"del_l_{idx}"): df = df.drop(index=idx); save_data(df); st.rerun()

# --- [TAB 3: 📝 기록하기] ---
with tab_rec:
    st.markdown("<div class='title-text'>오늘의 작업 기록</div>", unsafe_allow_html=True)
    with st.form("rec_form", clear_on_submit=True):
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
        if st.form_submit_button("기록 저장하기"):
            if r_title:
                img_l = [process_img(r_imgs[i]) if i < len(r_imgs) else "" for i in range(3)]
                new_d = pd.DataFrame([[r_date, r_title, r_clay, r_step, r_note, img_l[0], img_l[1], img_l[2], mood, r_type, r_obj]], columns=df.columns)
                df = pd.concat([df, new_d], ignore_index=True); save_data(df); st.balloons(); st.rerun()

# --- [TAB 4: 🏺 작품 모아보기 - 3x3 그리드 고정] ---
with tab_proj:
    st.markdown("<div class='title-text'>작품 모아보기</div>", unsafe_allow_html=True)
    p_filter = st.radio("상태 필터", ["전체", "작업중", "완성"], horizontal=True, key="p_f")
    
    if not df.empty:
        # 필터링 로직
        u_titles = df['작품명'].unique()[::-1]
        display_list = []
        for t in u_titles:
            p_df = df[df['작품명'] == t]
            is_done = "완성" in p_df['단계'].values
            if (p_filter == "작업중" and is_done) or (p_filter == "완성" and not is_done): continue
            display_list.append(t)
        
        # 3x3 (총 9칸) 그리드 생성
        grid_count = max(len(display_list), 9)
        cols = st.columns(3)
        for i in range(grid_count):
            with cols[i % 3]:
                if i < len(display_list):
                    t = display_list[i]
                    p_logs = df[df['작품명'] == t].sort_values(by='날짜')
                    rep = p_logs[p_logs['사진1'] != ""].iloc[-1] if not p_logs[p_logs['사진1'] != ""].empty else None
                    is_done = "완성" in p_logs['단계'].values
                    
                    st.markdown(f"<div style='text-align:center; font-weight:bold; font-size:0.75em; height:1.5em; overflow:hidden;'>{t} {'✅' if is_done else ''}</div>", unsafe_allow_html=True)
                    src = f"data:image/jpeg;base64,{rep['사진1']}" if rep is not None else ""
                    st.markdown(f'<div class="proj-grid-box">{"<img src=\'"+src+"\'>" if src else "<span style=\'color:#ccc; font-size:0.7em;\'>No Pic</span>"}</div>', unsafe_allow_html=True)
                else:
                    st.markdown("<div style='height:1.5em;'></div>", unsafe_allow_html=True)
                    st.markdown('<div class="proj-grid-box proj-empty-box"></div>', unsafe_allow_html=True)
    else: st.info("기록이 없습니다.")

# --- [TAB 5: ✨ 기분 조각들 - 통합 드롭다운 및 퍼센트 복원] ---
with tab_mood:
    st.markdown("<div class='title-text'>기분 조각들</div>", unsafe_allow_html=True)
    mood_mode = st.radio("분석 기준", ["📅 월별", "🏺 작품별"], horizontal=True)
    
    if mood_mode == "📅 월별":
        sel_m_str = st.selectbox("분석 월 선택", month_opts, index=st.session_state.sel_month_idx, key="mood_m_sel")
        view_y, view_m = int(sel_m_str[:4]), int(sel_m_str[6:8])
        f_df = df[pd.to_datetime(df['날짜']).dt.month == view_m]; d_n = f"{view_m}월"
    else:
        p_val = st.selectbox("작품 선택", sorted(df['작품명'].unique()), key="mood_p_sel")
        f_df = df[df['작품명'] == p_val]; d_n = p_val
        if not f_df.empty and pd.notna(f_df.iloc[-1]['사진1']):
            st.markdown(f'<div style="width:120px; margin:0 auto 10px;"><div class="proj-grid-box"><img src="data:image/jpeg;base64,{f_df.iloc[-1]["사진1"]}"></div></div>', unsafe_allow_html=True)

    if not f_df.empty:
        mood_counts = f_df['기분'].value_counts(); total_m = len(f_df)
        st.markdown(f"<div class='summary-box'>✨ {d_n}의 기록을 살펴보니,<br>다나님은 주로 <span class='highlight'>'{mood_counts.idxmax()}'</span> 기분으로 작업하셨네요!</div>", unsafe_allow_html=True)
        
        # 가로 4칸 표로 퍼센트 표시
        items = list(MOOD_DICT.items())
        h_mood = '<table style="width:100%; table-layout:fixed; border-collapse:collapse; margin-top:10px;"><tr>'
        for i, (name, emoji) in enumerate(items):
            cnt = mood_counts.get(name, 0); pct = int(cnt/total_m*100)
            if i == 4: h_mood += '</tr><tr>'
            h_mood += f'<td style="text-align:center; padding:8px 2px; background:white; border:1px solid #F8F8F8;"><div style="font-size:1.3em;">{emoji}</div><div style="font-size:0.7em; color:#888;">{name}</div><div style="font-weight:bold; color:{MAIN_COLOR}; font-size:0.85em;">{pct}%</div><div style="font-size:0.6em; color:#CCC;">({cnt}회)</div></td>'
        st.markdown(h_mood + '<td></td></tr></table>', unsafe_allow_html=True)

# --- [TAB 6: 📊 DANA의 기록 요약 - 3종 그래프 복원] ---
with tab_log:
    st.markdown("<div class='title-text'>DANA의 기록 요약</div>", unsafe_allow_html=True)
    if not df.empty:
        total_p = df['작품명'].nunique(); done_p = df[df['단계'] == "완성"]['작품명'].nunique(); ing_p = total_p - done_p
        top_m = df['기분'].mode()[0] if not df['기분'].empty else "-"; top_o = df['기물종류'].mode()[0] if not df['기물종류'].empty else "-"
        
        st.markdown(f"""
        <div class="dana-card">
            <p style='line-height:1.8;'>지금까지 Dana님은...<br>총 <span class="highlight">{done_p}개</span>의 작품을 완성하고,<br>지금은 <span class="highlight">{ing_p}개</span>의 아이들을 빚고 있어요. 🕊️<br>주로 흙을 만질 때 <span class="highlight">'{top_m}' {MOOD_DICT.get(top_m, '')}</span> 마음이었고,<br>가장 많이 만든 건 <span class="highlight">'{top_o}'</span>이에요!</p>
        </div>
        """, unsafe_allow_html=True)

        def draw_donut(labels, values, title):
            fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.6, marker=dict(colors=PASTEL_COLORS))])
            fig.update_layout(showlegend=True, margin=dict(t=30, b=10, l=10, r=10), height=250, legend=dict(orientation="h", y=-0.2))
            st.write(f"**{title}**"); st.plotly_chart(fig, use_container_width=True)

        draw_donut(df['기분'].value_counts().index, df['기분'].value_counts().values, "🌈 기분 비중")
        draw_donut(df['작업유형'].value_counts().index, df['작업유형'].value_counts().values, "⚙️ 작업 유형")
        draw_donut(df['기물종류'].value_counts().index, df['기물종류'].value_counts().values, "🏺 기물 종류")

st.markdown("<br><br><br>", unsafe_allow_html=True)
