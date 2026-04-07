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

    /* 기분 조각들 전용 표 스타일 */
    .mood-table {{
        width: 100%;
        border-collapse: collapse;
        table-layout: fixed;
        margin-top: 15px;
    }}
    .mood-table td {{
        text-align: center;
        padding: 10px 2px;
        background: white;
        border: 1px solid #F0F0F0;
        border-radius: 15px; /* 작동 안 할 수 있음 (td 특성상) */
    }}

    .gallery-card {{ background: white; border-radius: 15px; box-shadow: 0px 4px 12px rgba(0,0,0,0.05); margin-bottom: 20px; overflow: hidden; }}
    .gallery-img-container {{ width: 100%; aspect-ratio: 1 / 1; overflow: hidden; background-color: #F8F8F8; }}
    .gallery-img-container img {{ width: 100%; height: 100%; object-fit: cover; }}
    .cal-table {{ width: 100%; border-collapse: collapse; table-layout: fixed; }}
    .cal-table th {{ text-align: center; font-size: 0.7em; color: {MAIN_COLOR}; padding: 5px 0; }}
    .cal-table td {{ border: 1px solid #F0F0F0; background: white; height: 55px; vertical-align: top; padding: 4px 1px; text-align: center; }}
    .is-today {{ background-color: #FFF9F8 !important; border: 2px solid {MAIN_COLOR} !important; }}
    .summary-box {{ background: #F9F5F2; padding: 15px; border-radius: 15px; border-left: 5px solid {MAIN_COLOR}; margin-top: 10px; }}
    .highlight {{ color: #D4A373; font-weight: 800; font-size: 1.15em; }}
    .title-text {{ font-size: 1.5em; font-weight: 800; color: #5D574F; margin-bottom: 15px; }}
    .stButton>button {{ width: 100%; border-radius: 12px; height: 3.5em; background-color: {MAIN_COLOR}; color: white; font-weight: bold; border: none; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. 데이터 및 이미지 로직 ---
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

# --- 3. 메뉴 구성 ---
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
                sticker_html = "".join([f'<span style="font-size:1.1em;">{MOOD_DICT.get(m, "")}</span>' for m in logs['기분']]) if not logs.empty else ""
                if not logs.empty: m_moods.extend(logs['기분'].tolist()); work_days += 1
                t_cls = 'is-today' if curr_date == today_date else ''
                html += f'<td class="{t_cls}"><span style="font-size:0.6em; color:#CCC;">{day}</span><br>{sticker_html}</td>'
        html += '</tr>'
    st.markdown(html + '</tbody></table>', unsafe_allow_html=True)
    st.markdown(f"<div class='summary-box'>**💡 {sel_month}월 요약**<br>{'총 '+str(work_days)+'일 작업했어요.' if work_days>0 else '기록이 없어요.'}</div>", unsafe_allow_html=True)

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
        p_cols = st.columns(2)
        for idx, t in enumerate(display_titles):
            p_logs = df[df['작품명'] == t].sort_values(by=['날짜'])
            is_done = "완성" in p_logs['단계'].values
            rep_row = p_logs[p_logs['사진1'] != ""].iloc[-1] if not p_logs[p_logs['사진1'] != ""].empty else None
            with p_cols[idx % 2]:
                img_src = f"data:image/jpeg;base64,{rep_row['사진1']}" if rep_row is not None else ""
                st.markdown(f'<div class="gallery-card"><div class="gallery-img-container">{"<img src=\'"+img_src+"\'>" if rep_row is not None else "<div style=\'padding:40% 10%; color:#ccc;\'>No Photo</div>"}</div><div style="padding:8px; font-weight:bold; font-size:0.9em;">🏺 {t} {"<span class=\'complete-badge\'>완성</span>" if is_done else ""}</div></div>', unsafe_allow_html=True)
                with st.expander("과정 보기/수정"):
                    for r_idx, row in p_logs.iterrows():
                        st.caption(f"{row['날짜']} | {row['단계']}")
                        p_img_cols = st.columns(3)
                        for i, ic in enumerate(['사진1', '사진2', '사진3']):
                            if pd.notna(row[ic]) and row[ic] != "": p_img_cols[i].image(base64.b64decode(row[ic]), use_container_width=True)
                        if row['내용']: st.write(row['내용'])
                        btn_c1, btn_c2 = st.columns(2)
                        with btn_c1:
                            with st.popover("✏️ 수정"):
                                with st.form(f"edit_f_{r_idx}"):
                                    e_mood = st.radio("기분", list(MOOD_DICT.keys()), index=list(MOOD_DICT.keys()).index(row['기분']), horizontal=True, format_func=lambda x: MOOD_DICT[x])
                                    e_date = st.date_input("날짜", row['날짜'])
                                    e_title = st.text_input("작품명", row['작품명'])
                                    e_note = st.text_area("메모", row['내용'])
                                    photo_opt = st.radio("사진", ["유지", "교체"], horizontal=True)
                                    new_i = st.file_uploader("교체용 사진", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
                                    if st.form_submit_button("저장"):
                                        df.at[r_idx, '기분'], df.at[r_idx, '날짜'], df.at[r_idx, '작품명'], df.at[r_idx, '내용'] = e_mood, e_date, e_title, e_note
                                        if photo_opt == "교체":
                                            img_list = [process_img(new_i[j]) if j < len(new_i) else "" for j in range(3)]
                                            df.at[r_idx, '사진1'], df.at[r_idx, '사진2'], df.at[r_idx, '사진3'] = img_list[0], img_list[1], img_list[2]
                                        save_data(df); st.rerun()
                        with btn_c2:
                            with st.popover("🗑️ 삭제"):
                                if st.button("삭제 확인", key=f"d_{r_idx}"): df = df.drop(index=r_idx); save_data(df); st.rerun()
                        st.divider()

# --- [TAB 4: 기분 조각들 - 표 방식으로 전면 수정] ---
with tab_mood:
    st.markdown("<div class='title-text'>기분 조각들</div>", unsafe_allow_html=True)
    
    mood_mode = st.radio("모아보기 기준", ["📅 월별", "🏺 작품별"], horizontal=True)
    
    if mood_mode == "📅 월별":
        m_val = st.selectbox("월 선택", list(range(1, 13)), index=datetime.now().month-1)
        m_df = df.copy()
        m_df['월'] = pd.to_datetime(m_df['날짜']).dt.month
        filtered_df = m_df[m_df['월'] == m_val]
        title_msg = f"🎯 **{m_val}월** 감정 모음"
    else:
        p_val = st.selectbox("작품 선택", sorted(df['작품명'].unique()) if not df.empty else ["없음"])
        filtered_df = df[df['작품명'] == p_val]
        title_msg = f"🎯 **{p_val}** 작업 전체 기간 감정 모음"
    
    st.write(title_msg)
    
    if not filtered_df.empty:
        mood_counts = filtered_df['기분'].value_counts()
        
        # 가로 4칸짜리 표로 구성 (HTML 노출 방지 위해 더 깔끔하게 작성)
        items = list(MOOD_DICT.items())
        mood_table_html = '<table class="mood-table"><tr>'
        
        for i, (m_name, emoji) in enumerate(items):
            cnt = mood_counts.get(m_name, 0)
            if i == 4: # 4개 채우면 다음 줄로
                mood_table_html += '</tr><tr>'
            mood_table_html += f'''
                <td>
                    <div style="font-size:1.5em;">{emoji}</div>
                    <div style="font-size:0.75em; color:#666; margin:2px 0;">{m_name}</div>
                    <div style="font-weight:bold; color:{MAIN_COLOR};">{cnt}</div>
                </td>
            '''
        # 빈 칸 채우기 (나머지 칸)
        for _ in range(8 - len(items)):
            mood_table_html += '<td></td>'
            
        mood_table_html += '</tr></table>'
        st.markdown(mood_table_html, unsafe_allow_html=True)
    else:
        st.info("데이터가 없습니다.")

# --- [TAB 5: Dana's Log] ---
with tab_log:
    st.markdown("<div class='title-text'>DANA의 기록 요약</div>", unsafe_allow_html=True)
    if not df.empty:
        total_p = df['작품명'].nunique(); done_p = df[df['단계'] == "완성"]['작품명'].nunique(); ing_p = total_p - done_p
        top_m = df['기분'].mode()[0] if not df['기분'].empty else "-"; top_o = df['기물종류'].mode()[0] if not df['기물종류'].empty else "-"
        st.markdown(f"""<div class="dana-card"><p style='line-height:1.8;'>지금까지 Dana님은...<br>총 <span class="highlight">{done_p}개</span>를 완성하고,<br>지금은 <span class="highlight">{ing_p}개</span>를 빚고 있어요. 🕊️<br>주로 <span class="highlight">'{top_m}' {MOOD_DICT.get(top_m, '')}</span> 마음이었고,<br>주력 기물은 <span class="highlight">'{top_o}'</span>이에요!</p></div>""", unsafe_allow_html=True)
        mood_counts = df['기분'].value_counts()
        fig = go.Figure(data=[go.Pie(labels=mood_counts.index, values=mood_counts.values, hole=.6, marker=dict(colors=PASTEL_COLORS))])
        fig.update_layout(showlegend=True, margin=dict(t=10, b=10, l=10, r=10), height=280, legend=dict(orientation="h", y=-0.1))
        st.plotly_chart(fig, use_container_width=True)

st.markdown("<br><br><br>", unsafe_allow_html=True)
