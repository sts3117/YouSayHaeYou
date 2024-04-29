import streamlit as st
from streamlit_option_menu import option_menu

from PIL import Image

import firebase_admin
from firebase_admin import auth
import json
from collections import OrderedDict
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
from page_lists import chat_page, db_page, route_page, search_page, auth_page

# st.write(os.getcwd())
with st.sidebar:
    auth_core.main()


def main():
    if not st.session_state['authentication_status']:
        return
    
    #sidebar menu
    with st.sidebar:
        # st.sidebar.title(f"Personal Trip Planner")
        # st.write(f'Welcome *{st.session_state["name"]}*')
        selected = option_menu(
            menu_title = None,
            options = ["계정", "검색", "챗봇", "데이터베이스", "길찾기"],
            icons = ['person-circle','search', 'robot', 'book', 'map'],
            default_index=0,
            styles={
            "container": {"padding": "0!important", "background-color": "#fafafa"},
            "icon": {"color": "orange", "font-size": "15px"}, 
            "nav-link": {"font-size": "15px", "text-align": "left", "margin":"0px", "--hover-color": "#FFC7BA"},
            "nav-link-selected": {"background-color": "blue"},
        })
    if selected=='계정':
        st.title(f'{selected}')
        auth_page.main()
    if selected=="검색":
        st.title(f"{selected}")
        search_page.createPage()
    if selected=="챗봇":
        st.title(f"{selected}")
        chat_page.createPage()
    if selected=="데이터베이스":
        st.title(f"{selected}")
        db_page.createPage()
    if selected=="길찾기":
        st.title(f"{selected}🗺️")
        route_page.route()

if __name__ == '__main__':
    
    main()