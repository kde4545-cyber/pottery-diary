import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
import base64
from io import BytesIO
from PIL import Image, ImageOps
import calendar
import plotly.graph_objects as go

# --- 1. 페이지 설정 ---
st.set_page_config(page_title="Dana's Pottery Log", layout="centered")

# --- 2. 강력한 교보손글씨 주입 및 디자인 (글자 크기 축소) ---
st.markdown("""
    <style>
    /* 폰트 정의: 교보손글씨 2019 하나만 로드 */
    @font-face {
        font-family: 'KyoboHandwriting2019';
        src: url('https://cdn.jsdelivr.net/gh/projectnoonnu/noonfonts_20-04@2.1/KyoboHandwriting2019.woff') format('woff');
        font-weight: normal;
        font-style: normal;
    }

    /* 모든 요소에 교보손글씨 강제 적용 및 명조체 원천 차단 */
    * {
        font-family: 'KyoboHandwriting2019' !important;
    }

    html, body, [data-testid="stAppViewContainer"], .stMarkdown, p, div, span, label, input, select, textarea, button, .st-ae {
        font-family: 'KyoboHandwriting2019' !important;
        font-size: 0.95rem !important; /* 전체 글자 크기 더 작고 정갈하게 조정 */
        color: #5D574F !important;
        letter-spacing: -0.02em !important;
    }

    /* 제목 및 탭 메뉴 크기 조정 */
    .title-text { 
        font-size: 1.6rem !important; 
        font-weight: bold !important; 
        margin: 10px 0 !important;
    }
    .stTabs [data-baseweb="tab"] div {
        font-size: 1.2rem !important;
    }

    /* 캘린더 디자인 (모바일 7열 강제 고정) */
    .cal-table { width: 100%; border-collapse: collapse; table-layout: fixed; }
    .cal-table th { font-size: 0.8rem !important; color: #B09B90 !important; padding: 5px 0; font-weight: bold; }
    .cal-table td { 
        border: 1px solid #F2F2F2 !important; background: white !important; 
        height: 60px !important; vertical-align: top; padding: 2px; text-align: center; 
    }
    .cal-date-num { font-size: 0.65rem !important; color: #CCC !important; display: block; margin-bottom: 2px; }
    .cal-mood-sticker { font-size: 1.1rem !important; display: inline-block; margin: 1px; }
    .is-today { border: 2px solid #B09B90 !important; background-color: #FFF9F8 !important; }

    /* 갤러리 정방형 디자인 */
    .gallery-img-container {
        width: 100%;
        aspect-ratio: 1/1;
        overflow: hidden;
        border-radius: 12px;
        background-color: #F8F8F8;
    }
    .gallery-img-container img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    .complete-badge {
        background-color: #E2F0CB;
        color: #5D8A66;
        font-size: 0.65rem !important;
        padding: 2px 6px;
        border-radius: 5px;
        font-weight: bold;
    }

    /* 버튼 및 입력창 */
    .stButton>button { 
        width: 100% !important; border-radius: 12px !important; height: 3em !important; 
        background-color: #B09B90 !important; color: white !important; font-size: 1rem !important;
    }
    .summary-box { 
        background: #F9F5F2 !important; padding: 12px !important; border-radius: 12px !important; 
        border-left: 4px solid #B09B90 !important; margin-top: 10px !important; font-size: 0.95rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 데이터 및 이미지 처리 로직 ---
DATA_FILE = "pottery_diary_v4.csv"
MOOD_DICT = {"행복": "😊", "기쁨": "😄", "절망": "😱", "슬픔": "😢", "화이팅": "🔥", "실망": "😞", "감격": "😭"}
PASTEL_COLORS = ['#FFB7B2', '#FFDAC1', '#E2F0CB', '#B5EAD7', '#C7CEEA', '#F3FFE3', '#F9E2AF']

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
    # 정중앙 정방형 크롭
    img = ImageOps.fit(img, (800, 800), Image.Resampling.LANCZOS)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=80)
    return base64.b64encode(buf.getvalue()).decode()

df = load_data()

# --- 4. 메뉴 구성 ---
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
                stickers_html = "".join([f'<span class="cal-mood-sticker">{MOOD_DICT.get(m, "")}</span>' for m in logs['기분']]) if not logs.empty else ""
                if not logs.empty: m_moods.extend(logs['기분'].tolist()); work_days += 1
                t_cls = 'is-today' if curr_date == today_date else ''
                html += f'<td class="{t_cls}"><span class="cal-date-num">{day}</span>{stickers_html}</td>'
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
        if st.form_submit_button("기록 저장하기"):
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
            is_done = "완성" in p_logs['단계'].values
            rep_row = p_logs[p_logs['사진1'] != ""].iloc[-1] if not p_logs[p_logs['사진1'] != ""].empty else None
            with proj_cols[idx % 2]:
                img_src = f"data:image/jpeg;base64,{rep_row['사진1']}" if rep_row is not None else ""
                st.markdown(f'<div class="gallery-img-container">{"<img src=\'"+img_src+"\'>" if rep_row is not None else "<div style=\'padding:40% 0; text-align:center; color:#ccc;\'>No Photo</div>"}</div>', unsafe_allow_html=True)
                st.markdown(f"**🏺 {t}** {'<span class=\"complete-badge\">완성</span>' if is_done else ''}", unsafe_allow_html=True)
                with st.expander("과정 보기"):
                    for r_idx, row in p_logs.iterrows():
                        st.write(f"**{row['날짜']}** [{row['단계']}]")
                        for ic in ['사진1', '사진2', '사진3']:
                            if pd.notna(row[ic]) and row[ic] != "": st.image(base64.b64decode(row[ic]), use_container_width=True)
                        if st.button("삭제", key=f"del_{r_idx}"):
                            df = df.drop(index=r_idx); save_data(df); st.rerun()
    else: st.info("기록이 없습니다.")

# --- [TAB 4: 기분 조각들] ---
with tab_mood:
    st.markdown("<div class='title-text'>기분 조각들</div>", unsafe_allow_html=True)
    m_month = st.selectbox("월 선택", list(range(1, 13)), index=datetime.now().month-1, key="final_m")
    m_df = df.copy(); m_df['월'] = pd.to_datetime(m_df['날짜']).dt.month
    m_df = m_df[m_df['월'] == m_month]
    if not m_df.empty:
        mood_counts = m_df['기분'].value_counts()
        for m, emoji in MOOD_DICT.items():
            if m in mood_counts: st.write(f"{emoji} {m}: {mood_counts[m]}개")

# --- [TAB 5: 요약 리포트] ---
with tab_log:
    st.markdown("<div class='title-text'>Dana's Log</div>", unsafe_allow_html=True)
    if not df.empty:
        total_p = df['작품명'].nunique(); done_p = df[df['단계'] == "완성"]['작품명'].nunique(); ing_p = total_p - done_p
        top_m = df['기분'].mode()[0] if not df['기분'].empty else "-"; top_o = df['기물종류'].mode()[0] if not df['기물종류'].empty else "-"
        st.markdown(f"""
        <div class="summary-box">
            지금까지 Dana님은 총 {done_p}개를 완성했고,<br>
            지금은 {ing_p}개를 정성껏 빚고 있어요. ✨<br>
            주로 흙을 만질 때 '{top_m}' 마음이었고,<br>
            제일 많이 만든 건 '{top_o}'이에요!
        </div>
        """, unsafe_allow_html=True)
        fig = go.Figure(data=[go.Pie(labels=df['기분'].value_counts().index, values=df['기분'].value_counts().values, hole=.6, marker=dict(colors=PASTEL_COLORS))])
        fig.update_layout(height=280, font=dict(family="KyoboHandwriting2019", size=18))
        st.plotly_chart(fig, use_container_width=True)

st.markdown("<br><br><br>", unsafe_allow_html=True)
