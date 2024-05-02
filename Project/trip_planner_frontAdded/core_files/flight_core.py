from selenium import webdriver
from selenium.webdriver.common.by import By
from urllib.parse import urlencode
from selenium.webdriver.chrome.options import Options
import traceback
import time
import json
import re
from typing import Type
import csv
from pydantic.v1 import BaseModel, Field
from langchain.tools import BaseTool, StructuredTool, tool
import chromedriver_autoinstaller


chromedriver_autoinstaller.install(cwd=True, path="C:\Program Files\Google\Chrome\Application\chrome.exe")


class schema_flight(BaseModel):
    """Inputs for function"""
    starting: str = Field(..., description="The place where user will start, must be IATA code.")
    destination: str = Field(..., description="The place where user want to go, must be IATA code.")
    d1: int = Field(..., description="It is your departure date, It has to be like this: 20240501")
    d2: int = Field(..., description="It is your return date, It has to be like this: 20240502, in case of one-way travel it has to be like this: 00000000")
    adults: int = Field(..., description="It is how many people to reserve.")
    where: str = Field(..., description="It is about traveling abroad or domestically, if user wants to move within Korea it has to be: dome, if it is not it has to be: inte")
    oneway: int = Field(..., description="It is about whether the user wants to travel one way or round trip, if user wants to travel one way it has to be: one, if it is not it has to be: round")


class SearchTool_flight():
    name = "hotel_search_tool"
    description = "useful when you need to search flight"
    args_schema: Type[BaseModel] = schema_flight

    def _run(self, starting, destination, d1, d2, adults, where, oneway):
        return main(starting, destination, d1, d2, adults, where, oneway)

    def _arun(self, starting, destination, d1, d2, adults, where, oneway):
        raise NotImplementedError("error: arun Not Implemented")


@tool
def input_parser_flight(input_text):
    """
    useful when you need to search flight
    """
    matches = re.findall(r'([A-Za-z]+|\d{8}|[0-9-]+|\d+)', input_text)
    starting = matches[0]
    destination = matches[1]
    d1 = matches[2]
    d2 = matches[3]
    adults = matches[4]
    where = matches[5]
    oneway = matches[6]
    return SearchTool_flight()._run(starting, destination, d1, d2, adults, where, oneway)


# csv 에서 찾는 코드
# def find_airport_code(region):
#     with open("code.csv", "r", encoding='UTF-8') as file:
#         reader = csv.reader(file, delimiter=',')
#         for row in reader:
#             if region.lower() in row[1].lower():
#                 return row[2]
#     return None

# region = input("지역을 입력하세요: ")
# code = find_airport_code(region)

# if code:
#     print(f"{region}의 공항 코드는 {code}입니다.")
# else:
#     print(f"{region}에 해당하는 공항 코드를 찾을 수 없습니다.")

# 함수 정의
def extract_flight_data(driver, oneway):
    # 웹페이지 로딩 대기
    driver.implicitly_wait(10)

    # 화면 스크롤
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    time.sleep(1)

    round_trip = driver.find_elements(By.CLASS_NAME, 'concurrent_ConcurrentItemContainer__2lQVG')
    oneway_trip = driver.find_elements(By.CLASS_NAME, 'indivisual_IndivisualItem__3co62')

    # 항공 데이터 추출 및 저장
    flight_data = []
    if oneway == 'round':
        for flight in round_trip[:30]:
            name_element = flight.find_element(By.CSS_SELECTOR, '.airline_name__Tm2wJ')
            name = name_element.text
            # print(name)

            price_element = flight.find_element(By.CSS_SELECTOR, '.item_num__3R0Vz')
            price_string = price_element.text
            price = extract_numeric_price(price_string)
            # print(price)

            route_elements = flight.find_elements(By.CLASS_NAME, 'route_Route__2UInh')

            go_time_element = route_elements[0].find_element(By.CSS_SELECTOR, '.route_time__-2Z1T')
            go_time = go_time_element.text
            # print(go_time)

            arrive_time_element = route_elements[0].find_elements(By.CSS_SELECTOR, '.route_time__-2Z1T')[1]
            arrive_time = arrive_time_element.text
            # print(arrive_time)

            duration_element = route_elements[0].find_element(By.CSS_SELECTOR, '.route_info__1RhUH')
            duration = duration_element.text.split(', ')[1]
            # print(duration)

            return_time_element = route_elements[1].find_element(By.CSS_SELECTOR, '.route_time__-2Z1T')
            return_time = return_time_element.text
            # print(return_time)

            return_arrive_element = route_elements[1].find_elements(By.CSS_SELECTOR, '.route_time__-2Z1T')[1]
            return_arrive = return_arrive_element.text
            # print(return_arrive)

            return_duration_element = route_elements[1].find_element(By.CSS_SELECTOR, '.route_info__1RhUH')
            return_duration = return_duration_element.text.split(', ')[1]
            # print(return_duration)

            flight_data.append({
                "name": name,
                "price": price,
                "go_time": go_time,
                "arrive_time": arrive_time,
                "duration": duration,
                "return_time": return_time,
                "return_arrive": return_arrive,
                "return_duration": return_duration
            })
            print(flight_data)
    if oneway == "one":
        for flight in oneway_trip[:30]:
            name_element = flight.find_element(By.CSS_SELECTOR, '.airline_name__Tm2wJ')
            name = name_element.text
            # print(name)

            price_element = flight.find_element(By.CSS_SELECTOR, '.item_num__3R0Vz')
            price_string = price_element.text
            price = int(price_string.replace(',', ''))
            # print(price)

            go_time_element = flight.find_element(By.CSS_SELECTOR, '.route_time__-2Z1T')
            go_time = go_time_element.text
            # print(go_time)

            arrive_time_element = flight.find_elements(By.CSS_SELECTOR, '.route_time__-2Z1T')[1]
            arrive_time = arrive_time_element.text
            # print(arrive_time)

            duration_element = flight.find_element(By.CSS_SELECTOR, '.route_info__1RhUH')
            duration = duration_element.text.split(', ')[1]
            # print(duration)

            flight_data.append({
                "name": name,
                "price": price,
                "go_time": go_time,
                "arrive_time": arrive_time,
                "duration": duration
            })
            print(flight_data)

    return flight_data


def extract_numeric_price(price_string):
    # 가격 문자열에서 숫자만 추출
    numeric_price = re.sub(r'[^0-9]', '', price_string)
    return numeric_price


def main(starting, destination, d1, d2, adults, where, oneway):
    base_url = "https://flight.naver.com/flights/"

    # 예시 URL : https://flight.naver.com/flights/domestic/SEL-CJU-20240502/CJU-SEL-20240504?adult=1&fareType=YC
    # 입력값
    starting = starting   # 'ICN'  # find_airport_code('샤를 드 골')  # 변경 필요
    destination = destination   # 'FCO'  # find_airport_code('피우미치노') # 변경 필요
    d1 = d1   # '20240501'
    d2 = d2   # '20240503'
    adults = adults   # '1'
    where = where   # '국외'
    oneway = oneway   # False

    def checkwhere(where):
        if where == "inte":
            return 'international'
        else:
            return 'domestic'

    query_params = {
        'adult': adults,
        'fareType': 'Y',
        'Direct': 'True'
    }

    url_with_params_round = base_url + checkwhere(
        where) + '/' + starting + '-' + destination + '-' + d1 + '/' + destination + '-' + starting + '-' + d2 + '?' + urlencode(
        query_params)

    url_with_params_oneway = base_url + checkwhere(
        where) + '/' + starting + '-' + destination + '-' + d1 + '?' + urlencode(
        query_params)

    # print(url_with_params_round)
    """ 네이버 항공권은, 검색할 때, URL에 국내/국외, 날짜, 공항코드(IATA), 조건(사람 수 등)으로 검색을 함,
    그래서 공항코드를 매핑하기 위해 csv에서 찾는데, 이 부분을 아마데우스에서 대체가 가능하면 변경"""

    # Chrome WebDriver 옵션 설정
    chrome_options = Options()
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
    # chrome_options.add_argument("Cookie=NNB=XPU7KG555H3GG; ba.uuid=a5682dcc-3972-4d95-9ea3-9a8e30efae5c; BUC=aejv8NNJQZRh4d37mkRzxF-84CsXYe0edpLpawVGj20=; ba.uuid=0")
    chrome_options.add_argument("--headless")  # 백그라운드 동작
    chrome_options.add_argument("--incognito")  # 시크릿 모드

    # WebDriver 실행
    start_time = time.time()
    driver = webdriver.Chrome(options=chrome_options)
    if oneway == "one":
        driver.get(url_with_params_oneway)
    else:
        driver.get(url_with_params_round)
    time.sleep(10)

    try:
        # 항공 데이터 추출
        flight_data = extract_flight_data(driver, oneway)

        # 데이터 저장 (json)
        # with open("flight_data.json", "w", encoding="utf-8") as f:
        #     json.dump(flight_data, f, ensure_ascii=False, indent=4)
        return flight_data

    except Exception as e:
        print(f"Error occurred: {e}")
        traceback.print_exc()

    finally:
        # WebDriver 종료
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Response Generation Time: {execution_time:.2f} seconds")
        driver.quit()

