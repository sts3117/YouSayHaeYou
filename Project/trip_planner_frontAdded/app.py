import streamlit as st
st.set_page_config(layout="wide")
from streamlit_option_menu import option_menu
from PIL import Image
import time
import firebase_admin
from firebase_admin import auth
import json
from collections import OrderedDict
from streamlit_navigation_bar import st_navbar


if not firebase_admin._apps:
    cred_json = OrderedDict()
    cred_json["type"] = st.secrets["type"]  # 이렇게 값을 숨겨주는 게 좋다.
    cred_json["project_id"] = st.secrets["project_id"]
    cred_json["private_key_id"] = st.secrets["private_key_id"]
    cred_json["private_key"] = st.secrets["private_key"].replace('\\n', '\n')
    cred_json["client_email"] = st.secrets["client_email"]
    cred_json["client_id"] = st.secrets["client_id"]
    cred_json["auth_uri"] = st.secrets["auth_uri"]
    cred_json["token_uri"] = st.secrets["token_uri"]
    cred_json["auth_provider_x509_cert_url"] = st.secrets["auth_provider_x509_cert_url"]
    cred_json["client_x509_cert_url"] = st.secrets["client_x509_cert_url"]
    cred_json["universe_domain"] = st.secrets["universe_domain"]

    js = json.dumps(cred_json)  
    js_dict = json.loads(js)
    cred = firebase_admin.credentials.Certificate(js_dict)
    firebase_admin.initialize_app(cred)
from core_files import auth_core
from core_files import data_core
from page_lists import chat_page, db_page, route_page, search_page, auth_page, home_page

# with st.sidebar:
col1, col2, col3 = st.columns([3,4,3])
with col2:
    auth_core.main()

def main():
    if not st.session_state['authentication_status']:
        return
    
    # #sidebar menu
    # with st.sidebar:
    #     # st.sidebar.title(f"Personal Trip Planner")
    #     # st.write(f'Welcome *{st.session_state["name"]}*')
    #     selected = option_menu(
    #         key='option_menu_select',
    #         menu_title = None,
    #         options = ["홈", "계정", "검색", "챗봇", "데이터베이스", "길찾기"],
    #         icons = ['house', 'person-circle','search', 'robot', 'book', 'map'],
    #         default_index=0,
    #         styles={
    #         "container": {"padding": "0!important", "background-color": "#fafafa"},
    #         "icon": {"color": "orange", "font-size": "15px"}, 
    #         "nav-link": {"font-size": "15px", "text-align": "left", "margin":"0px", "--hover-color": "#FFC7BA"},
    #         "nav-link-selected": {"background-color": "blue"},
    #     })
    
    styles = {
    "nav": {
        "background-color": "royalblue",
        "justify-content": "center",
    },
    
    "span": {
        "color": "white",
        "padding": "14px",
    },
    "active": {
        "color": "var(--text-color)",
        "background-color": "white",
        "font-weight": "bold",
        "padding": "14px",
    },
    "hover": {
        "background-color": "rgba(255, 255, 255, 0.35)",
    },
    }
    
       
    page = st_navbar(["홈", "계정", "검색", "챗봇", "DB", "길찾기"], styles=styles)
    
    if page=='홈' :
        home_page.home()
    if  page=='계정':
        st.subheader("비밀번호 재설정/개인정보변경")
        auth_page.main()
    if page=="검색":
        st.subheader("사이드바에 정보를 채워 검색을 해보세요")
        search_page.createPage()
        
    if page=="챗봇":
        st.subheader("가고싶은 곳에 대해 질문해보세요")
        chat_page.createPage()
        
    if page=="DB":
        st.subheader("가고 싶은 지역을 선택해서 질문하면 내부 DB로 검색해드려요")
        db_page.createPage()
    if page=="길찾기" :
        st.subheader("가고 싶은 곳까지의 경로를 찾아보세요")
        route_page.route()
        
    
    
    # selected_top = option_menu(
    #     key='option_menu_select_top',
    #     menu_title = None,
    #     options = ["홈", "계정", "검색", "챗봇", "DB", "길찾기"],
    #     icons = ['house', 'person-circle','search', 'robot', 'book', 'map'],
    #     default_index=0,
    #     orientation="horizontal",
    #     styles={
    #     "container": {"padding": "0!important", "background-color": "#EBF1FF"},
    #     "icon": {"color": "#EA8210", "font-size": "15px", "text-align":"center"}, 
    #     "nav-link": {"font-size": "20px", "text-align": "center", "margin":"0px", "--hover-color": "#FFC7BA"},
    #     "nav-link-selected": {"background-color": "#10444C"},
    # })
    
    # loading page
    # progress_text = "잠시만 기다려주세요"
    # progress = st.progress(0, text=progress_text)
        # for i in range(50):
        #     time.sleep(0.1)
        #     progress.progress(i+1, text=progress_text)
        # time.sleep(0.5)
        # progress.empty()
    # if selected_top=='홈' :
    #     home_page.home()
    # if  selected_top=='계정':
    #     st.subheader("비밀번호 재설정/개인정보변경")
    #     auth_page.main()
    # if selected_top=="검색":
    #     st.subheader("사이드바에 정보를 채워 검색을 해보세요")
    #     search_page.createPage()
        
    # if selected_top=="챗봇":
    #     st.subheader("가고싶은 곳에 대해 질문해보세요")
    #     chat_page.createPage()
        
    # if selected_top=="DB":
    #     st.subheader("가고 싶은 지역을 선택해서 질문하면 내부 DB로 검색해드려요")
    #     db_page.createPage()
    # if selected_top=="길찾기" :
    #     st.subheader("가고 싶은 곳까지의 경로를 찾아보세요")
    #     route_page.route()
        
    js = '''
        <script>
            var body = window.parent.document.querySelector(".main");
            console.log(body);
            body.scrollTop = 0;
            
        </script>
        '''
        
    st.markdown('---')
    
    if st.button(f"▲ TOP"):
        st.components.v1.html(js)

    st.sidebar.markdown('---')
    st.sidebar.markdown(''' 
        ## Created by: 
        Team.알리미\n
        [한컴아카데미](https://hancomacademy.com/) with nvidia\n
        special thanks to Ahmad Luay Adnani
        ''')


main()