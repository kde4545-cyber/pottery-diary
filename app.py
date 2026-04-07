# --- [TAB 3: 📜 기록 모아보기] ---
with tab_list:
    st.markdown("<div class='title-text'>기록 모아보기</div>", unsafe_allow_html=True)
    if not df.empty:
        # 날짜 순으로 정렬하여 리스트업
        display_df = df.sort_values(by='날짜', ascending=False)
        
        for idx, row in display_df.iterrows():
            with st.expander(f"🏺 {row['날짜']} | {row['작품명']} ({row['단계']})"):
                st.write(f"**기분:** {MOOD_DICT.get(row['기분'], '')} | **유형:** {row['작업유형']} | **흙:** {row['흙']} | **기물:** {row['기물종류']}")
                st.write(f"**메모:** {row['내용']}")
                
                # 사진 표시
                icols = st.columns(3)
                for i, c in enumerate(['사진1', '사진2', '사진3']):
                    if pd.notna(row[c]) and row[c] != "":
                        icols[i].image(base64.b64decode(row[c]), use_container_width=True)
                
                # 수정 팝오버
                with st.popover("✏️ 정보 수정"):
                    with st.form(f"full_edit_{idx}"):
                        e_mood = st.radio("기분", list(MOOD_DICT.keys()), 
                                         index=list(MOOD_DICT.keys()).index(row['기분']) if row['기분'] in MOOD_DICT else 0, 
                                         horizontal=True, format_func=lambda x: MOOD_DICT[x])
                        e_date = st.date_input("날짜", row['날짜'])
                        e_title = st.text_input("작품명", row['작품명'])
                        ec1, ec2 = st.columns(2)
                        e_type = ec1.selectbox("작업 유형", TYPE_LIST, index=TYPE_LIST.index(row['작업유형']) if row['작업유형'] in TYPE_LIST else 0)
                        e_clay = ec2.selectbox("흙 종류", CLAY_LIST, index=CLAY_LIST.index(row['흙']) if row['흙'] in CLAY_LIST else 0)
                        e_obj = st.selectbox("기물 종류", OBJ_LIST, index=OBJ_LIST.index(row['기물종류']) if row['기물종류'] in OBJ_LIST else 0)
                        e_step = st.select_slider("단계", options=STEP_LIST, value=row['단계'])
                        e_note = st.text_area("메모", row['내용'])
                        e_imgs = st.file_uploader("새 사진으로 교체 (선택 시 기존 사진 삭제됨)", type=["jpg", "png", "jpeg"], accept_multiple_files=True, key=f"f_edit_img_{idx}")
                        
                        if st.form_submit_button("수정 내용 저장"):
                            # 1. 일반 텍스트 정보 업데이트
                            df.at[idx, '기분'] = e_mood
                            df.at[idx, '날짜'] = e_date
                            df.at[idx, '작품명'] = e_title
                            df.at[idx, '작업유형'] = e_type
                            df.at[idx, '흙'] = e_clay
                            df.at[idx, '기물종류'] = e_obj
                            df.at[idx, '단계'] = e_step
                            df.at[idx, '내용'] = e_note
                            
                            # 2. 사진 업데이트 (새로 업로드한 파일이 있을 때만 교체)
                            if e_imgs and len(e_imgs) > 0:
                                img_list = [process_img(e_imgs[i]) if i < len(e_imgs) else "" for i in range(3)]
                                df.at[idx, '사진1'] = img_list[0]
                                df.at[idx, '사진2'] = img_list[1]
                                df.at[idx, '사진3'] = img_list[2]
                            
                            save_data(df)
                            st.success("수정이 완료되었습니다!")
                            st.rerun()
                
                # 삭제 버튼
                if st.button("🗑️ 이 기록 삭제", key=f"dl_{idx}"):
                    df = df.drop(index=idx)
                    save_data(df)
                    st.rerun()
    else:
        st.info("기록된 내용이 없습니다.")
