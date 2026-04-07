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

    /* 캘린더 표 디자인 */
    .cal-table {{ width: 100%; border-collapse: collapse; table-layout: fixed; margin-bottom: 10px; }}
    .cal-table th {{ text-align: center; font-size: 0.7em; color: {MAIN_COLOR}; padding: 8px 0; font-weight: bold; }}
    .cal-table td {{ 
        border: 1px solid #EEE; background: white; height: 65px; 
        vertical-align: top; padding: 2px; text-align: center; position: relative;
    }}
    .cal-date-num {{ font-size: 0.6em; color: #CCC; display: block; text-align: left; padding-left: 2px; }}
    
    /* 기록이 있는 날 음영 처리 */
    .has-record {{ background-color: #F9F5F2 !important; }}
    
    /* 캘린더 내 작은 썸네일 */
    .cal-thumb {{
        width: 35px; height: 35px; object-fit: cover; border-radius: 5px; margin-top: 2px;
    }}
    .cal-badge {{
        position: absolute; bottom: 2px; right: 2px;
        background: rgba(141, 110, 99, 0.7); color: white;
        font-size: 0.5em; padding: 1px 3px; border-radius: 3px;
    }}
    .is-today-circle {{ border: 2px solid {MAIN_COLOR} !important; }}

    .summary-box {{ background: #F9F5F2; padding: 15px; border-radius: 15px; border-left: 5px solid {MAIN_COLOR}; margin-top: 10px; line-height: 1.6; }}
    .highlight {{ color: #D4A373; font-weight: 800; font-size: 1.15em; }}
    .title-text {{ font-size: 1.5em; font-weight: 800; color: #5D574F; margin-bottom: 15px; }}
    .stButton>button {{ width: 100%; border-radius: 12px; height: 3em; background-color: {MAIN_COLOR}; color: white; font-weight: bold; border: none; }}
    
    /* 갤러리 정방형 */
    .gallery-img-container {{ width: 100%; aspect-ratio: 1/1; overflow: hidden; border-radius: 12px; background-color: #F8F8F8; }}
    .gallery-img-container img {{ width: 100%; height: 100%; object-fit: cover; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. 데이터 및 세션 로직 ---
DATA_FILE = "pottery_diary_v4.csv"
MOOD_DICT = {"행복": "😊", "기쁨": "😄", "절망": "😱", "슬픔": "😢", "화이팅": "🔥", "실망": "😞", "감격": "😭"}

def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df['날짜'] = pd.to_datetime(df['날짜']).dt.date
        return df
    return pd.DataFrame(columns=["날짜", "작품명", "흙", "단계", "내용", "사진1", "사진2", "사진3", "기분", "작업유형", "기물종류"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')

def process_img(upload_file):
    if upload_file is None: return ""
    img = Image.open(upload_file).convert("RGB")
    img = ImageOps.fit(img, (800, 800), Image.Resampling.LANCZOS)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=80)
    return base64.b64encode(buf.getvalue()).decode()

df = load_data()

# 년월 리스트 생성 (25년 1월 ~ 26년 4월)
month_options = []
for y in [2025, 2026]:
    for m in range(1, 13):
        if y == 2026 and m > 4: break
        month_options.append(f"{y}년 {m:02d}월")

if 'selected_month_str' not in st.session_state:
    st.session_state.selected_month_str = "2026년 04월"

# --- 3. 메뉴 구성 ---
tab_cal, tab_rec, tab_proj, tab_mood, tab_log = st.tabs(["📅", "📝", "🏺", "✨", "📊"])

# --- [TAB 1: 캘린더 모아보기] ---
with tab_cal:
    # 상단 네비게이션
    col1, col2, col3 = st.columns([1, 4, 1])
    with col2:
        st.session_state.selected_month_str = st.selectbox("이동할 년월 선택", month_options, index=month_options.index(st.session_state.selected_month_str), label_visibility="collapsed")
    
    # 선택된 년월 파싱
    view_y = int(st.session_state.selected_month_str[:4])
    view_m = int(st.session_state.selected_month_str[6:8])
    
    with col1:
        if st.button("◀"):
            idx = month_options.index(st.session_state.selected_month_str)
            if idx > 0: 
                st.session_state.selected_month_str = month_options[idx-1]
                st.rerun()
    with col3:
        if st.button("▶"):
            idx = month_options.index(st.session_state.selected_month_str)
            if idx < len(month_options)-1: 
                st.session_state.selected_month_str = month_options[idx+1]
                st.rerun()

    st.markdown(f"<div class='title-text'>{view_m}월 모아보기</div>", unsafe_allow_html=True)
    
    # 캘린더 그리기
    cal_data = calendar.monthcalendar(view_y, view_m)
    today_date = datetime.now().date()
    work_days = 0
    
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
                
                has_rec_cls = "has-record" if not day_logs.empty else ""
                today_cls = "is-today-circle" if curr_date == today_date else ""
                
                thumb_html = ""
                if not day_logs.empty:
                    work_days += 1
                    last_log = day_logs.iloc[-1]
                    if pd.notna(last_log['사진1']) and last_log['사진1'] != "":
                        thumb_html = f'<img src="data:image/jpeg;base64,{last_log["사진1"]}" class="cal-thumb">'
                    if len(day_logs) > 1:
                        thumb_html += f'<span class="cal-badge">+{len(day_logs)-1}</span>'
                
                html += f'<td class="{has_rec_cls} {today_cls}"><span class="cal-date-num">{day}</span>{thumb_html}</td>'
        html += '</tr>'
    st.markdown(html + '</tbody></table>', unsafe_allow_html=True)
    st.markdown(f"<div class='summary-box'>💡 이번 달은 {work_days}일 작업했어요!</div>", unsafe_allow_html=True)

    # 하단 상세 보기
    st.divider()
    detail_date = st.date_input("상세 내용을 볼 날짜 선택", today_date)
    sel_logs = df[df['날짜'] == detail_date]
    if not sel_logs.empty:
        for idx, row in sel_logs.iterrows():
            with st.container():
                st.markdown(f"""
                <div class="summary-box">
                    <b>{MOOD_DICT.get(row['기분'], '')} {row['작품명']}</b> | {row['단계']}<br>
                    {row['내용']}
                </div>
                """, unsafe_allow_html=True)
                i_cols = st.columns(3)
                for i, c_n in enumerate(['사진1', '사진2', '사진3']):
                    if pd.notna(row[c_n]) and row[c_n] != "": i_cols[i].image(base64.b64decode(row[c_n]), use_container_width=True)

# --- [TAB 2: 기록하기] ---
with tab_rec:
    st.markdown("<div class='title-text'>오늘의 작업 기록</div>", unsafe_allow_html=True)
    with st.form("record_form", clear_on_submit=True):
        sel_mood = st.radio("기분", list(MOOD_DICT.keys()), horizontal=True, format_func=lambda x: MOOD_DICT[x], label_visibility="collapsed")
        c1, c2 = st.columns(2)
        with c1: r_date = st.date_input("날짜", datetime.now().date())
        with c2: r_title = st.text_input("작품명")
        c3, c4 = st.columns(2)
        with c3: r_type = st.selectbox("유형", ["물레", "핸드빌딩", "기타"])
        with c4: r_clay = st.selectbox("흙", ["백자토", "산백토", "조형토", "청자토", "옹기토", "기타"])
        r_obj = st.selectbox("기물", ["컵", "접시", "그릇", "항아리", "고블렛", "면기", "오브제", "기타"])
        r_step = st.select_slider("단계", options=["성형", "건조", "초벌", "시유", "완성"])
        r_imgs = st.file_uploader("사진 (최대 3장)", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
        r_note = st.text_area("메모")
        if st.form_submit_button("저장하기"):
            if r_title:
                img_list = [process_img(r_imgs[i]) if i < len(r_imgs) else "" for i in range(3)]
                new_row = pd.DataFrame([[r_date, r_title, r_clay, r_step, r_note, img_list[0], img_list[1], img_list[2], sel_mood, r_type, r_obj]], columns=df.columns)
                df = pd.concat([df, new_row], ignore_index=True); save_data(df); st.balloons(); st.rerun()

# --- [TAB 3: 작품 모아보기] ---
with tab_proj:
    st.markdown("<div class='title-text'>작품 모아보기</div>", unsafe_allow_html=True)
    p_filter = st.radio("필터", ["전체", "작업중", "완성"], horizontal=True)
    if not df.empty:
        u_titles = df['작품명'].unique()
        display_titles = [t for t in u_titles if (p_filter=="전체") or (p_filter=="작업중" and "완성" not in df[df['작품명']==t]['단계'].values) or (p_filter=="완성" and "완성" in df[df['작품명']==t]['단계'].values)]
        proj_cols = st.columns(2)
        for idx, t in enumerate(display_titles):
            p_logs = df[df['작품명'] == t].sort_values(by=['날짜'])
            rep_row = p_logs[p_logs['사진1'] != ""].iloc[-1] if not p_logs[p_logs['사진1'] != ""].empty else None
            with proj_cols[idx % 2]:
                img_src = f"data:image/jpeg;base64,{rep_row['사진1']}" if rep_row is not None else ""
                st.markdown(f'<div class="gallery-img-container">{"<img src=\'"+img_src+"\'>" if rep_row is not None else "<div style=\'padding:40% 0; text-align:center; color:#ccc;\'>No Photo</div>"}</div>', unsafe_allow_html=True)
                st.markdown(f"**🏺 {t}**")
                with st.expander("상세/수정/삭제"):
                    for r_idx, row in p_logs.iterrows():
                        st.caption(f"{row['날짜']} | {row['단계']}")
                        if st.button("삭제", key=f"del_{r_idx}"): df = df.drop(index=r_idx); save_data(df); st.rerun()
    else: st.info("기록이 없습니다.")

# --- [TAB 4: 기분 조각들] ---
with tab_mood:
    st.markdown("<div class='title-text'>기분 조각들</div>", unsafe_allow_html=True)
    mood_mode = st.radio("기준", ["월별", "작품별"], horizontal=True)
    if mood_mode == "월별":
        m_val = st.selectbox("월 선택", list(range(1, 13)), index=datetime.now().month-1, key="sm_m")
        m_df = df.copy(); m_df['월'] = pd.to_datetime(m_df['날짜']).dt.month
        filtered_df = m_df[m_df['월'] == m_val]; d_name = f"{m_val}월"
    else:
        p_val = st.selectbox("작품 선택", sorted(df['작품명'].unique()) if not df.empty else ["없음"], key="sp_m")
        filtered_df = df[df['작품명'] == p_val]; d_name = p_val
        if not filtered_df.empty and filtered_df.iloc[-1]['사진1'] != "":
            st.markdown(f'<div style="width:120px; margin:0 auto 10px;"><div class="gallery-img-container"><img src="data:image/jpeg;base64,{filtered_df.iloc[-1]["사진1"]}"></div></div>', unsafe_allow_html=True)

    if not filtered_df.empty:
        mood_counts = filtered_df['기분'].value_counts(); total_m = len(filtered_df)
        st.markdown(f"<div class='summary-box'>✨ {d_name}은 주로 <b>'{mood_counts.idxmax()}'</b>였네요!</div>", unsafe_allow_html=True)
        items = list(MOOD_DICT.items())
        h_mood = '<table style="width:100%; table-layout:fixed; border-collapse:collapse;"><tr>'
        for i in range(4):
            name, emoji = items[i]; cnt = mood_counts.get(name, 0); pct = int(cnt/total_m*100)
            h_mood += f'<td style="text-align:center; padding:5px; background:white; border:1px solid #F8F8F8;"><div style="font-size:1.2em;">{emoji}</div><div style="font-size:0.7em; color:#888;">{name}</div><div style="font-weight:bold; color:{MAIN_COLOR}; font-size:0.8em;">{pct}%</div></td>'
        h_mood += '</tr><tr>'
        for i in range(4, 7):
            name, emoji = items[i]; cnt = mood_counts.get(name, 0); pct = int(cnt/total_m*100)
            h_mood += f'<td style="text-align:center; padding:5px; background:white; border:1px solid #F8F8F8;"><div style="font-size:1.2em;">{emoji}</div><div style="font-size:0.7em; color:#888;">{name}</div><div style="font-weight:bold; color:{MAIN_COLOR}; font-size:0.8em;">{pct}%</div></td>'
        st.markdown(h_mood + '<td></td></tr></table>', unsafe_allow_html=True)

# --- [TAB 5: Dana's Log] ---
with tab_log:
    st.markdown("<div class='title-text'>DANA의 기록 요약</div>", unsafe_allow_html=True)
    if not df.empty:
        total_p = df['작품명'].nunique(); done_p = df[df['단계'] == "완성"]['작품명'].nunique()
        st.markdown(f"<div class='dana-card'>지금까지 총 <span class='highlight'>{done_p}개</span>를 완성했어요!</div>", unsafe_allow_html=True)
        fig = go.Figure(data=[go.Pie(labels=df['기분'].value_counts().index, values=df['기분'].value_counts().values, hole=.6, marker=dict(colors=PASTEL_COLORS))])
        fig.update_layout(showlegend=True, margin=dict(t=10, b=10, l=10, r=10), height=280, legend=dict(orientation="h", y=-0.1))
        st.plotly_chart(fig, use_container_width=True)

st.markdown("<br><br><br>", unsafe_allow_html=True)
