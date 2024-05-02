import streamlit as st
from core_files import auth_core

def main():
    user_tab1, user_tab2 = st.tabs(["비밀번호 재설정", "개인정보 변경"])
    
    with user_tab1:
        col1, col2 = st.columns(2)
        with col1:
            auth_core.update_password_form()
    with user_tab2:
        col1, col2 = st.columns(2)
        with col1:
            auth_core.update_display_name_form()
    
    return None
    