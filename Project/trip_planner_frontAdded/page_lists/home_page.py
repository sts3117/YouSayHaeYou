import streamlit as st
from streamlit.components.v1 import html

def home():
    
    st.subheader("- WELCOME TO PERSONAL TRIP PLANNER -")
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("여행 계획을 쉽게 세우고 싶은 ")
        st.subheader("당신을 위한 여행 계획 서비스")
        st.markdown('<p style="font-family:sans-serif; color:Green; font-size: 40px; font-weight: 500">Ali-me(알리미)</p>', unsafe_allow_html=True)
        st.markdown('---')

        st.markdown('<p style="font-family:Courier; color:Green; font-size: 20px;">여행 계획을 세우기 위해 머리를 부여잡던 시절은 이제 그만!</p>', unsafe_allow_html=True)

        st.write("여행은 많은 사람들에게 기쁨과 휴식을 주는 존재입니다. 여행이 주는 즐거움은 크지만 여행을 가기 전에 계획을 세우는 것은 우리를 피곤하게 만드는 경우가 많지요.")
        st.write("여행계획에서 가장 중요한 부분은 어떤 항공편으로 어디를 가서 무엇을 먹을지 결정하는 것인데 이 결정은 쉽지 않은 일입니다. 예산, 이동동선, 평점 등 고려해야 하는 요소들이 너무 많기 때문이지요. 그래서 여러 조건들을 비교해가며 계획을 세우다보면 몇시간은 금방 지나가게 됩니다.")
        st.write("그래서 저희는 생각했습니다. 복잡한 여행 계획을 조건만 넣어주면 알아서 찾아주는 여행 플래너가 있으면 좋겠다. 그래서 여행 계획과 그 정보들을 알아서 찾아주는 개인화된 AI 여행 플래너를 만들고자 계획했습니다.")
        st.write("수많은 고민과 테스트 끝에 마침내 개인화된 여행 플래너 '알리미' 서비스가 탄생했습니다. 원하는 지역, 예산과 같은 조건을 입력하면 자동으로 항공/호텔/여행지 정보를 찾아옵니다. 이 서비스를 사용하면 더 이상 항공편/호텔/여행지를 찾으며 계획을 세우느라 머리를 부여잡을 필요가 없습니다. ")
        st.write("나만을 위한 여행플래너 알리미로 더 즐거운 여행을 계획해보세요")

    with col2:
        st.image("imgs\character.png", width=500,caption="알리미 서비스 마스코드 'Al-im(알림)'")
        