import os, sys
import streamlit as st
import folium
from streamlit_folium import folium_static
from core_files import route_core

def route():
    st.markdown('---')
    col1, col2 = st.columns(2)
    with col1:
        start = st.text_input('어디에서 출발하시나요?:')
        dest = st.text_input('어디로 가시나요?:')
        sel = st.selectbox('어떻게 가시나요?', ('대중교통으로', '걸어서', '차로'))
        
    m1 = ''
    info_style=''
            
    if st.button('길 찾기'):
        if sel == '대중교통으로':
            st.markdown('---')
            st.subheader(f"'{start}'에서 '{dest}'까지 {sel} 가는 경로입니다")
            ddf, route1, distance, duration, start_point = route_core.s_to_d(start, dest, sel)
            m1 = route_core.draw_route_on_folium(ddf, start_point)
            
        else:
            ddf, route1, distance, duration = route_core.s_to_d(start, dest, sel)
            st.subheader(f"{start}에서 {dest}까지 {sel} 가는 경로입니다")
            m1 = route1.plot_route()
            
            # st.text(f"거리는 {distance}km입니다.")
            # st.text(f"예상 소요 시간은 {duration}에요!")

        col3, col4  = st.columns([5.5, 4.5])
        with col3:
            folium_static(m1)
        with col4:
            info_style = f"""
            <div style='text-align: left;'>
                <div style='background-color:#f0f0f0; padding:10px; border-radius:10px;'>
                    <p style='font-size:20px; margin:0; '><b>📌거리는 {distance}km입니다.</b></p>
                    <br>
                    <p style='font-size:20px; margin:0;'><b>📌 예상 소요 시간은 {duration}에요!</b></p>
                    <br>
                </div>
            </div>
            """
            st.markdown(info_style, unsafe_allow_html=True)