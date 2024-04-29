import math
import time
import json
from contextlib import suppress
from datetime import datetime, timedelta
from functools import partial
from typing import Dict, Final, Optional, Sequence, Union

import extra_streamlit_components as stx
import firebase_admin
import jwt
import requests
import streamlit as st
from email_validator import EmailNotValidError, validate_email
from firebase_admin import auth
from collections import OrderedDict

TITLE: Final = "Personal Trip Planner"

POST_REQUEST_URL_BASE: Final = "https://identitytoolkit.googleapis.com/v1/accounts:"
post_request = partial(
    requests.post,
    headers={"content-type": "application/json; charset=UTF-8"},
    timeout=10,
)

def authenticate_user(
        email: str, password: str, require_email_verification: bool = True
) -> Optional[Dict[str, Union[str, bool, int]]]:
    """
    Authenticates a user with the given email and password using the Firebase Authentication
    REST API.
    Parameters:
        email (str): The email address of the user to authenticate.
        password (str): The password of the user to authenticate.
        require_email_verification (bool): Specify whether a user has to be e-mail verified to
        be authenticated
    Returns:
        dict or None: A dictionary containing the authenticated user's ID token, refresh token,
        and other information, if authentication was successful. Otherwise, None.
    Raises:
        requests.exceptions.RequestException: If there was an error while authenticating the user.
    """

    url = f"{POST_REQUEST_URL_BASE}signInWithPassword?key={st.secrets['FIREBASE_WEB_API_KEY']}"
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True,
        "emailVerified": require_email_verification,
    }
    response = post_request(url, json=payload)
    if response.status_code != 200:
        st.error(f"인증 실패: {parse_error_message(response)}")
        return None
    response = response.json()
    if require_email_verification and "idToken" not in response:
        st.error("유효하지 않은 이메일 또는 비밀번호입니다.")
        return None
    return response


def forgot_password_form(preauthorized: Union[str, Sequence[str], None]) -> None:
    """Creates a Streamlit widget to reset a user's password. Authentication uses
    the Firebase Authentication REST API.
    Parameters:
        preauthorized (Union[str, Sequence[str], None]): An optional domain or a list of
        domains which are authorized to register.
    """

    with st.form("비밀번호를 잊으셨습니까?"):
        email = st.text_input("E-mail", key="forgot_password")
        if not st.form_submit_button("비밀번호 재설정"):
            return None
    if "@" not in email and isinstance(preauthorized, str):
        email = f"{email}@{preauthorized}"

    url = f"{POST_REQUEST_URL_BASE}sendOobCode?key={st.secrets['FIREBASE_WEB_API_KEY']}"
    payload = {"requestType": "PASSWORD_RESET", "email": email}
    response = post_request(url, json=payload)
    if response.status_code == 200:
        return st.success(f"비밀번호 초기화 링크가 {email}로 전송되었습니다.")
    return st.error(f"비밀번호 초기화 이메일 전송 오류: {parse_error_message(response)}")


def register_user_form(preauthorized: Union[str, Sequence[str], None]) -> None:
    """Creates a Streamlit widget for user registration.
    Password strength is validated using entropy bits (the power of the password alphabet).
    Upon registration, a validation link is sent to the user's email address.
    Parameters:
        preauthorized (Union[str, Sequence[str], None]): An optional domain or a list of
        domains which are authorized to register.
    """

    with st.form(key="register_form"):
        email, name, password, confirm_password, register_button = (
            st.text_input("E-mail"),
            st.text_input("이름"),
            st.text_input("비밀번호", type="password"),
            st.text_input("비밀번호 확인", type="password"),
            st.form_submit_button(label="확인"),
        )
    if not register_button:
        return None
    # Below are some checks to ensure proper and secure registration
    if password != confirm_password:
        return st.error("암호가 틀렸습니다.")
    if not name:
        return st.error("이름을 입력해주세요.")
    if "@" not in email and isinstance(preauthorized, str):
        email = f"{email}@{preauthorized}"
    if preauthorized and not email.endswith(preauthorized):
        return st.error("지원하지 않는 이메일입니다.(현재 구글, 네이버 지원)")
    try:
        validate_email(email, check_deliverability=True)
    except EmailNotValidError as e:
        return st.error(e)

    # Need a password that has minimum 66 entropy bits (the power of its alphabet)
    # I multiply this number by 1.5 to display password strength with st.progress
    # For an explanation, read this -
    # https://en.wikipedia.org/wiki/Password_strength#Entropy_as_a_measure_of_password_strength
    alphabet_chars = len(set(password))
    strength = int(len(password) * math.log2(alphabet_chars) * 1.5)
    if strength < 30:
        st.progress(strength)
        return st.warning(
            "비밀번호가 너무 약합니다. 더 강하게 설정해주세요.", icon="⚠️"
        )
    auth.create_user(
        email=email, password=password, display_name=name, email_verified=False
    )
    # Having registered the user, send them a verification e-mail
    token = authenticate_user(email, password, require_email_verification=False)[
        "idToken"
    ]
    url = f"{POST_REQUEST_URL_BASE}sendOobCode?key={st.secrets['FIREBASE_WEB_API_KEY']}"
    payload = {"requestType": "VERIFY_EMAIL", "idToken": token}
    response = post_request(url, json=payload)
    if response.status_code != 200:
        return st.error(f"확인 메일 전송에 실패했습니다: {parse_error_message(response)}")
    st.success(
        "회원가입이 완료되었습니다. 회원가입 절차를 완료하기 위해서는, "
        "이메일의 확인 링크를 클릭해주세요. 메일함에 없을 경우 스팸메일함에 들어가 있을 수도 있어요."
    )
    return st.balloons()


def update_password_form() -> None:
    """Creates a Streamlit widget to update a user's password."""

    # Get the email and password from the user
    new_password = st.text_input("비밀번호 재설정", key="new_password", type="password")
    # Attempt to log the user in
    if not st.button("재설정"):
        return None
    user = auth.get_user_by_email(st.session_state["username"])
    auth.update_user(user.uid, password=new_password)
    return st.success("비밀번호가 성공적으로 변경되었습니다.")


def parse_error_message(response: requests.Response) -> str:
    """
    Parses an error message from a requests.Response object and makes it look better.
    Parameters:
        response (requests.Response): The response object to parse.
    Returns:
        str: Prettified error message.
    Raises:
        KeyError: If the 'error' key is not present in the response JSON.
    """
    return (
        response.json()["error"]["message"]
        .casefold()
        .replace("_", " ")
        .replace("email", "e-mail")
    )


def main():
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
    pretty_title(TITLE)

    # st.session_state["authentication_status"] = False

    if not_logged_in(preauthorized=("gmail.com", "naver.com")):
        return None

    with st.sidebar:
        login_panel()


def pretty_title(title: str) -> None:
    """Make a centered title, and give it a red line. Adapted from
    'streamlit_extras.colored_headers' package.
    Parameters:
    -----------
    title : str
        The title of your page.
    """
    st.markdown(
        f"<h2 style='text-align: center'>{title}</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        (
            '<hr style="background-color: #ff4b4b; margin-top: 0;'
            ' margin-bottom: 0; height: 3px; border: none; border-radius: 3px;">'
        ),
        unsafe_allow_html=True,
    )


def login_panel() -> None:
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

    if st.button("로그아웃"):
        # cookie_manager.delete(cookie_name)
        st.session_state["name"] = None
        st.session_state["username"] = None
        st.session_state["authentication_status"] = None
        st.rerun()
    st.write(f"환영합니다, {st.session_state['name']}님!")
    # user_tab1, user_tab2 = st.tabs(["비밀번호 재설정", "개인정보 변경"])
    # with user_tab1:
    #     update_password_form()
    # with user_tab2:
    #     update_display_name_form()
    return None


def update_display_name_form() -> None:
    """Creates a Streamlit widget to update a user's display name.
    Parameters
    ----------
     - cookie_manager : stx.CookieManager
        A JWT cookie manager instance for Streamlit
    - cookie_name : str
        The name of the reauthentication cookie.
    - cookie_expiry_days: (optional) str
        An integer representing the number of days until the cookie expires
    """

    # Get the email and password from the user
    new_name = st.text_input("이름 변경", key="new name")
    # Attempt to log the user in
    if not st.button("확인"):
        return None
    user = auth.get_user_by_email(st.session_state["username"])
    auth.update_user(user.uid, display_name=new_name)
    st.session_state["name"] = new_name
    return st.success("이름이 성공적으로 변경되었습니다.")


def not_logged_in(preauthorized: Union[str, Sequence[str], None] = None) -> bool:
    """Creates a tab panel for unauthenticated, preventing the user control sidebar and
    the rest of the script from appearing until the user logs in.
    Parameters
    ----------
     - cookie_manager : stx.CookieManager
        A JWT cookie manager instance for Streamlit
    - cookie_name : str
        The name of the reauthentication cookie.
    - cookie_expiry_days: (optional) str
        An integer representing the number of days until the cookie expires
    Returns
    -------
    Authentication status boolean.
    Notes
    -----
    If the user is already authenticated, the login panel function is called to create a side
    panel for logged-in users. If the function call does not update the authentication status
    because the username/password does not exist in the Firebase database, the rest of the script
    does not get executed until the user logs in.
    """

    early_return = True
    # In case of a first run, pre-populate missing session state arguments
    for key in {"name", "authentication_status", "username", "logout"}.difference(
            set(st.session_state)
    ):
        st.session_state[key] = None

    login_tabs = st.empty()
    with login_tabs:
        login_tab1, login_tab2, login_tab3 = st.tabs(
            ["로그인", "회원 가입", "비밀번호 찾기"]
        )
        with login_tab1:
            login_form(preauthorized)
        with login_tab2:
            register_user_form(preauthorized)
        with login_tab3:
            forgot_password_form(preauthorized)

    auth_status = st.session_state["authentication_status"]
    if auth_status is False:
        st.error("이름 또는 비밀번호가 틀렸습니다.")
        return early_return
    if auth_status is None:
        return early_return
    login_tabs.empty()
    # A workaround for a bug in Streamlit -
    # https://playground.streamlit.app/?q=empty-doesnt-work
    # TLDR: element.empty() doesn't actually seem to work with a multi-element container
    # unless you add a sleep after it.
    time.sleep(0.01)
    return not early_return


def login_form(preauthorized: Union[str, Sequence[str], None]) -> None:
    """Creates a login widget using Firebase REST API and a cookie manager.
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
    If the user has already been authenticated, this function does nothing. Otherwise, it displays
    a login form which prompts the user to enter their email and password. If the login credentials
    are valid and the user's email address has been verified, the user is authenticated and a
    reauthentication cookie is created with the specified expiration date.
    """

    if st.session_state["authentication_status"]:
        return None
    with st.form("로그인"):
        email = st.text_input("E-mail")
        if "@" not in email and isinstance(preauthorized, str):
            email = f"{email}@{preauthorized}"
        st.session_state["username"] = email
        password = st.text_input("비밀번호", type="password")
        if not st.form_submit_button("로그인"):
            return None

    # Authenticate the user with Firebase REST API
    login_response = authenticate_user(email, password)
    if not login_response:
        return None
    try:
        decoded_token = auth.verify_id_token(login_response["idToken"])
        user = auth.get_user(decoded_token["uid"])
        if not user.email_verified:
            return st.error("메일함을 확인해주세요.")
        # At last, authenticate the user
        st.session_state["name"] = user.display_name
        st.session_state["username"] = user.email
        st.session_state["authentication_status"] = True
    except Exception as e:
        st.error(e)
    return None
