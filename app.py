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
    
    .stTabs [data-baseweb="tab-list"] {{ justify-content: space-around; border-bottom: none; }}
    .stTabs [data-baseweb="tab"] {{ flex-grow: 1; text-align: center; }}
    .stTabs [data-baseweb="tab-list"] button div {{ font-size: 1.4rem !important; }}

    /* 인스타그램형 3x3 그리드 강제 고정 */
    div[data-testid="stHorizontalBlock"].insta-grid {{
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: wrap !important;
        gap: 4px !important;
        justify-content: flex-start !important;
    }}
    div[data-testid="stHorizontalBlock"].insta-grid > div[data-testid="column"] {{
        flex: 0 0 calc(33.333% - 4px) !important;
        min-width: calc(33.333% - 4px) !important;
        max-width: calc(33.333% - 4px) !important;
    }}

    .insta-box {{
        width: 100%;
        aspect-ratio: 1/1;
        overflow: hidden;
        border-radius: 8px;
        background-color: #F0F0F0;
        border: 1px solid #EEE;
    }}
    .insta-box img {{ width: 100%; height: 100%; object-fit: cover; }}
    .insta-empty {{ background-color: #F6F6F6; border: 1px dashed #DDD; }}

    .cal-table {{ width: 100%; border-collapse: collapse; table-layout: fixed; margin-bottom: 10px; }}
    .cal-table td {{ border: 1px solid #F2F2F2; background: white; height: 60px; vertical-align: top; text-align: center; padding: 2px; }}
    .has-rec {{ background-color: #F9F5F2 !important; }}

    .dana-card {{ background: white; padding: 20px; border-radius: 20px; box-shadow: 0px 8px 20px rgba(0,0,0,0.03); margin-bottom: 20px; }}
    .summary-box {{ background: #F9F5F2; padding: 15px; border-radius: 15px; border-left: 5px solid {MAIN_COLOR}; margin-top: 10px; line-height: 1.6; }}
    .highlight {{ color: #D4A373; font-weight: 800; font-size: 1.1em; }}
    .title-text {{ font-size: 1.5em; font-weight: 800; color: #5D574F; margin-bottom: 15px; }}
    .stButton>button {{ width: 100%; border-radius: 12px; height: 3.5em; background-color: {MAIN_COLOR}; color: white; font-weight: bold; border: none; }}
    
    /* 그리드용 작은 버튼 스타일 */
    .grid-btn button {{
        height: 25px !important;
        font-size: 0.7em !important;
        margin-top: 2px !important;
        background-color: #E6DED8 !important;
        color: #5D574F !important;
    }}
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
month_opts = [f"{y}년 {m:02d}월" for y in [2025, 2026] for m in range(1, 13) if not (y == 2026 and m > 4)]
if 'sel_m_idx' not in st.session_state: st.session_state.sel_m_idx = len(month_opts) - 1
if 'selected_project' not in st.session_state: st.session_state.selected_project = None

# --- 3. 메뉴 구성 ---
tab_cal, tab_list, tab_rec, tab_proj, tab_mood, tab_log = st.tabs(["📅", "📜", "📝", "🏺", "✨", "📊"])

# --- [TAB 1: 📅 월간 모아보기] ---
with tab_cal:
    c1, c2, c3 = st.columns([1, 6, 1])
    with c1:
        if st.button("◀", key="cp"):
            if st.session_state.sel_m_idx > 0: st.session_state.sel_m_idx -= 1; st.rerun()
    with c2:
        m_str = st.selectbox("월", month_opts, index=st.session_state.sel_m_idx, label_visibility="collapsed", key="cs")
        st.session_state.sel_m_idx = month_opts.index(m_str)
    with c3:
        if st.button("▶", key="cn"):
            if st.session_state.sel_m_idx < len(month_opts)-1: st.session_state.sel_m_idx += 1; st.rerun()
    y_v, m_v = int(m_str[:4]), int(m_str[6:8])
    st.markdown(f"<div class='title-text'>{m_v}월 모아보기</div>", unsafe_allow_html=True)
    cal_data = calendar.monthcalendar(y_v, m_v)
    h_cal = '<table class="cal-table"><thead><tr>'
    for d_n in ["월", "화", "수", "목", "금", "토", "일"]: h_cal += f'<th>{d_n}</th>'
    h_cal += '</tr></thead><tbody>'
    for week in cal_data:
        h_cal += '<tr>'
        for day in week:
            if day == 0: h_cal += '<td></td>'
            else:
                logs = df[df['날짜'] == date(y_v, m_v, day)]
                td_cls = "has-rec" if not logs.empty else ""
                thumb = f'<img src="data:image/jpeg;base64,{logs.iloc[-1]["사진1"]}" style="width:30px;height:30px;object-fit:cover;border-radius:4px;">' if not logs.empty and pd.notna(logs.iloc[-1]['사진1']) else ""
                h_cal += f'<td class="{td_cls}"><span style="font-size:0.6em;color:#CCC;display:block;">{day}</span>{thumb}</td>'
        h_cal += '</tr>'
    st.markdown(h_cal + '</tbody></table>', unsafe_allow_html=True)

# --- [TAB 2: 📜 기록 모아보기 - 수정 기능 추가] ---
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
                
                # 수정 및 삭제 버튼
                ec1, ec2 = st.columns(2)
                with ec1:
                    with st.popover("✏️ 내용 수정"):
                        with st.form(f"edit_f_{idx}"):
                            e_date = st.date_input("날짜", row['날짜'])
                            e_title = st.text_input("작품명", row['작품명'])
                            e_step = st.selectbox("단계", ["성형", "건조", "초벌", "시유", "완성"], index=["성형", "건조", "초벌", "시유", "완성"].index(row['단계']))
                            e_mood = st.selectbox("기분", list(MOOD_DICT.keys()), index=list(MOOD_DICT.keys()).index(row['기분']))
                            e_note = st.text_area("메모", row['내용'])
                            if st.form_submit_button("수정 저장"):
                                df.at[idx, '날짜'], df.at[idx, '작품명'], df.at[idx, '단계'], df.at[idx, '기분'], df.at[idx, '내용'] = e_date, e_title, e_step, e_mood, e_note
                                save_data(df); st.rerun()
                with ec2:
                    if st.button("🗑️ 삭제", key=f"dl_{idx}"): df = df.drop(index=idx); save_data(df); st.rerun()

# --- [TAB 3: 📝 기록하기] ---
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
                new_d = pd.DataFrame([[r_date, r_title, r_clay, r_step, r_note, img_l[0], img_l[1], img_l[2], mood, r_type, r_obj]], columns=df.columns)
                df = pd.concat([df, new_d], ignore_index=True); save_data(df); st.balloons(); st.rerun()

# --- [TAB 4: 🏺 작품 모아보기 - 9칸 그리드 & 클릭 상세] ---
with tab_proj:
    st.markdown("<div class='title-text'>작품 모아보기</div>", unsafe_allow_html=True)
    p_filter = st.radio("상태 필터", ["전체", "작업중", "완성"], horizontal=True, key="pf_insta")
    
    unique_titles = df['작품명'].unique()[::-1] if not df.empty else []
    display_list = []
    for t in unique_titles:
        is_done = "완성" in df[df['작품명'] == t]['단계'].values
        if (p_filter == "작업중" and is_done) or (p_filter == "완성" and not is_done): continue
        display_list.append(t)

    # 3x3 그리드 표시 (제목 제거)
    st.markdown('<div class="insta-grid">', unsafe_allow_html=True)
    cols = st.columns(3)
    for i in range(max(9, len(display_list))):
        with cols[i % 3]:
            if i < len(display_list):
                t = display_list[i]
                p_logs = df[df['작품명'] == t].sort_values(by='날짜')
                rep = p_logs[p_logs['사진1'] != ""].iloc[-1] if not p_logs[p_logs['사진1'] != ""].empty else None
                src = f"data:image/jpeg;base64,{rep['사진1']}" if rep is not None else ""
                st.markdown(f'<div class="insta-box">{"<img src=\'"+src+"\'>" if src else "No Pic"}</div>', unsafe_allow_html=True)
                st.markdown('<div class="grid-btn">', unsafe_allow_html=True)
                if st.button("🔍 보기", key=f"view_{t}"):
                    st.session_state.selected_project = t
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="insta-box insta-empty"></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # 선택된 작품 상세 정보 표시 (그리드 하단)
    if st.session_state.selected_project:
        st.divider()
        st.subheader(f"🏺 {st.session_state.selected_project}의 히스토리")
        p_history = df[df['작품명'] == st.session_state.selected_project].sort_values(by='날짜')
        for _, r in p_history.iterrows():
            st.markdown(f"**{r['날짜']}** | {r['단계']}")
            st.caption(r['내용'])
            icols = st.columns(3)
            for i, cn in enumerate(['사진1', '사진2', '사진3']):
                if pd.notna(r[cn]) and r[cn] != "": icols[i].image(base64.b64decode(r[cn]), use_container_width=True)
            st.divider()

# --- [TAB 5: ✨ 기분 조각들] ---
with tab_mood:
    st.markdown("<div class='title-text'>기분 조각들</div>", unsafe_allow_html=True)
    mood_mode = st.radio("분석 기준", ["📅 월별", "🏺 작품별"], horizontal=True)
    if mood_mode == "📅 월별":
        sel_m = st.selectbox("분석 월 선택", month_opts, index=st.session_state.sel_m_idx, key="m_s")
        v_m = int(sel_m[6:8]); f_df = df[pd.to_datetime(df['날짜']).dt.month == v_m]; d_n = f"{v_m}월"
    else:
        p_v = st.selectbox("작품 선택", sorted(df['작품명'].unique()) if not df.empty else ["없음"], key="p_s")
        f_df = df[df['작품명'] == p_v]; d_n = p_v
        if not f_df.empty and pd.notna(f_df.iloc[-1]['사진1']):
            st.markdown(f'<div style="width:100px; margin:0 auto 10px;"><div class="insta-box"><img src="data:image/jpeg;base64,{f_df.iloc[-1]["사진1"]}"></div></div>', unsafe_allow_html=True)
    if not f_df.empty:
        mood_counts = f_df['기분'].value_counts(); total_m = len(f_df)
        st.markdown(f"<div class='summary-box'>✨ {d_n}에는 주로 <b>'{mood_counts.idxmax()}'</b>였네요!</div>", unsafe_allow_html=True)
        items = list(MOOD_DICT.items()); h_mood = '<table style="width:100%; table-layout:fixed; border-collapse:collapse; margin-top:10px;"><tr>'
        for i, (name, emoji) in enumerate(items):
            cnt = mood_counts.get(name, 0); pct = int(cnt/total_m*100)
            if i == 4: h_mood += '</tr><tr>'
            h_mood += f'<td style="text-align:center; padding:8px 2px; background:white; border:1px solid #F8F8F8;"><div style="font-size:1.2em;">{emoji}</div><div style="font-size:0.7em; color:#888;">{name}</div><div style="font-weight:bold; color:{MAIN_COLOR}; font-size:0.8em;">{pct}%</div><div style="font-size:0.5em; color:#CCC;">({cnt}회)</div></td>'
        st.markdown(h_mood + '<td></td></tr></table>', unsafe_allow_html=True)

# --- [TAB 6: 📊 DANA의 기록 요약] ---
with tab_log:
    st.markdown("<div class='title-text'>DANA의 기록 요약</div>", unsafe_allow_html=True)
    if not df.empty:
        done_p = df[df['단계'] == "완성"]['작품명'].nunique(); ing_p = df['작품명'].nunique() - done_p
        st.markdown(f"""
        <div class="dana-card">
            <p style='line-height:1.8;'>지금까지 Dana님은...<br>총 <span class="highlight">{done_p}개</span>의 작품을 완성하고,<br>지금은 <span class="highlight">{ing_p}개</span>의 아이들을 빚고 있어요. ✨<br>주로 흙을 만질 때 <span class="highlight">'{df['기분'].mode()[0]}'</span> 마음이었고,<br>가장 많이 만든 건 <span class="highlight">'{df['기물종류'].mode()[0]}'</span>이에요!</p>
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
