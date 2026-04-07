import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
from io import BytesIO
from PIL import Image

st.set_page_config(page_title="나의 도자기 일기", layout="centered")

st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    html, body, [class*="css"], .stMarkdown, p, span, label, input, button, select {
        font-family: 'Pretendard', sans-serif !important;
        letter-spacing: -0.03em !important;
    }
    .stButton>button {
        width: 100%; border-radius: 12px; height: 3.5em;
        background-color: #8d6e63; color: white; font-weight: bold; border: none;
    }
    .log-card {
        background-color: #ffffff; padding: 18px; border-radius: 15px;
        border: 1px solid #f0f0f0; margin-bottom: 20px;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.03);
    }
    </style>
    """, unsafe_allow_html=True)

DATA_FILE = "pottery_diary_data.csv"

def img_to_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="JPEG", quality=70)
    return base64.b64encode(buffered.getvalue()).decode()

def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=["날짜", "작품명", "흙", "단계", "내용", "사진"])

st.title("🏺 나의 도자기 일기")

with st.expander("📝 오늘 작업 기록하기", expanded=True):
    date = st.date_input("날짜", datetime.now())
    title = st.text_input("작품명", placeholder="어떤 작품인가요?")
    clay = st.selectbox("흙 종류", ["백자토", "산백토", "조형토", "청자토", "옹기토", "기타"])
    process = st.select_slider("단계", options=["성형", "건조", "초벌", "시유", "완성"])
    uploaded_file = st.file_uploader("사진 올리기", type=["jpg", "jpeg", "png"])
    content = st.text_area("메모", placeholder="주의사항이나 배운 점")
    
    if st.button("기록 저장하기"):
        if title:
            img_base64 = ""
            if uploaded_file:
                img = Image.open(uploaded_file)
                img.thumbnail((800, 800))
                img_base64 = img_to_base64(img)
            
            new_entry = pd.DataFrame([[date, title, clay, process, content, img_base64]], 
                                     columns=["날짜", "작품명", "흙", "단계", "내용", "사진"])
            df = load_data()
            df = pd.concat([df, new_entry], ignore_index=True)
            df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
            st.success("저장 완료!")
            st.rerun()
        else:
            st.error("작품명을 적어주세요!")

st.divider()
df = load_data()
if not df.empty:
    for _, row in df.iloc[::-1].iterrows():
        with st.container():
            st.markdown(f"""
            <div class="log-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="font-size: 0.85em; color: #888;">{row['날짜']}</span>
                    <span style="background: #efebe9; color: #8d6e63; padding: 2px 8px; border-radius: 20px; font-size: 0.8em; font-weight: bold;">{row['단계']}</span>
                </div>
                <div style="font-size: 1.15em; font-weight: 700;">{row['작품명']}</div>
                <div style="font-size: 0.9em; color: #555; margin-top: 2px;">{row['흙']}</div>
                <div style="margin-top: 10px; font-size: 0.95em; line-height: 1.5; white-space: pre-wrap;">{row['내용']}</div>
            </div>
            """, unsafe_allow_html=True)
            if pd.notna(row['사진']) and row['사진'] != "":
                st.image(base64.b64decode(row['사진']))
else:
    st.info("아직 기록이 없어요.")