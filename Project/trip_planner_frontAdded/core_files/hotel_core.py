from selenium import webdriver
from selenium.webdriver.common.by import By
from urllib.parse import urlencode
from selenium.webdriver.chrome.options import Options
import traceback
import time
import json
import re
from typing import Type

from pydantic.v1 import BaseModel, Field
from langchain.tools import BaseTool, StructuredTool, tool
import chromedriver_autoinstaller


chromedriver_autoinstaller.install(cwd=True, path="C:\Program Files\Google\Chrome\Application\chrome.exe")


class schema_hotel(BaseModel):
    """Inputs for function"""
    destination: str = Field(..., description="The place where user will stay.")
    IN: str = Field(..., description="It is your check-in date, It has to be like this: 2024-05-04")
    OUT: str = Field(..., description="It is your check-out date, It has to be like this: 2024-05-05")
    person: int = Field(..., description="It is how many people will stay.")
    rooms: int = Field(..., description="It is how many rooms to reserve.")


class SearchTool_hotel():
    name = "hotel_search_tool"
    description = "useful when you need to search hotel"
    args_schema: Type[BaseModel] = schema_hotel

    def _run(self, destination, IN, OUT, person, rooms):
        return main(destination, IN, OUT, person, rooms)

    def _arun(self, destination, IN, OUT, person, rooms):
        raise NotImplementedError("error: arun Not Implemented")


@tool
def input_parser_hotel(input_text):
    """
    useful when you need to search hotel
    """
    matches = re.findall(r'([A-Za-z]+|[0-9-]+|\d)', input_text)
    destination = matches[0]
    IN = matches[1]
    OUT = matches[2]
    person = matches[3]
    rooms = matches[4]
    return SearchTool_hotel()._run(destination, IN, OUT, person, rooms)


# 함수 정의
def extract_hotel_data(driver):
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

    hotel_list = driver.find_elements(By.CLASS_NAME,
                                      'uitk-card.uitk-card-roundcorner-all.uitk-card-has-border.uitk-card-has-primary-theme')

    # 호텔 데이터 추출 및 저장
    hotel_data = []
    for hotel in hotel_list[2:52]:  # 앞에 2개는 광고라 뺌, 50개만 일단 추출
        name_element = hotel.find_element(By.CSS_SELECTOR,
                                          '.uitk-heading.uitk-heading-5.overflow-wrap.uitk-layout-grid-item.uitk-layout-grid-item-has-row-start')
        name = name_element.text
        print(name)

        price_element = hotel.find_element(By.CSS_SELECTOR,
                                           '.uitk-text.uitk-type-500.uitk-type-medium.uitk-text-emphasis-theme')
        price_string = price_element.text
        price = extract_numeric_price(price_string)
        print(price)

        rating_element = hotel.find_element(By.CSS_SELECTOR, '.uitk-badge-base-text')
        rating = rating_element.text
        print(rating)

        hotel_data.append({"name": name, "price": price, "rating": rating})

    return hotel_data


def extract_numeric_price(price_string):
    # 가격 문자열에서 숫자만 추출
    numeric_price = re.sub(r'[^0-9]', '', price_string)
    return numeric_price


def main(destination, IN, OUT, person, rooms):
    base_url = "https://kr.hotels.com/Hotel-Search?"

    # 입력값
    destination = destination  # '후쿠오카'
    d1 = IN  # '2024-05-04'
    d2 = OUT  # '2024-05-05'
    adults = person  # '2'
    rooms = rooms  # '1'

    # 고정값 설정
    flexibility = '0_DAY'
    startDate = d1
    endDate = d2

    query_params = {
        'destination': destination,
        'flexibility': flexibility,
        'd1': d1,
        'startDate': startDate,
        'd2': d2,
        'endDate': endDate,
        'adults': adults,
        'rooms': rooms
    }

    url_with_params = base_url + urlencode(query_params)

    # Chrome WebDriver 옵션 설정
    chrome_options = Options()
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
    chrome_options.add_argument("headless")

    # WebDriver 실행
    start_time = time.time()
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url_with_params)
    time.sleep(1)

    try:
        # 호텔 데이터 추출
        hotel_data = extract_hotel_data(driver)

        # 데이터 저장 (json)
        # with open("hotel_data.json", "w", encoding="utf-8") as f:
        #     json.dump(hotel_data, f, ensure_ascii=False, indent=4)
        return hotel_data

    except Exception as e:
        print(f"Error occurred: {e}")
        traceback.print_exc()

    finally:
        # WebDriver 종료
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Response Generation Time: {execution_time:.2f} seconds")
        driver.quit()