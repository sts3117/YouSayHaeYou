import streamlit as st
from streamlit_option_menu import option_menu
import os
from dotenv import load_dotenv
import json
import requests
import folium
from streamlit_folium import folium_static
import pandas as pd
import datetime 
from PIL import Image
from streamlit_autorefresh import st_autorefresh

st.set_page_config(layout="wide")
load_dotenv()

os.environ["GOOGLE_MAP_API_KEY"] = st.secrets["GOOGLE_MAP_API_KEY"]
os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
url = 'https://places.googleapis.com/v1/places:searchText'
img = Image.open('imgs\character.png')


def get_current_temperature(latitude: float, longitude: float) -> dict:
    """Fetch current temperature for given coordinates."""

    BASE_URL = "https://api.open-meteo.com/v1/forecast"

    # Parameters for the request
    params = {
        'latitude': latitude,
        'longitude': longitude,
        'hourly': 'temperature_2m',
        'forecast_days': 1,
    }

    # Make the request
    response = requests.get(BASE_URL, params=params)

    if response.status_code == 200:
        results = response.json()
    else:
        raise Exception(f"API Request failed with status code: {response.status_code}")

    current_utc_time = datetime.datetime.utcnow()
    time_list = [datetime.datetime.fromisoformat(time_str.replace('Z', '+00:00')) for time_str in
                 results['hourly']['time']]
    temperature_list = results['hourly']['temperature_2m']

    closest_time_index = min(range(len(time_list)), key=lambda i: abs(time_list[i] - current_utc_time))
    current_temperature = temperature_list[closest_time_index]

    return current_temperature


def createPage():
    #css 스타일 적용
    with open('style.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

    #tab 생성
    detail_tab, db_tab = st.tabs(['Detail', 'Data'])

    # #Autorefresh:
    # count = st_autorefresh(interval=5000, limit=100, key="fizzbuzzcounter")

    os.environ["GOOGLE_MAP_API_KEY"] = st.secrets["GOOGLE_MAP_API_KEY"]
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
    
    st.sidebar.markdown("---")
    st.sidebar.write('아래 내용을 모두 채워주세요.')
    destination = st.sidebar.text_input('어느 지역으로 가시나요?:', key='destination_app')
    min_rating = st.sidebar.number_input('최소 별점은 얼마로 할까요?:', value=4.0, min_value=0.5, max_value=4.5, step=0.5,
                                         key='minrating_app')
    radius = st.sidebar.number_input('몇 미터 반경으로 찾을까요?:', value=3000, min_value=500, max_value=50000, step=100, key='radius_app')
    

    if destination:
        with detail_tab: 
            headers = {
                'Content-Type': 'application/json',
                # 'X-Goog-Api-Key': api_key,
                'X-Goog-Api-Key':os.environ["GOOGLE_MAP_API_KEY"],
                'X-Goog-FieldMask': 'places.location',
            }
            data = {
                'textQuery': destination,
                'maxResultCount': 1,
            }

            # Convert data to JSON format
            json_data = json.dumps(data)

            # Make the POST request
            response = requests.post(url, data=json_data, headers=headers)

            # Print the response
            result = response.json()

            print("결과: ",result)

            # Convert JSON data to DataFrame
            df = pd.json_normalize(result['places'])

            # Get the latitude and longitude values
            initial_latitude = df['location.latitude'].iloc[0]
            initial_longitude = df['location.longitude'].iloc[0]

            # Create the circle
            circle_center = {"latitude": initial_latitude, "longitude": initial_longitude}
            circle_radius = radius

            headers_place = {
                'Content-Type': 'application/json',
                # 'X-Goog-Api-Key': api_key,
                'X-Goog-Api-Key': os.environ["GOOGLE_MAP_API_KEY"],
                'X-Goog-FieldMask': 'places.displayName,places.formattedAddress,places.priceLevel,places.userRatingCount,places.rating,places.websiteUri,places.location,places.googleMapsUri',
            }
            
            
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

                # Convert data to JSON format
                json_data_hotel = json.dumps(data_hotel)
                # Make the POST request
                response_hotel = requests.post(url, data=json_data_hotel, headers=headers_place)
                # Print the response
                result_hotel = response_hotel.json()
                print(result_hotel)
                # Convert JSON data to DataFrame
                df_hotel = pd.json_normalize(result_hotel['places'])
                # Add 'type'
                df_hotel['type'] = 'Hotel'
                return df_hotel

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

                # Convert data to JSON format
                json_data_restaurant = json.dumps(data_restaurant)
                # Make the POST request
                response_restaurant = requests.post(url, data=json_data_restaurant, headers=headers_place)
                # Print the response
                result_restaurant = response_restaurant.json()
                print(result_restaurant)
                # Convert JSON data to DataFrame
                df_restaurant = pd.json_normalize(result_restaurant['places'])
                # Add 'type'
                df_restaurant['type'] = 'Restaurant'
                return df_restaurant

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

                # Convert data to JSON format
                json_data_tourist = json.dumps(data_tourist)
                # Make the POST request
                response_tourist = requests.post(url, data=json_data_tourist, headers=headers_place)
                # Print the response
                result_tourist = response_tourist.json()
                print(result_tourist)
                # Convert JSON data to DataFrame
                df_tourist = pd.json_normalize(result_tourist['places'])
                # Add 'type'
                df_tourist['type'] = 'Tourist'
                return df_tourist

            df_hotel1 = hotel()
            df_restaurant1 = restaurant()
            df_tourist1 = tourist()

            # Assuming all three dataframes have similar columns
            df_place = pd.concat([df_hotel1, df_restaurant1, df_tourist1], ignore_index=True)
            df_place = df_place.sort_values(by=['userRatingCount', 'rating'], ascending=[False, False]).reset_index(
                drop=True)

            df_place_rename = df_place[
                ['type', 'displayName.text', 'formattedAddress', 'rating', 'userRatingCount', 'googleMapsUri', 'websiteUri',
                'location.latitude', 'location.longitude', 'displayName.languageCode']]
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

            def total_map():
                type_colour = {'Hotel': 'blue', 'Restaurant': 'green', 'Tourist': 'orange'}
                type_icon = {'Hotel': 'home', 'Restaurant': 'cutlery', 'Tourist': 'star'}
                print(df_place_rename['Latitude'][0], df_place_rename['Longitude'][0])
                mymap = folium.Map(location=(df_place_rename['Latitude'][0], df_place_rename['Longitude'][0]), zoom_start=9,
                                control_scale=True)

                for i in range(len(df_place_rename)):
                    icon_color = type_colour[df_place_rename['Type'][i]]
                    icon_type = type_icon[df_place_rename['Type'][i]]
                    icon = folium.Icon(color=icon_color, icon=icon_type)

                    # Use different icons for hotels, restaurants, and tourist attractions
                    folium.Marker(location=(df_place_rename['Latitude'][i], df_place_rename['Longitude'][i]), icon=icon,
                                popup="<i>{}</i>".format(df_place_rename['Name'][i])).add_to(mymap)

                folium_static(mymap)

            def database():
                st.dataframe(df_place_rename)
                total_map()

            def maps():
                #현재기온
                cur_temp = get_current_temperature(initial_latitude, initial_longitude)
                
                # 옷 추천 함수
                def recommend_clothing(cur_temp):
                    if cur_temp > 23:
                        text=(f"🥵 지금은 덥네요! 반팔을 챙겨가세요!")
                    elif cur_temp < 16:
                        text=(f"😰 지금은 춥네요! 긴팔을 챙겨가세요!")
                    else:
                        text=(f"😃 지금이 여행하기 딱 좋은 날씨! 바로 출발하세요!")
                    return text
                
                

                # 열을 만들고 현재 기온 표시
                col1, col2 = st.columns(2)
                with col1:
                    styled_text1 = f"""
                    <div style='text-align: center;'>
                        <div style='background-color:#f0f0f0; padding:10px; border-radius:10px;'>
                            <p style='font-size:26px; margin:0; font-weight: bold;'>{destination} 현재 기온</p>
                            <p style='font-size:24px; margin:0;'><b>🌡️{cur_temp}°C</b></p>
                        </div>
                    </div>
                    """
                    st.markdown(styled_text1, unsafe_allow_html=True)
                    

                # 열을 만들고 옷차림 추천 표시
                with col2:
                    txt = recommend_clothing(cur_temp)
                    sentence = txt.split('!')
                    styled_text2 = f"""
                    <div style='text-align: center;'>
                        <div style='background-color:#f0f0f0; padding:10px; border-radius:10px;'>
                            <p style='font-size:26px; margin:0; '><b>{sentence[0]}</b></p>
                            <p style='font-size:24px; margin:0;'><b>{sentence[1]}</b></p>
                        </div>
                    </div>
                    """
                    st.markdown(styled_text2, unsafe_allow_html=True)
                    
                st.markdown("---")    
    
                #선택지
                selected = option_menu(
                    menu_title = None,
                    options = ["호텔", "음식점", "여행지"],
                    icons = ['hotel', 'restaurant', 'plane'],
                    default_index=0,
                    orientation="horizontal",
                    styles={
                    "container": {"padding": "0!important"},    # "background-color": "#D7FFBF"
                    "icon": {"color": "orange", "font-size": "20px"}, 
                    "nav-link": {"font-size": "20px", "text-align": "center", "margin":"0px", "--hover-color": "#BCBCBC"},
                    "nav-link-selected": {"background-color": "green"},
                    }
                    )
                print(selected)
                
                # 검색 결과 표시
                initial_location = [initial_latitude, initial_longitude]
                type_colour = {'Hotel': 'blue', 'Restaurant': 'green', 'Tourist': 'orange'}
                type_icon = {'Hotel': 'home', 'Restaurant': 'cutlery', 'Tourist': 'star'}
                
                st.subheader(f"{destination} 근처에서 {selected}들을 찾아봤어요!")
                
                
                # Search Result
                if selected == '호텔':
                    df_place = df_hotel1
                    with st.spinner("잠시만 기다려주세요..."):
                        for index, row in df_place.iterrows():
                            location = [row['location.latitude'], row['location.longitude']]
                            mymap = folium.Map(location=initial_location,
                                            zoom_start=9, control_scale=True)
                            content = (str(row['displayName.text']) + '<br>' +
                                    'Rating: ' + str(row['rating']) + '<br>' +
                                    'Address: ' + str(row['formattedAddress']) + '<br>' +
                                    'Website: ' + str(row['websiteUri'])
                                    )
                            iframe = folium.IFrame(content, width=300, height=125)
                            popup = folium.Popup(iframe, max_width=300)

                            icon_color = type_colour[row['type']]
                            icon_type = type_icon[row['type']]
                            icon = folium.Icon(color=icon_color, icon=icon_type)

                            # Use different icons for hotels, restaurants, and tourist attractions
                            folium.Marker(location=location, popup=popup, icon=icon).add_to(mymap)
                            st.markdown("---")
                            
                            # title
                            st.header(f"{index + 1}. {row['displayName.text']}")
                            
                            # column 생성 및 비율 설정
                            col1, col2 = st.columns([5.5, 4.5])
                            
                            with col1:
                                folium_static(mymap)
                            with col2:
                                styled_text3 = f"""
                                <div style='text-align: left;'>
                                    <div style='background-color:#f0f0f0; padding:10px; border-radius:10px;'>
                                        <p style='font-size:20px; margin:0; '><b>📌 평점: {row['rating']}</b></p>
                                        <br>
                                        <p style='font-size:20px; margin:0;'><b>📌 주소: {row['formattedAddress']}</b></p>
                                        <br>
                                        <p style='font-size:20px; margin:0;'><b>📌 웹사이트: 
                                            <a herf= {row['websiteUri']}> 공식 홈페이지 </a> 
                                            </b></p>
                                        <br>
                                        <p style='font-size:20px; margin:0;'><b>📌 추가적인 정보: 
                                            <a herf= {row['googleMapsUri']}> 지도에서 확인하기 </a>
                                            </b></p>
                                    </div>
                                </div>
                                """
                                st.markdown(styled_text3, unsafe_allow_html=True)
                                
                            st.markdown("---")


                elif selected == '음식점':
                    df_place = df_restaurant1
                    with st.spinner("잠시만 기다려주세요..."):
                        for index, row in df_place.iterrows():
                            location = [row['location.latitude'], row['location.longitude']]
                            mymap = folium.Map(location=initial_location,
                                            zoom_start=9, control_scale=True)
                            content = (str(row['displayName.text']) + '<br>' +
                                    'Rating: ' + str(row['rating']) + '<br>' +
                                    'Address: ' + str(row['formattedAddress']) + '<br>' +
                                    'Website: ' + str(row['websiteUri'])
                                    )
                            iframe = folium.IFrame(content, width=300, height=125)
                            popup = folium.Popup(iframe, max_width=300)

                            icon_color = type_colour[row['type']]
                            icon_type = type_icon[row['type']]
                            icon = folium.Icon(color=icon_color, icon=icon_type)

                            # Use different icons for hotels, restaurants, and tourist attractions
                            folium.Marker(location=location, popup=popup, icon=icon).add_to(mymap)
                            st.markdown("---")

                            # title
                            st.header(f"{index + 1}. {row['displayName.text']}")
                            
                            
                            # column 생성 및 비율 설정
                            col1, col2 = st.columns([5.5, 4.5])
                            
                            with col1:
                                folium_static(mymap)
                            with col2:
                                styled_text3 = f"""
                                <div style='text-align: left;'>
                                    <div style='background-color:#f0f0f0; padding:10px; border-radius:10px;'>
                                        <p style='font-size:20px; margin:0; '><b>📌 평점: {row['rating']}</b></p>
                                        <br>
                                        <p style='font-size:20px; margin:0;'><b>📌 주소: {row['formattedAddress']}</b></p>
                                        <br>
                                        <p style='font-size:20px; margin:0;'><b>📌 웹사이트: 
                                            <a herf= {row['websiteUri']}> 공식 홈페이지 </a> 
                                            </b></p>
                                        <br>
                                        <p style='font-size:20px; margin:0;'><b>📌 추가적인 정보: 
                                            <a herf= {row['googleMapsUri']}> 지도에서 확인하기 </a>
                                            </b></p>
                                    </div>
                                </div>
                                """
                                st.markdown(styled_text3, unsafe_allow_html=True)
                                
                            st.markdown("---")
                            
                else:
                    df_place = df_tourist1
                    with st.spinner("잠시만 기다려주세요..."):
                        for index, row in df_place.iterrows():
                            location = [row['location.latitude'], row['location.longitude']]
                            mymap = folium.Map(location=initial_location,
                                            zoom_start=9, control_scale=True)
                            content = (str(row['displayName.text']) + '<br>' +
                                    'Rating: ' + str(row['rating']) + '<br>' +
                                    'Address: ' + str(row['formattedAddress']) + '<br>' +
                                    'Website: ' + str(row['websiteUri'])
                                    )
                            iframe = folium.IFrame(content, width=300, height=125)
                            popup = folium.Popup(iframe, max_width=300)

                            icon_color = type_colour[row['type']]
                            icon_type = type_icon[row['type']]
                            icon = folium.Icon(color=icon_color, icon=icon_type)

                            # Use different icons for hotels, restaurants, and tourist attractions
                            folium.Marker(location=location, popup=popup, icon=icon).add_to(mymap)
                            st.markdown("---")

                            #title
                            st.header(f"{index + 1}. {row['displayName.text']}")
                            
                            
                            # column 생성 및 비율 설정
                            col1, col2 = st.columns([5.5, 4.5])
                            
                            with col1:
                                folium_static(mymap)
                            with col2:
                                styled_text3 = f"""
                                <div style='text-align: left;'>
                                    <div style='background-color:#f0f0f0; padding:10px; border-radius:10px;'>
                                        <p style='font-size:20px; margin:0; '><b>📌 평점: {row['rating']}</b></p>
                                        <br>
                                        <p style='font-size:20px; margin:0;'><b>📌 주소: {row['formattedAddress']}</b></p>
                                        <br>
                                        <p style='font-size:20px; margin:0;'><b>📌 웹사이트: 
                                            <a herf= {row['websiteUri']}> 공식 홈페이지 </a> 
                                            </b></p>
                                        <br>
                                        <p style='font-size:20px; margin:0;'><b>📌 추가적인 정보: 
                                            <a herf= {row['googleMapsUri']}> 지도에서 확인하기 </a>
                                            </b></p>
                                    </div>
                                </div>
                                """
                                st.markdown(styled_text3, unsafe_allow_html=True)
                                
                            st.markdown("---")
            
            #실행                
            maps()
        
        with db_tab:
            database()
    else:
        left_co, cent_co,last_co = st.columns(3)
        with cent_co:
            st.image(img, width=500, ) 