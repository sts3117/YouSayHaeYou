# import library 
import asyncio

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
import streamlit as st
import pandas as pd
import json
import requests
import os, time
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import folium
from streamlit_folium import folium_static
from functools import lru_cache
import chatbot_core
# import route_core
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import HuggingFaceEmbeddings  
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.document_loaders import DataFrameLoader
from langchain.agents import tool
import datetime

load_dotenv()

url = 'https://places.googleapis.com/v1/places:searchText'

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

def main():

    st.sidebar.write('아래 내용을 모두 채워주세요.')
    destination = st.sidebar.text_input('어느 지역으로 가시나요?:', key='destination_app')
    min_rating = st.sidebar.number_input('최소 별점은 얼마로 할까요?:', value=4.0, min_value=0.5, max_value=4.5, step=0.5, key='minrating_app')
    radius = st.sidebar.number_input('몇 미터 반경으로 찾을까요?:', value=3000, min_value=500, max_value=50000, step=100, key='radius_app')
    
    if destination:
        headers = {
            'Content-Type': 'application/json',
            'X-Goog-Api-Key': os.environ["GOOGLE_MAPS_API_KEY"],
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

        print(result)

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
            'X-Goog-Api-Key': os.environ["GOOGLE_MAPS_API_KEY"],
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

        def route():
            st.header(f'길 찾기 🗺️')
            start = st.text_input('어디에서 출발하시나요?:')
            dest = st.text_input('어디로 가시나요?:')
            sel = st.selectbox('어떻게 가시나요?', ('대중교통으로', '걸어서', '차로'))
            if st.button('길 찾기'):
                ddf, route1 = route_core.s_to_d(start, dest, sel)
                m1 = route1.plot_route()
                folium_static(m1)

        def maps():
            st.header("🌏 여행 가이드 🌏")

            places_type = st.radio('무엇을 찾고 계신가요?: ', ["호텔 🏨", "음식점 🍴", "관광 ⭐"])
            initial_location = [initial_latitude, initial_longitude]
            type_colour = {'Hotel': 'blue', 'Restaurant': 'green', 'Tourist': 'orange'}
            type_icon = {'Hotel': 'home', 'Restaurant': 'cutlery', 'Tourist': 'star'}

            st.subheader(f"{destination} 근처에서 {places_type}을 찾아봤어요!")
            cur_temp = get_current_temperature(initial_latitude, initial_longitude)
            st.text(f"{destination}의 현재 기온은 {cur_temp}°C 에요!")
            if cur_temp > 23:
                st.text(f"덥네요! 반팔을 챙겨가세요!")
            elif cur_temp < 16:
                st.text(f"춥네요! 긴팔을 챙겨가세요!")
            else:
                st.text(f"지금이 여행하기 딱 좋은 날씨! 바로 출발하세요!")

            if places_type == '호텔 🏨':
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

                        st.write(f"## {index + 1}. {row['displayName.text']}")
                        folium_static(mymap)
                        st.write(f"평점: {row['rating']}")
                        st.write(f"주소: {row['formattedAddress']}")
                        st.write(f"웹사이트: {row['websiteUri']}")
                        st.write(f"추가적인 정보: {row['googleMapsUri']}\n")


            elif places_type == '음식점 🍴':
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

                        st.write(f"## {index + 1}. {row['displayName.text']}")
                        folium_static(mymap)
                        st.write(f"평점: {row['rating']}")
                        st.write(f"주소: {row['formattedAddress']}")
                        st.write(f"웹사이트: {row['websiteUri']}")
                        st.write(f"추가적인 정보: {row['googleMapsUri']}\n")
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

                        st.write(f"## {index + 1}. {row['displayName.text']}")
                        folium_static(mymap)
                        st.write(f"평점: {row['rating']}")
                        st.write(f"주소: {row['formattedAddress']}")
                        st.write(f"웹사이트: {row['websiteUri']}")
                        st.write(f"추가적인 정보: {row['googleMapsUri']}\n")

        def chatbot():
            class Message(BaseModel):
                actor: str
                payload: str

            # llm = ChatOpenAI(openai_api_key=os.environ["OPENAI_API_KEY"], model_name='gpt-3.5-turbo', temperature=0)

            USER = "user"
            ASSISTANT = "ai"
            MESSAGES = "messages"

            # def initialize_session_state():
            if MESSAGES not in st.session_state:
                st.session_state[MESSAGES] = [Message(actor=ASSISTANT, payload="안녕하세요! 어떤 도움이 필요하신가요?")]

            msg: Message
            for msg in st.session_state[MESSAGES]:
                st.chat_message(msg.actor).write(msg.payload)

            # Prompt
            query: str = st.chat_input("이곳에 질문을 입력하세요.")

            # Combine info
            df_place['combined_info'] = df_place.apply(lambda
                                                           row: f"Type: {row['type']}, Name: {row['displayName.text']}. Rating: {row['rating']}. Address: {row['formattedAddress']}. Website: {row['websiteUri']}",
                                                       axis=1)
            # Load Processed Dataset
            loader = DataFrameLoader(df_place, page_content_column="combined_info")
            docs = loader.load()

            # Document splitting
            text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            texts = text_splitter.split_documents(docs)

            # embeddings model
            # Define the path to the pre-trained model you want to use
            modelPath = "sentence-transformers/all-MiniLM-l6-v2"

            # Create a dictionary with model configuration options, specifying to use the CPU for computations
            model_kwargs = {'device': 'cpu'}

            # Create a dictionary with encoding options, specifically setting 'normalize_embeddings' to False
            encode_kwargs = {'normalize_embeddings': False}

            # Initialize an instance of HuggingFaceEmbeddings with the specified parameters
            embeddings = HuggingFaceEmbeddings(
                model_name=modelPath,  # Provide the pre-trained model's path
                model_kwargs=model_kwargs,  # Pass the model configuration options
                encode_kwargs=encode_kwargs  # Pass the encoding options
            )

            # Vector DB
            vectorstore = FAISS.from_documents(texts, embeddings)

            agent_executor = chatbot_core.agent()

            if query:
                st.session_state[MESSAGES].append(Message(actor=USER, payload=str(query)))
                st.chat_message(USER).write(query)

                with st.spinner("생각중이에요..."):
                    start_time = time.time()
                    response: str = agent_executor.invoke({'input': query})['output']
                    end_time = time.time()  # 종료 시간 기록
                    execution_time = end_time - start_time  # 실행 시간 계산
                    print(f"Response Generation Time: {execution_time:.2f} seconds")

                    st.session_state[MESSAGES].append(Message(actor=ASSISTANT, payload=response))
                    st.chat_message(ASSISTANT).write(response)
            # st.write("Chatbot")
        
        method = st.sidebar.radio(" ", ["검색 🔎","챗봇 🤖", "데이터베이스 📑","길찾기 🗺️"], key="method_app")
        if method == "검색 🔎":
            maps()
        elif method == "챗봇 🤖":
            chatbot()
        elif method == "데이터베이스 📑":
            database()
        else:
            route()

    js = '''
    <script>
        var body = window.parent.document.querySelector(".main");
        console.log(body);
        body.scrollTop = 0;
    </script>
    '''

    if st.button(f"위로 이동"):
        st.components.v1.html(js)
        
    st.sidebar.markdown(''' 
        ## Created by: 
        Team.알리미\n
        [한컴아카데미](https://hancomacademy.com/) with nvidia\n
        special thanks to Ahmad Luay Adnani
        ''')
    st.image("https://camo.githubusercontent.com/6be6e494569696bede37e8b21f6ebe646fdbad1c81e39082e5136bf5a8afc067/68747470733a2f2f63617073756c652d72656e6465722e76657263656c2e6170702f6170693f747970653d776176696e6726636f6c6f723d6175746f266865696768743d3230302673656374696f6e3d68656164657226746578743d416c692d6d6526666f6e7453697a653d3930")
        
if __name__ == '__main__':
    main()