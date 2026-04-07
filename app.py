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

# 디자인 테마 설정
PASTEL_COLORS = ['#FFB7B2', '#FFDAC1', '#E2F0CB', '#B5EAD7', '#C7CEEA', '#F3FFE3', '#F9E2AF']
MAIN_COLOR = '#B09B90'

# [강력한 폰트 주입 코드]
st.markdown("""
    <style>
    /* 1. 폰트 불러오기 (여러 경로 확보) */
    @import url('https://fonts.googleapis.com/css2?family=Nanum+Pen+Script&display=swap');
    @font-face {
        font-family: 'KyoboHandwriting2019';
        src: url('https://fastly.jsdelivr.net/gh/projectnoonnu/noonfonts_20-04@2.1/KyoboHandwriting2019.woff') format('woff');
        font-weight: normal;
        font-style: normal;
    }

    /* 2. 모든 요소에 폰트 및 크기 강제 적용 */
    /* * 기호를 사용하여 모든 태그를 타겟팅하고 !important로 최우선순위 부여 */
    * {
        font-family: 'KyoboHandwriting2019', 'Nanum Pen Script', cursive !important;
    }

    /* 3. 스트림릿 전용 폰트 사이즈 조정 (개별 설정보다 전체 스케일 조정) */
    html, body, [data-testid="stAppViewContainer"] {
        font-size: 15px !important; /* 기본 글자 크기 최적화 */
    }

    /* 제목 크기 대폭 하향 */
    .title-text { 
        font-size: 1.8rem !important; 
        font-weight: bold !important; 
        color: #5D574F !important;
        margin: 10px 0 !important;
    }

    /* 상단 탭 메뉴 글자 */
    .stTabs [data-baseweb="tab"] div {
        font-size: 1.1rem !important;
    }

    /* 캘린더 표 디자인 최적화 */
    .cal-table { 
        width: 100%; 
        border-collapse: collapse; 
        table-layout: fixed; 
        margin-top: 5px;
    }
    .cal-table th { 
        font-size: 0.8rem !important; 
        color: #B09B90 !important; 
        padding: 5px 0 !important;
        border-bottom: 1px solid #EEE !important;
    }
    .cal-table td { 
        border: 1px solid #F8F8F8 !important; 
        background: white !important; 
        height: 60px !important; 
        vertical-align: top !important; 
        padding: 2px !important; 
        text-align: center !important; 
    }
    .cal-date-num { 
        font-size: 0.7rem !important; 
        color: #BBB !important; 
        display: block !important; 
    }
    .cal-mood-sticker { 
        font-size: 1rem !important; 
        display: inline-block !important;
    }
    .is-today { 
        background-color: #FFF9F8 !important; 
        border: 1.5px solid #B09B90 !important; 
    }

    /* 버튼 및 입력창 크기 */
    .stButton>button { 
        width: 100% !important; 
        border-radius: 10px !important; 
        height: 2.8em !important; 
        font-size: 1rem !important;
        background-color: #B09B90 !important; 
        color: white !important;
    }
    .summary-box { 
        background: #F9F5F2 !important; 
        padding: 10px !important; 
        border-radius: 10px !important; 
        font-size: 0.95rem !important; 
        margin-top: 5px !important;
    }
    
    /* 이미지 갤러리 정방형 유지 */
    .gallery-img-container {
        width: 100%;
        aspect-ratio: 1/1;
        overflow: hidden;
        border-radius: 10px;
    }
    .gallery-img-container img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 데이터 및 이미지 처리 ---
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

# --- 3. 메뉴 구성 (탭) ---
tab_cal, tab_rec, tab_proj, tab_mood, tab_log = st.tabs(["📅", "📝", "🏺", "✨", "📊"])

# --- [TAB 1: 캘린더] ---
with tab_cal:
    c1, c2 = st.columns(2)
    with c1: sel_year = st.selectbox("년도", [2024, 2025, 2026], index=2)
    with c2: sel_month = st.selectbox("월", list(range(1, 13)), index=datetime.now().month-1)
    
    st.markdown(f"<div class='title-text'>{sel_month}월 모아보기</div>", unsafe_allow_html=True)
    
    cal_obj = calendar.monthcalendar(sel_year, sel_month)
    today_date = datetime.now().date()
    m_moods, work_days = [], 0
    
    html = '<table class="cal-table"><thead><tr>'
    for d_n in ["월", "화", "수", "목", "금", "토", "일"]: html += f'<th>{d_n}</th>'
    html += '</tr></thead><tbody>'
    
    for week in cal_obj:
        html += '<tr>'
        for day in week:
            if day == 0: html += '<td></td>'
            else:
                curr_date = date(sel_year, sel_month, day)
                logs = df[df['날짜'] == curr_date]
                stickers = "".join([f'<span class="cal-mood-sticker">{MOOD_DICT.get(m, "")}</span>' for m in logs['기분']]) if not logs.empty else ""
                if not logs.empty: m_moods.extend(logs['기분'].tolist()); work_days += 1
                t_cls = 'is-today' if curr_date == today_date else ''
                html += f'<td class="{t_cls}"><span class="cal-date-num">{day}</span>{stickers}</td>'
        html += '</tr>'
    st.markdown(html + '</tbody></table>', unsafe_allow_html=True)
    st.markdown(f"<div class='summary-box'>💡 이번 달은 {work_days}일 작업했어요!</div>", unsafe_allow_html=True)

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
                df = pd.concat([df, new_row], ignore_index=True); save_data(df); st.rerun()

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
                st.markdown(f'<div class="gallery-img-container">{"<img src=\'"+img_src+"\'>" if rep_row is not None else "No Photo"}</div>', unsafe_allow_html=True)
                st.markdown(f"**🏺 {t}**")
                with st.expander("상세 보기"):
                    for r_idx, row in p_logs.iterrows():
                        st.write(f"**{row['날짜']}** ({row['단계']})")
                        if st.button("삭제", key=f"del_{r_idx}"):
                            df = df.drop(index=r_idx); save_data(df); st.rerun()
    else: st.info("기록이 없습니다.")

# --- [TAB 4/5: 기분 및 리포트] ---
with tab_mood:
    st.subheader("✨ 기분 조각들")
    m_month = st.selectbox("월", list(range(1, 13)), index=datetime.now().month-1, key="sm_m")
    m_df = df.copy(); m_df['월'] = pd.to_datetime(m_df['날짜']).dt.month
    m_df = m_df[m_df['월'] == m_month]
    if not m_df.empty:
        mood_counts = m_df['기분'].value_counts()
        for m, emoji in MOOD_DICT.items():
            if m in mood_counts: st.write(f"{emoji} {m}: {mood_counts[m]}개")

with tab_log:
    st.subheader("📊 Dana's Report")
    if not df.empty:
        done_p = df[df['단계'] == "완성"]['작품명'].nunique()
        st.write(f"총 {done_p}개 작품을 완성했어요!")
        fig = go.Figure(data=[go.Pie(labels=df['기분'].value_counts().index, values=df['기분'].value_counts().values, hole=.6, marker=dict(colors=PASTEL_COLORS))])
        fig.update_layout(height=250, margin=dict(t=0, b=0, l=0, r=0), font=dict(family="Nanum Pen Script", size=18))
        st.plotly_chart(fig, use_container_width=True)

st.markdown("<br><br><br>", unsafe_allow_html=True)
