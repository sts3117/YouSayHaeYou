# memo

[Home](https://docs.crewai.com/)

## 24.04.17

### pdf 대신 csv 넣는 방법

```
from crewai_tools import CSVSearchTool

csv_tool = CSVSearchTool(csv='conv.csv')

```

- [Q] csv나 pdf 데이터를 통해 추천하는 무언가가 없는 느낌? 순수하게 search api를 통해 플래닝을 하는 것 같음

---

## 24.04.18

> 도큐먼트를 조금 더 자세히 봐서 개선점을 찾아야할 것 같음
> 
- 메모리 시스템이 있음
    - Short-Term Memory
        - 최근 상호 작용 및 결과를 임시로 저장하여 상담원이 현재 상황과 관련된 정보를 기억하고 활용할 수 있도록 합니다.
    - Long-Term Memory
        - 과거 실행에서 얻은 귀중한 통찰력과 학습 내용을 보존하여 상담원이 시간이 지남에 따라 지식을 구축하고 개선할 수 있도록 합니다
    - Entity Memory
        - 작업 중에 접하는 개체(사람, 장소, 개념)에 대한 정보를 캡처하고 구성하여 더 깊은 이해와 관계 매핑을 촉진합니다.
    - Contextual Memory
        - 상호작용의 맥락을 유지하여 일련의 작업이나 대화에 대한 상담원 응답의 일관성과 관련성을 지원합니다.
    

> 코드 예시
> 

```python
from crewai import Crew, Agent, Task, Process

# Assemble your crew with memory capabilities
my_crew = Crew(
    agents=[...],
    tasks=[...],
    process=Process.sequential,
    memory=True,
    verbose=True
```

- 계층적, 순차적 프로세스 구조에 대해서도 고민해봐야 함
---

# 0419
## [오후]

[https://imsi-0419.streamlit.app](https://imsi-0419.streamlit.app)

### 웹 內 발견된 문제점 및 개선사항

- 구글맵 API(~~틈만 나면 오류남~~😡)
    - 대중교통 길찾기 외에는 한글 지원이 안됨
    - 또한 어떤 길찾기든, 지도에 경로만 찍어주지 구체적인 대중교통 종류라던지, 시간에 대한 언급이 없음
- 스크롤 맨 위로 올리는 기능
- 지역을 바꾸거나 그랬을 때, 이전 질문 내용이 그대로 유지됨, 즉 질문했던 내용을 초기화한다던지, 새로운 탭을 제공한다던지 하는게 미존재
- Gemini → 글렀음.
- Claude → 실험 중
- 

### CODE

```python
llm = ChatAnthropic(temperature=0.7, model_name='claude-3-sonnet-20240229') # sonnet , opu

```
---
# 0422
## 오전

확실하지는 않으나, 개인적인 의견으로는

- places 오류는 ip 관련해서 네트워크 문제가 아닌 것 같음, 상태코드 200 잘 들어옴
    - 오히려, 파싱이나 요청 코드가 문제일까 아닌가 의심스러움
    - 근데 뭘 건드려야 할 지 모르겠음
- claude는 위 문제만 해결되면 사용도 가능할 것 같음

- 검색 결과가 없거나 키가 없는 경우 예외 처리  

  ```python
    # chatbot_core.py
    
    def search_online(input_text):
        search = DuckDuckGoSearchRun().run(f"site:tripadvisor.com things to do{input_text}")
        return search if search else "No relevant search results found on TripAdvisor."
    
    def search_hotel(input_text):
        search = DuckDuckGoSearchRun().run(f"site:booking.com {input_text}")
        return search if search else "No relevant hotel search results found on Booking.com."
    
    def search_flight(input_text):
        search = DuckDuckGoSearchRun().run(f"site:skyscanner.com {input_text}")
        return search if search else "No relevant flight search results found on Skyscanner."
    
    def search_general(input_text):
        search = DuckDuckGoSearchRun().run(f"{input_text}")
        return search if search else "No relevant general search results found."
    ```
    
    ```python
    # app_run.py
    
    def hotel():
        data_hotel = {
            'textQuery': f'Place to stay near {destination}',
            'minRating': min_rating,
            'languageCode': 'ko',
            'locationBias': {
                "circle": {
                    "center": circle_center,
                    "radius": circle_radius
                }
            }
        }
    
        json_data_hotel = json.dumps(data_hotel)
        response_hotel = requests.post(url, data=json_data_hotel, headers=headers_place)
    
        if response_hotel.status_code == 200:
            result_hotel = response_hotel.json()
            if 'places' in result_hotel:
                df_hotel = pd.json_normalize(result_hotel['places'])
                df_hotel['type'] = 'Hotel'
                return df_hotel
            else:
                print("No 'places' key found in the hotel API response")
                return pd.DataFrame()
        else:
            print(f"Hotel API request failed with status code: {response_hotel.status_code}")
            return pd.DataFrame()
    
    def restaurant():
        data_restaurant = {
            'textQuery': f'Place to eat near {destination}',
            'minRating': min_rating,
            'languageCode': 'ko',
            'locationBias': {
                "circle": {
                    "center": circle_center,
                    "radius": circle_radius
                }
            }
        }
    
        json_data_restaurant = json.dumps(data_restaurant)
        response_restaurant = requests.post(url, data=json_data_restaurant, headers=headers_place)
    
        if response_restaurant.status_code == 200:
            result_restaurant = response_restaurant.json()
            if 'places' in result_restaurant:
                df_restaurant = pd.json_normalize(result_restaurant['places'])
                df_restaurant['type'] = 'Restaurant'
                return df_restaurant
            else:
                print("No 'places' key found in the restaurant API response")
                return pd.DataFrame()
        else:
            print(f"Restaurant API request failed with status code: {response_restaurant.status_code}")
            return pd.DataFrame()
    
    def tourist():
        data_tourist = {
            'textQuery': f'Tourist attraction near {destination}',
            'minRating': min_rating,
            'languageCode': 'ko',
            'locationBias': {
                "circle": {
                    "center": circle_center,
                    "radius": circle_radius
                }
            }
        }
    
        json_data_tourist = json.dumps(data_tourist)
        response_tourist = requests.post(url, data=json_data_tourist, headers=headers_place)
    
        if response_tourist.status_code == 200:
            result_tourist = response_tourist.json()
            if 'places' in result_tourist:
                df_tourist = pd.json_normalize(result_tourist['places'])
                df_tourist['type'] = 'Tourist'
                return df_tourist
            else:
                print("No 'places' key found in the tourist API response")
                return pd.DataFrame()
        else:
            print(f"Tourist API request failed with status code: {response_tourist.status_code}")
            return pd.DataFrame()
            
    df_hotel1 = hotel()
    df_restaurant1 = restaurant()
    df_tourist1 = tourist()
    
    # Assuming all three dataframes have similar columns
    if not df_hotel1.empty and not df_restaurant1.empty and not df_tourist1.empty:
        df_place = pd.concat([df_hotel1, df_restaurant1, df_tourist1], ignore_index=True)
        df_place = df_place.sort_values(by=['userRatingCount', 'rating'], ascending=[False, False]).reset_index(drop=True)
    
        df_place_rename = df_place[['type', 'displayName.text', 'formattedAddress', 'rating', 'userRatingCount', 'googleMapsUri', 'websiteUri', 'location.latitude', 'location.longitude', 'displayName.languageCode']]
        df_place_rename = df_place_rename.rename(columns={
            'displayName.text': 'Name',
            'rating': 'Rating',
            'googleMapsUri': 'Google Maps URL',
            'websiteUri': 'Website URL',
            'userRatingCount': 'User Rating Count',
            'location.latitude': 'Latitude',
            'location.longitude': 'Longitude',
            'formattedAddress': 'Address',
            'displayName.languageCode': 'Language Code',
            'type': 'Type'
        })
    else:
        print("One or more dataframes are empty. Skipping DataFrame concatenation and renaming.")
        df_place_rename = pd.DataFrame()
    ```
---
# 0423

- llama, koalpaca와 같은 다른 모델을 사용해보기 위해 만들었던 test 파일은 폐기
    - llama의 경우, 한국어 관련해서 문제가 있으며, 연동 관련해서 기술적 문제
    - koalpaca의 경우, 모델을 다운로드 하는 과정에서 램 용량(32GB)를 초과하는 이슈로 인해 자꾸 죽어버림
    - 사이즈가 작은 모델 조차도 다운로드에 애를 먹어 하드웨어적 이슈로 판단되어 포기
- 해봐야 할 것
    - map api 호출 시, 여전히 places 오류가 나타나는가? 만약 나타난다면, test로 만들었던 코드와 호출 방식 비교
    - 일반적으로 api 호출 시 데이터가 없을 경우 ‘{}’에 나타나는 현상으로 보임
    - 왜 데이터를 그렇게 받는지, 예외 처리를 넣어야하는 경우도 상정

- [imsi-0422.streamlit.app](http://imsi-0422.streamlit.app)
    - 길찾기 관련해서 국내의 경우 ‘대중교통’에서 길은 찾아줌, 어떤 대중교통을 이용하는지는 클릭하면 나오는 것으로 확인
    - 국외는 되지 않으며, 영/한 상관없이 나오지 않음
    - 새로고침 시, 로그인 유지가 안 됨(의도한 것인지 모름)
    - 챗봇 상태가 gpt3.5turbo도 엄청 올바른 답은 안해주는 듯
    - TRY-2
        
        > 남자 2명이 함께하는 도쿄 여행 1박 2일 일정을 제안드리겠습니다.
        > 
        > 
        > 일정:
        > 
        > - 첫째날:
        >     - 아침: 호텔 JAL City 하네다 도쿄에서 숙박  — ?
        >     - 오전: 하네다 공항에서 이동
        >     - 오후: 신주쿠에서 고질라 헤드를 구경하고 신주쿠 가이엔 가게에서 재미있는 선물을 구매
        >     - 저녁: 키치조지와 하모니카 앨리에서 바투어
        > - 둘째날:
        >     - 아침: 호텔에서 체크아웃 후 우에노에서 숙박
        >     - 오전: 선소지 사원 방문
        >     - 오후: 야마시로야 장난감 가게에서 새로운 추억 만들기
        >     - 점심: 하모니카 앨리에서 현지 음식 투어
        >     - 오후: 우에노에서 자전거 대여하여 도쿄를 탐험
        >     - 저녁: 우에노 근처의 맛집에서 저녁 식사
        > 
        > 이렇게 도쿄 여행을 즐길 수 있는 일정을 추천해드립니다. 즐거운 여행 되세요!
        > 
        - 장소들은 정상적이나, 계획을 세우는데 있어서 이슈가 있음
    - TRY-2
        
        > 남자 둘이서 후쿠오카 텐진으로 1박 2일 여행을 가려고 해, 아침 9시 비행기고 돌아올 떄는 저녁 6시 비행기야, 날씨와 관계 없이 사람들이 많이 가는 핫플레이스를 최대한 보고 오고 싶어
        > 
        - 2분 이상의 지연, 포기
