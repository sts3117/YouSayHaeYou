# 0421

- claude3를 통해서 travel_chat과 유사한 코드를 새로 생성해봄
    - google map api 관련해서 지속된 오류(KeyError)에 원인 파악이 힘들어서….

- 현재까지 구현 시도한 것은 아래와 같음
    - 호텔, 음식점, 관광지 평점 상위 10개에 대해 받아오기
    - 구글에 해당 장소들에 대한 검색량 받아오기(의도한 것은 아니나 되긴 함)
    - 여행할 도시 이름, 검색할 반경(기존에 streamlit 페이지에 구현된 것과 동일), 여행 일수 입력하도록 하기
    - 검색 데이터, 지도 데이터를 langchain claude에 넘겨 프롬프트 엔지니어링을 통해 계획을 세우도록 함
        
        ```python
        prompt = f"""
You are a travel planner assistant. Based on the following information about hotels, restaurants, and tourist attractions in {city}, create an optimal travel itinerary for a {num_days}-day trip. Consider factors such as ratings, location, and relevance to create a well-rounded and enjoyable experience.

Places:
{str(places)}
"""
        ```
        

- 발생한 문제
    - claude 크레딧 문제
        - 이로 인해 제대로된 계획을 뽑아주는지는 금일 확인 못함
    - (미흡한 코드 지식)claude3 검색량 초과로 금일 더 이상 수정, 개선 불가

- 회고
    - gemini는 글렀는데, gpt랑 claude 결제해서 쓰는게 진짜 맞을까? 
    llama, alpaca도 다시 생각해봐야 할듯
    - streamlit 및 DB 관련해서 이슈가 있다면 그 부분도 다시 생각
    - 랭체인 잘 몰라서 제대로 못 쓰고 있는 것 같음
    - 현재 팀이 진행중인 코드에 이 코드로 개선 가능하면 도입하기
