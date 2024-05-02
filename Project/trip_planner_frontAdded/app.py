import streamlit as st

st.set_page_config(page_title="Personal Trip Planner", layout="wide", page_icon="🛫", menu_items={
        'About': "이 app은 여러분들의 여행을 도와줄 거에요!"
    })
from streamlit_option_menu import option_menu
import firebase_admin
import json
from collections import OrderedDict
import hydralit_components as hc

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
from page_lists import chat_page, db_page, route_page, search_page, auth_page, home_page

auth_core.main()


def main():
    if not st.session_state['authentication_status']:
        return

    # specify the primary menu definition
    menu_data = [
        {'icon': "🛠", 'label': "계정설정"},
        {'icon': "🔎", 'label': "검색"},
        {'icon': "📋", 'label': "챗봇"},  # no tooltip message
        {'icon': "📝", 'label': "DB"},
        {'icon': "🗺️", 'label': "길찾기"},
    ]

    over_theme = {'txc_inactive': '#FFFFFF', 'menu_background': '#00B622'}
    page = hc.nav_bar(
        menu_definition=menu_data,
        override_theme=over_theme,
        home_name='홈',
        hide_streamlit_markers=True,  # will show the st hamburger as well as the navbar now!
        sticky_nav=True,  # at the top or not
        sticky_mode='pinned',  # jumpy or not-jumpy, but sticky or pinned
    )

    if page == '홈':
        home_page.home()
    if page == '계정설정':
        st.subheader("비밀번호 재설정/개인정보변경")
        auth_page.main()
    if page == "검색":
        st.subheader("사이드바에 정보를 채워 검색을 해보세요")
        search_page.createPage()

    if page == "챗봇":
        st.subheader("가고싶은 곳에 대해 질문해보세요")
        chat_page.createPage()

    if page == "DB":
        st.subheader("가고 싶은 지역을 선택해서 질문하면 내부 DB로 검색해드려요")
        db_page.createPage()
    if page == "길찾기":
        st.subheader("가고 싶은 곳까지의 경로를 찾아보세요")
        route_page.route()

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
