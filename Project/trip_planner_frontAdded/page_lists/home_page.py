import streamlit as st
from streamlit_extras.stylable_container import stylable_container
from page_lists import chat_page, db_page, route_page, search_page, auth_page, home_page
from streamlit.components.v1 import html
from streamlit_extras.stylable_container import stylable_container

def home():
    st.markdown("---")
    
    st.subheader("- About Us -")
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("여행 계획을 쉽게 세우고 싶은 ")
        st.subheader("당신을 위한 여행 계획 서비스")
        st.subheader("'Ali-me(알리미)입니다'")
        st.markdown('---')

    with col2:
        st.image("imgs\character.png", caption="알리미 서비스 마스코드 'Al-im(알림)'")
        