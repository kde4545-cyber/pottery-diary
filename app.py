import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
import base64
from io import BytesIO
from PIL import Image, ImageOps
import calendar
import plotly.graph_objects as go

# --- 1. 페이지 설정 및 디자인 (가장 안정적인 Pretendard로 복구) ---
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
    
    /* 상단 메뉴바 균등 정렬 복구 */
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

    /* 7열 고정 달력 디자인 (HTML Table 방식 - 모바일 절대 고정) */
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
    .cal-date-num {{ font-size: 0.7em; color: #CCC; display: block; text-align: left; }}
    .has-rec {{ background-color: #F9F5F2 !important; }}
    .cal-thumb {{ width: 32px; height: 32px; object-fit: cover; border-radius: 4px; margin-top: 2px; }}
    .cal-plus {{ position: absolute; bottom: 2px; right: 2px; font-size: 0.6em; color: {MAIN_COLOR}; font-weight: bold; }}

    /* 카드 및 요약 박스 */
    .summary-box {{ background: #F9F5F2; padding: 15px; border-radius: 15px; border-left: 5px solid {MAIN_COLOR}; margin-top: 10px; line-height: 1.6; }}
    .dana-card {{ background: white; padding: 20px; border-radius: 20px; box-shadow: 0px 8px 20px rgba(0,0,0,0.03); margin-bottom: 20px; }}
    .title-text {{ font-size: 1.5em; font-weight: 800; color: #5D574F; margin-bottom: 15px; }}
    .highlight {{ color: #D4A373; font-weight: 800; font-size: 1.15em; }}

    /* 이미지 갤러리 정방형 */
    .gallery-img-container {{ width: 100%; aspect-ratio: 1/1; overflow: hidden; border-radius: 12px; background-color: #F8F8F8; }}
    .gallery-img-container img {{ width: 100%; height: 100%; object-fit: cover; }}
    
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

# 년월 리스트 생성 (25년 01월 ~ 26년 04월)
month_opts = []
for y in [2025, 2026]:
    for m in range(1, 13):
        if y == 2026 and m > 4: break
        month_opts.append(f"{y}년 {m:02d}월")

if 'sel_month_idx' not in st.session_state: st.session_state.sel_month_idx = len(month_opts) - 1

# --- 3. 메뉴 구성 (6단 탭) ---
tabs = st.tabs(["📅", "📜", "📝", "🏺", "✨", "📊"])
tab_cal, tab_list, tab_rec, tab_proj, tab_mood, tab_log = tabs

# --- [TAB 1: 📅 월간 모아보기] ---
with tab_cal:
    nav_c1, nav_c2, nav_c3 = st.columns([1, 6, 1])
    with nav_c1:
        if st.button("◀", key="p_m"):
            if st.session_state.sel_month_idx > 0: st.session_state.sel_month_idx -= 1; st.rerun()
    with nav_c2:
        month_str = st.selectbox("월", month_opts, index=st.session_state.sel_month_idx, label_visibility="collapsed")
        st.session_state.sel_month_idx = month_opts.index(month_str)
    with nav_c3:
        if st.button("▶", key="n_m"):
            if st.session_state.sel_month_idx < len(month_opts) - 1: st.session_state.sel_month_idx += 1; st.rerun()

    view_y, view_m = int(month_str[:4]), int(month_str[6:8])
    st.markdown(f"<div class='title-text'>{view_m}월 모아보기</div>", unsafe_allow_html=True)
    
    # 캘린더 (Table 방식 - 모바일 고정)
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

# --- [TAB 2: 📜 기록 모아보기 - 최신순 리스트] ---
with tab_list:
    st.markdown("<div class='title-text'>기록 모아보기</div>", unsafe_allow_html=True)
    if not df.empty:
        # 최신 날짜순 정렬
        sorted_df = df.sort_values(by='날짜', ascending=False)
        for idx, row in sorted_df.iterrows():
            with st.container():
                st.markdown(f"""
                <div class="summary-box">
                    <span style="font-size:1.2em;">{MOOD_DICT.get(row['기분'], '')}</span> <b>{row['작품명']}</b> | {row['단계']}<br>
                    <small>{row['날짜']} | {row['작업유형']} | {row['기물종류']}</small><br>
                    <p style="margin-top:5px;">{row['내용']}</p>
                </div>
                """, unsafe_allow_html=True)
                img_cols = st.columns(3)
                for i, c_n in enumerate(['사진1', '사진2', '사진3']):
                    if pd.notna(row[c_n]) and row[c_n] != "":
                        img_cols[i].image(base64.b64decode(row[c_n]), use_container_width=True)
                
                # 수정/삭제 버튼
                btn_c1, btn_c2 = st.columns(2)
                with btn_c1:
                    with st.popover("✏️ 수정"):
                        with st.form(f"edit_{idx}"):
                            new_note = st.text_area("내용 수정", row['내용'])
                            if st.form_submit_button("수정 저장"):
                                df.at[idx, '내용'] = new_note
                                save_data(df); st.rerun()
                with btn_c2:
                    if st.button("🗑️ 삭제", key=f"list_del_{idx}"):
                        df = df.drop(index=idx); save_data(df); st.rerun()
                st.divider()
    else:
        st.info("아직 기록이 없습니다.")

# --- [TAB 3: 📝 오늘의 작업 기록] ---
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
        r_imgs = st.file_uploader("사진(최대 3장)", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
        r_note = st.text_area("메모")
        if st.form_submit_button("기록 저장하기"):
            if r_title:
                img_l = [process_img(r_imgs[i]) if i < len(r_imgs) else "" for i in range(3)]
                new_data = pd.DataFrame([[r_date, r_title, r_clay, r_step, r_note, img_l[0], img_l[1], img_l[2], mood, r_type, r_obj]], columns=df.columns)
                df = pd.concat([df, new_data], ignore_index=True); save_data(df); st.balloons(); st.rerun()

# --- [TAB 4: 🏺 작품 모아보기] ---
with tab_proj:
    st.markdown("<div class='title-text'>작품 모아보기</div>", unsafe_allow_html=True)
    p_f = st.radio("필터", ["전체", "작업중", "완성"], horizontal=True, label_visibility="collapsed")
    if not df.empty:
        u_t = df['작품명'].unique()
        display_t = [t for t in u_t if (p_f=="전체") or (p_f=="작업중" and "완성" not in df[df['작품명']==t]['단계'].values) or (p_f=="완성" and "완성" in df[df['작품명']==t]['단계'].values)]
        cols = st.columns(2)
        for i, t in enumerate(display_t):
            p_l = df[df['작품명'] == t].sort_values(by='날짜')
            rep = p_l[p_l['사진1'] != ""].iloc[-1] if not p_l[p_l['사진1'] != ""].empty else None
            with cols[i%2]:
                src = f"data:image/jpeg;base64,{rep['사진1']}" if rep is not None else ""
                st.markdown(f'<div class="gallery-img-container">{"<img src=\'"+src+"\'>" if rep is not None else "<div style=\'padding:40% 0; text-align:center; color:#ccc;\'>No Photo</div>"}</div>', unsafe_allow_html=True)
                st.markdown(f"**🏺 {t}**")

# --- [TAB 5: ✨ 기분 조각들] ---
with tab_mood:
    st.markdown("<div class='title-text'>기분 조각들</div>", unsafe_allow_html=True)
    mood_mode = st.radio("기준", ["월별", "작품별"], horizontal=True)
    target_df = df.copy()
    if mood_mode == "월별":
        m_val = int(month_str[6:8])
        target_df = target_df[pd.to_datetime(target_df['날짜']).dt.month == m_val]
        st.write(f"🎯 **{m_val}월** 감정 통계")
    else:
        p_val = st.selectbox("작품 선택", sorted(df['작품명'].unique()) if not df.empty else ["없음"])
        target_df = target_df[target_df['작품명'] == p_val]
        st.write(f"🎯 **{p_val}** 전체 기간 감정 통계")
    
    if not target_df.empty:
        counts = target_df['기분'].value_counts()
        for m, emoji in MOOD_DICT.items():
            if m in counts: st.write(f"{emoji} {m}: {counts[m]}회")

# --- [TAB 6: 📊 DANA의 기록 요약] ---
with tab_log:
    st.markdown("<div class='title-text'>DANA의 기록 요약</div>", unsafe_allow_html=True)
    if not df.empty:
        done_p = df[df['단계'] == "완성"]['작품명'].nunique()
        st.markdown(f"<div class='summary-box'>지금까지 총 **{done_p}개**의 작품을 완성했어요! ✨</div>", unsafe_allow_html=True)
        fig = go.Figure(data=[go.Pie(labels=df['기분'].value_counts().index, values=df['기분'].value_counts().values, hole=.6, marker=dict(colors=PASTEL_COLORS))])
        fig.update_layout(height=300, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)

st.markdown("<br><br><br>", unsafe_allow_html=True)
