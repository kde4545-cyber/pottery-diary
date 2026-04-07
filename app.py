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

# CSS 디자인 (글자 크기 최적화 및 잘림 방지)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Nanum+Pen+Script&display=swap');
    
    /* 전체 폰트 적용 */
    html, body, [data-testid="stAppViewContainer"], .stMarkdown, p, span, label, input, select, textarea, button {
        font-family: 'Nanum Pen Script', cursive !important;
        font-size: 1.15rem !important; /* 글자 크기 적절히 하향 조정 */
        color: #5D574F;
    }

    /* 상단 메뉴(탭) 폰트 조절 */
    .stTabs [data-baseweb="tab-list"] button div {
        font-size: 1.5rem !important;
    }

    /* 제목 강조 */
    .title-text { 
        font-size: 1.8rem !important; 
        font-weight: bold; 
        color: #5D574F; 
        margin-bottom: 15px; 
    }
    .highlight { color: #D4A373; font-weight: bold; font-size: 1.3rem; }

    /* 캘린더 디자인 (모바일 가로 7열 고정) */
    .cal-table { width: 100%; border-collapse: collapse; table-layout: fixed; margin-bottom: 10px; }
    .cal-table th { text-align: center; font-size: 0.8rem; color: #B09B90; padding: 5px 0; }
    .cal-table td { 
        border: 1px solid #F0F0F0; 
        background: white; 
        height: 65px; 
        vertical-align: top; 
        padding: 3px; 
        text-align: center; 
    }
    .cal-date-num { font-size: 0.7rem; color: #CCC; display: block; }
    .cal-mood-container { display: flex; flex-wrap: wrap; justify-content: center; gap: 1px; }
    .cal-mood-sticker { font-size: 1rem; }
    .is-today { border: 2px solid #B09B90 !important; background-color: #FFF9F8 !important; }

    /* 갤러리 카드 */
    .gallery-card { background: white; border-radius: 15px; box-shadow: 0px 4px 12px rgba(0,0,0,0.05); margin-bottom: 15px; overflow: hidden; }
    .gallery-img-container { width: 100%; aspect-ratio: 1 / 1; overflow: hidden; }
    .gallery-img-container img { width: 100%; height: 100%; object-fit: cover; }
    .gallery-title { padding: 8px; font-size: 1.1rem; color: #444; font-weight: bold; }

    /* 버튼 스타일 */
    .stButton>button { 
        width: 100%; border-radius: 12px; height: 3em; 
        background-color: #B09B90; color: white; font-weight: bold; border: none;
    }
    .summary-box { background: #F9F5F2; padding: 15px; border-radius: 15px; border-left: 5px solid #B09B90; margin-top: 10px; }
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

# --- 3. 메뉴 구성 (이모지 탭) ---
tab_cal, tab_rec, tab_proj, tab_mood, tab_log = st.tabs(["📅", "📝", "🏺", "✨", "📊"])

# --- [TAB 1: 캘린더] ---
with tab_cal:
    col_y, col_m = st.columns(2)
    with col_y: sel_year = st.selectbox("년도", [2024, 2025, 2026], index=2)
    with col_m: sel_month = st.selectbox("월", list(range(1, 13)), index=datetime.now().month-1)
    
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
                day_logs = df[df['날짜'] == curr_date]
                stickers_html = '<div class="cal-mood-container">'
                if not day_logs.empty:
                    work_days += 1
                    for mood in day_logs['기분']:
                        stickers_html += f'<span class="cal-mood-sticker">{MOOD_DICT.get(mood, "")}</span>'
                        m_moods.append(mood)
                stickers_html += '</div>'
                t_cls = 'is-today' if curr_date == today_date else ''
                html += f'<td class="{t_cls}"><span class="cal-date-num">{day}</span>{stickers_html}</td>'
        html += '</tr>'
    st.markdown(html + '</tbody></table>', unsafe_allow_html=True)

    if work_days > 0:
        top_m = max(set(m_moods), key=m_moods.count)
        summary = f"이번 달은 총 {work_days}일 작업했어요. 기분은 주로 '{top_m}' {MOOD_DICT[top_m]}이네요!"
    else: summary = "기록을 채워볼까요?"
    st.markdown(f"<div class='summary-box'>**💡 {sel_month}월 요약**<br>{summary}</div>", unsafe_allow_html=True)

# --- [TAB 2: 오늘의 기록] ---
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
                df = pd.concat([df, new_row], ignore_index=True); save_data(df)
                st.balloons(); st.rerun()
            else: st.error("작품명을 적어주세요!")

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
            is_done = "완성" in p_logs['단계'].values
            rep_row = p_logs[p_logs['사진1'] != ""].iloc[-1] if not p_logs[p_logs['사진1'] != ""].empty else None
            
            with proj_cols[idx % 2]:
                img_src = f"data:image/jpeg;base64,{rep_row['사진1']}" if rep_row is not None else ""
                st.markdown(f'<div class="gallery-card"><div class="gallery-img-container">{"<img src=\'"+img_src+"\'>" if rep_row is not None else "No Photo"}</div><div class="gallery-title">🏺 {t} {"(완성)" if is_done else ""}</div></div>', unsafe_allow_html=True)
                with st.expander("상세 기록"):
                    for r_idx, row in p_logs.iterrows():
                        st.caption(f"{row['날짜']} | {row['단계']}")
                        if row['내용']: st.write(row['내용'])
                        for img_col in ['사진1', '사진2', '사진3']:
                            if pd.notna(row[img_col]) and row[img_col] != "":
                                st.image(base64.b64decode(row[img_col]), use_container_width=True)
                        if st.button("삭제", key=f"del_{r_idx}"):
                            df = df.drop(index=r_idx); save_data(df); st.rerun()
    else: st.info("기록이 없습니다.")

# --- [TAB 4/5: 기분 및 통계] ---
with tab_mood:
    st.subheader("✨ 기분 조각들")
    m_month = st.selectbox("월 선택", list(range(1, 13)), index=datetime.now().month-1, key="sm_mood")
    m_df = df.copy(); m_df['월'] = pd.to_datetime(m_df['날짜']).dt.month
    m_df = m_df[m_df['월'] == m_month]
    if not m_df.empty:
        m_counts = m_df['기분'].value_counts()
        m_grid = st.columns(4)
        for i, (m, emoji) in enumerate(MOOD_DICT.items()):
            cnt = m_counts.get(m, 0)
            with m_grid[i % 4]: st.write(f"{emoji} {m}: {cnt}개")

with tab_log:
    st.subheader("📊 기록 요약")
    if not df.empty:
        total_p = df['작품명'].nunique(); done_p = df[df['단계'] == "완성"]['작품명'].nunique()
        st.markdown(f"<div class='dana-card'>지금까지 총 <span class='highlight'>{done_p}개</span>를 완성했어요!</div>", unsafe_allow_html=True)
        mood_counts = df['기분'].value_counts()
        fig = go.Figure(data=[go.Pie(labels=mood_counts.index, values=mood_counts.values, hole=.6, marker=dict(colors=PASTEL_COLORS))])
        fig.update_layout(showlegend=True, height=300, font=dict(family="Nanum Pen Script", size=18))
        st.plotly_chart(fig, use_container_width=True)
