import streamlit as st
from core_files import auth_core

def main():
    """Creates a side panel for logged-in users, preventing the login menu from
    appearing.
    Parameters
    ----------
     - cookie_manager : stx.CookieManager
        A JWT cookie manager instance for Streamlit
    - cookie_name : str
        The name of the reauthentication cookie.
    - cookie_expiry_days: (optional) str
        An integer representing the number of days until the cookie expires
    Notes
    -----
    If the user is logged in, this function displays two tabs for resetting the user's password
    and updating their display name.
    If the user clicks the "Logout" button, the reauthentication cookie and user-related information
    from the session state is deleted, and the user is logged out.
    """

    user_tab1, user_tab2 = st.tabs(["비밀번호 재설정", "개인정보 변경"])
    with user_tab1:
        auth_core.update_password_form()
    with user_tab2:
        auth_core.update_display_name_form()
    return None
    