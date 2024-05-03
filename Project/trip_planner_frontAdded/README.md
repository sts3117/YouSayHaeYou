## Local에서 실행하기 위해 필요한 것

- 1단계: .streamlit 폴더 만들기
- 2단계: secrets.toml 파일 만들어서 API키 넣기
    - 필요한 API 목록. 아래 이름을 그대로 변수로 사용
        - GOOGLE_MAP_API_KEY 
        - OPENAI_API_KEY
        - AMEDEUS_CLIENT_ID
        - AMADEIS_CLIENT_SECRET
        - FIREBASE_WEB_API_KEY
    - FIREBASE json파일 다운로드 후 {}내부 요소 복사 붙여넣기({}은 빼고 복사)
        - json파일 내부는 dictionary로 형태. ditionary 내부의 key, value값만 필요함
        - "key":"value", 형태로 되어 있는데 ','제거하고 key값은 변수로 사용해야 하므로 괄호("")제거
        - 변수명 = "값"  <- 형태로 만들기 위해 ':'을 '='로 변경