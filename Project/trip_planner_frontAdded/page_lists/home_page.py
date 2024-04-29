import streamlit as st
from streamlit_extras.stylable_container import stylable_container
from page_lists import chat_page, db_page, route_page, search_page, auth_page, home_page
from streamlit.components.v1 import html
from streamlit_extras.stylable_container import stylable_container

def home():
    st.markdown("---")
    
    st.subheader("원하는 페이지를 클릭해주세요")
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        with stylable_container(
            key="container_with_border",
            css_styles="""
                {
                    border: 1px solid rgba(49, 51, 63, 0.2);
                    border-radius: 1rem;
                    padding: 12px;
                    justify-content: center;
                    align-items: center;
                    background-color : #E8E8E8;
                    width: 80%;
                }
                """,
            ):
            st.write("호텔, 음식점, 여행지를 하나하나 찾고 싶다면?!")
            move2_search = st.button("검색 페이지로 이동")
            

        st.markdown("---")
        
        with stylable_container(
            key="container_with_border",
            css_styles="""
                {
                    border: 1px solid rgba(49, 51, 63, 0.2);
                    border-radius: 1rem;
                    padding: 12px;
                    justify-content: center;
                    align-items: center;
                    background-color : #E8E8E8;
                    width: 80%;
                    text-align: center;
                }
                """,
            ):
            st.write("어떻게 가야하는지 길을 찾고 싶다면?!")
            move2_route =  st.button('길찾기 페이지로 이동')
         
    with col2:
        with stylable_container(
            key="container_with_border",
            css_styles="""
                {
                    border: 1px solid rgba(49, 51, 63, 0.2);
                    border-radius: 1rem;
                    padding: 12px;
                    justify-content: center;
                    align-items: center;
                    background-color : #E8E8E8;
                    width: 80%;
                    text-align: center;
                }
                """,
            ):
            st.write("챗봇에게 모든 계획을 세우게 하고 싶다면?!")
            move2_chat =  st.button('챗봇 페이지로 이동')
        st.markdown('---')
        
        with stylable_container(
            key="container_with_border",
            css_styles="""
                {
                    border: 1px solid rgba(49, 51, 63, 0.2);
                    border-radius: 1rem;
                    padding: 12px;
                    justify-content: center;
                    align-items: center;
                    background-color : #E8E8E8;
                    width: 80%;
                    text-align: center;
                }
                """,
            ):
            st.write("기존의 데이터를 사용해서 더 빠르게 계획을 세우고 싶다면?!")
            move2_db =  st.button('DB 페이지로 이동')