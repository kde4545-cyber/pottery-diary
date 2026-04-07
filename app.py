import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
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

    /* 캘린더 사진 그리드 디자인 */
    .cal-grid-container {{
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 3px;
        width: 100%;
    }}
    .cal-header-item {{
        text-align: center; font-size: 0.7em; font-weight: bold; color: {MAIN_COLOR}; padding: 5px 0;
    }}
    .cal-photo-cell {{
        position: relative;
        width: 100%;
        aspect-ratio: 1 / 1.1;
        background: white;
        border: 1px solid #F0F0F0;
        border-radius: 8px;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        align-items: center;
    }}
    .cal-photo-cell img {{
        width: 100%;
        height: 80%;
        object-fit: cover;
    }}
    .cal-day-num {{
        font-size: 0.6em;
        color: #BBB;
        padding-top: 2px;
    }}
    .photo-count-badge {{
        position: absolute;
        top: 2px;
        right: 2px;
        background: rgba(0,0,0,0.4);
        color: white;
        font-size: 0.5em;
        padding: 1px 4px;
        border-radius: 4px;
    }}
    .is-selected-day {{
        border: 2px solid {MAIN_COLOR} !important;
        background-color: #FFF9F8 !important;
    }}

    .gallery-card {{ background: white; border-radius: 15px; box-shadow: 0px 4px 12px rgba(0,0,0,0.05); margin-bottom: 10px; overflow: hidden; }}
    .gallery-img-container {{ width: 100%; aspect-ratio: 1 / 1; overflow: hidden; background-color: #F8F8F8; }}
    .gallery-img-container img {{ width: 100%; height: 100%; object-fit: cover; }}
    .summary-box {{ background: #F9F5F2; padding: 15px; border-radius: 15px; border-left: 5px solid {MAIN_COLOR}; margin-top: 10px; line-height: 1.6; }}
    .highlight {{ color: #D4A373; font-weight: 800; font-size: 1.15em; }}
    .title-text {{ font-size: 1.5em; font-weight: 800; color: #5D574F; margin-bottom: 15px; }}
    .stButton>button {{ width: 100%; border-radius: 12px; height: 3.5em; background-color: {MAIN_COLOR}; color: white; font-weight: bold; border: none; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. 데이터 및 세션 관리 ---
DATA_FILE = "pottery_diary_v4.csv"
MOOD_DICT = {"행복": "😊", "기쁨": "😄", "절망": "😱", "슬픔": "😢", "화이팅": "🔥", "실망": "😞", "감격": "😭"}

# 현재 보고 있는 달 관리
if 'view_month' not in st.session_state:
    st.session_state.view_month = datetime.now().date().replace(day=1)
if 'selected_date' not in st.session_state:
    st.session_state.selected_date = datetime.now().date()

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

# --- 3. 메뉴 구성 ---
tab_cal, tab_rec, tab_proj, tab_mood, tab_log = st.tabs(["📅", "📝", "🏺", "✨", "📊"])

# --- [TAB 1: 캘린더 모아보기] ---
with tab_cal:
    # 달력 네비게이션 (이전/이후 버튼 + 드롭다운)
    col_prev, col_sel, col_next = st.columns([1, 4, 1])
    
    with col_prev:
        if st.button("◀"):
            st.session_state.view_month = (st.session_state.view_month - timedelta(days=1)).replace(day=1)
            st.rerun()
            
    with col_sel:
        # 2025년 1월부터 선택 가능하도록 리스트 생성
        start_year = 2025
        years = [2025, 2026, 2027]
        months = list(range(1, 13))
        
        # 년-월 선택 박스
        cur_y = st.session_state.view_month.year
        cur_m = st.session_state.view_month.month
        
        sel_col1, sel_col2 = st.columns(2)
        with sel_col1:
            new_y = st.selectbox("년", years, index=years.index(cur_y), label_visibility="collapsed")
        with sel_col2:
            new_m = st.selectbox("월", months, index=months.index(cur_m), label_visibility="collapsed")
        
        # 선택박스 변경 시 세션 업데이트
        if new_y != cur_y or new_m != cur_m:
            st.session_state.view_month = date(new_y, new_m, 1)
            st.rerun()

    with col_next:
        if st.button("▶"):
            # 다음 달 1일 계산
            nm = st.session_state.view_month.month + 1
            ny = st.session_state.view_month.year
            if nm > 12: nm = 1; ny += 1
            st.session_state.view_month = date(ny, nm, 1)
            st.rerun()

    st.markdown(f"<div class='title-text'>{st.session_state.view_month.month}월 모아보기</div>", unsafe_allow_html=True)

    # 캘린더 그리드 표시
    cal_html = '<div class="cal-grid-container">'
    for d in ["월", "화", "수", "목", "금", "토", "일"]:
        cal_html += f'<div class="cal-header-item">{d}</div>'
    
    cal_data = calendar.monthcalendar(st.session_state.view_month.year, st.session_state.view_month.month)
    
    for week in cal_data:
        for day in week:
            if day == 0:
                cal_html += '<div></div>'
            else:
                curr_date = date(st.session_state.view_month.year, st.session_state.view_month.month, day)
                day_logs = df[df['날짜'] == curr_date]
                
                # 대표 사진 및 개수 확인
                thumb_img = ""
                extra_count = ""
                if not day_logs.empty:
                    # 마지막 글의 사진 1번
                    last_log = day_logs.iloc[-1]
                    if pd.notna(last_log['사진1']) and last_log['사진1'] != "":
                        thumb_img = f'<img src="data:image/jpeg;base64,{last_log["사진1"]}">'
                    
                    # 총 기록 수 (1개 초과 시 +n 표시)
                    if len(day_logs) > 1:
                        extra_count = f'<div class="photo-count-badge">+{len(day_logs)-1}</div>'
                
                # 오늘 또는 선택된 날 강조
                selected_cls = "is-selected-day" if curr_date == st.session_state.selected_date else ""
                
                cal_html += f'''
                    <div class="cal-photo-cell {selected_cls}">
                        <div class="cal-day-num">{day}</div>
                        {thumb_img}
                        {extra_count}
                    </div>
                '''
    cal_html += '</div>'
    st.markdown(cal_html, unsafe_allow_html=True)

    # 날짜 클릭 기능을 대신할 선택기 (모바일 대응)
    st.divider()
    st.write("🔍 **날짜를 선택해서 상세 기록을 확인하세요**")
    detail_date = st.date_input("상세 보기 날짜", st.session_state.selected_date, key="detail_picker")
    if detail_date != st.session_state.selected_date:
        st.session_state.selected_date = detail_date
        st.rerun()

    # 선택된 날짜의 상세 내역
    selected_logs = df[df['날짜'] == st.session_state.selected_date]
    if not selected_logs.empty:
        st.markdown(f"### 🏺 {st.session_state.selected_date}의 기록")
        for idx, row in selected_logs.iterrows():
            with st.container():
                st.markdown(f"""
                <div class="summary-box">
                    <b>{MOOD_DICT.get(row['기분'], '')} {row['작품명']}</b> | {row['단계']}<br>
                    <small>{row['작업유형']} · {row['기물종류']} · {row['흙']}</small><br>
                    {row['내용']}
                </div>
                """, unsafe_allow_html=True)
                i_cols = st.columns(3)
                for i, c_name in enumerate(['사진1', '사진2', '사진3']):
                    if pd.notna(row[c_name]) and row[c_name] != "":
                        i_cols[i].image(base64.b64decode(row[c_name]), use_container_width=True)
                st.write("")
    else:
        st.caption("선택한 날짜에 기록이 없습니다.")

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
        if st.form_submit_button("기록 저장하기"):
            if r_title:
                img_list = [process_img(r_imgs[i]) if i < len(r_imgs) else "" for i in range(3)]
                new_row = pd.DataFrame([[r_date, r_title, r_clay, r_step, r_note, img_list[0], img_list[1], img_list[2], sel_mood, r_type, r_obj]], columns=df.columns)
                df = pd.concat([df, new_row], ignore_index=True); save_data(df); st.balloons(); st.rerun()

# --- [TAB 3: 작품 모아보기] ---
with tab_proj:
    st.markdown("<div class='title-text'>작품 모아보기</div>", unsafe_allow_html=True)
    p_filter = st.radio("필터", ["전체", "작업중", "완성"], horizontal=True, label_visibility="collapsed")
    if not df.empty:
        u_titles = df['작품명'].unique()
        display_titles = [t for t in u_titles if (p_filter=="전체") or (p_filter=="작업중" and "완성" not in df[df['작품명']==t]['단계'].values) or (p_filter=="완성" and "완성" in df[df['작품명']==t]['단계'].values)]
        proj_cols = st.columns(2)
        for idx, t in enumerate(display_titles):
            p_logs = df[df['작품명'] == t].sort_values(by=['날짜'])
            finished = "완성" in p_logs['단계'].values
            rep_row = p_logs[p_logs['사진1'] != ""].iloc[-1] if not p_logs[p_logs['사진1'] != ""].empty else None
            with proj_cols[idx % 2]:
                img_src = f"data:image/jpeg;base64,{rep_row['사진1']}" if rep_row is not None else ""
                st.markdown(f'<div class="gallery-card"><div class="gallery-img-container">{"<img src=\'"+img_src+"\'>" if rep_row is not None else "<div style=\'padding:40% 10%; color:#ccc;\'>No Photo</div>"}</div><div style="padding:8px; font-weight:bold; font-size:0.9em;">🏺 {t} {"(완성)" if finished else ""}</div></div>', unsafe_allow_html=True)
                with st.expander("과정 보기"):
                    for r_idx, row in p_logs.iterrows():
                        st.caption(f"{row['날짜']} | {row['단계']}")
                        if st.button("삭제", key=f"del_{r_idx}"): df = df.drop(index=r_idx); save_data(df); st.rerun()

# --- [TAB 4: 기분 조각들] ---
with tab_mood:
    st.markdown("<div class='title-text'>기분 조각들</div>", unsafe_allow_html=True)
    mood_mode = st.radio("기준", ["월별", "작품별"], horizontal=True)
    if mood_mode == "월별":
        m_val = st.selectbox("월", list(range(1, 13)), index=datetime.now().month-1)
        m_df = df.copy(); m_df['월'] = pd.to_datetime(m_df['날짜']).dt.month
        filtered_df = m_df[m_df['월'] == m_val]
        display_name = f"{m_val}월"
    else:
        p_val = st.selectbox("작품", sorted(df['작품명'].unique()) if not df.empty else ["없음"])
        filtered_df = df[df['작품명'] == p_val]
        display_name = p_val
        if not filtered_df.empty:
            photo_logs = filtered_df[filtered_df['사진1'] != ""]
            if not photo_logs.empty:
                st.markdown(f'<div style="width:120px; margin:0 auto;"><div class="gallery-card"><div class="gallery-img-container"><img src="data:image/jpeg;base64,{photo_logs.iloc[-1]["사진1"]}"></div></div></div>', unsafe_allow_html=True)

    if not filtered_df.empty:
        mood_counts = filtered_df['기분'].value_counts()
        total_m = len(filtered_df)
        st.markdown(f"<div class='summary-box'>✨ {display_name}은 주로 <b>'{mood_counts.idxmax()}'</b> 기분이었네요!</div>", unsafe_allow_html=True)
        # 기분 요약 표 (단순화)
        m_cols = st.columns(4)
        for i, (name, emoji) in enumerate(MOOD_DICT.items()):
            cnt = mood_counts.get(name, 0)
            with m_cols[i%4]: st.write(f"{emoji}\n{int(cnt/total_m*100)}%")

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
