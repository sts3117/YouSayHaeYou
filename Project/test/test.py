import os
from dotenv import load_dotenv
import googlemaps
from googleapiclient.discovery import build
from langchain.llms import Anthropic

# .env 파일에서 API 키 읽어오기
load_dotenv()
maps_api_key = os.environ['GOOGLE_MAPS_API_KEY']
search_api_key = os.environ['GOOGLE_SEARCH_API_KEY']
search_engine_id = os.environ['SEARCH_ENGINE_ID']
anthropic_api_key = os.environ['ANTHROPIC_API_KEY']

# 구글 맵 클라이언트 생성
gmaps = googlemaps.Client(key=maps_api_key)

# 구글 검색 클라이언트 생성
service = build("customsearch", "v1", developerKey=search_api_key)

# Anthropic Claude 모델 초기화
claude = Anthropic(model="claude-3-sonnet-20240229", anthropic_api_key=anthropic_api_key)

# 검색할 도시, 반경, 여행 일수 입력받기
city = input("검색할 도시를 입력하세요: ")
radius = int(input("검색할 반경을 미터 단위로 입력하세요: "))
num_days = int(input("여행 일수를 입력하세요: "))

# 도시 이름을 지리적 좌표로 변환
geocode_result = gmaps.geocode(city)
if geocode_result:
    location = geocode_result[0]['geometry']['location']
    lat, lng = location['lat'], location['lng']
    search_location = f"{lat},{lng}"
else:
    print(f"{city}에 대한 위치 정보를 찾을 수 없습니다.")
    exit()

# 호텔, 음식점, 관광지 검색 및 정보 수집
places = []

# 호텔 검색
hotels = gmaps.places_nearby(location=search_location, radius=radius, type='lodging', language='ko', rank_by='prominence')
hotel_results = [hotel for hotel in hotels['results'] if hotel.get('rating') and hotel.get('vicinity')]

for hotel in hotel_results[:10]:
    name = hotel['name']
    if hotel.get('name_en'):
        name += f" ({hotel['name_en']})"
    
    # 웹 검색 결과 가져오기
    query = f"{name} {city} hotel"
    search_results = service.cse().list(q=query, cx=search_engine_id, num=1).execute()
    search_snippet = search_results['items'][0]['snippet'] if search_results['items'] else ""
    
    places.append({
        'name': name,
        'address': hotel['vicinity'],
        'rating': hotel['rating'],
        'search_snippet': search_snippet,
        'type': 'hotel'
    })

# 음식점 검색
restaurants = gmaps.places_nearby(location=search_location, radius=radius, type='restaurant', language='ko', rank_by='prominence')
restaurant_results = [restaurant for restaurant in restaurants['results'] if restaurant.get('rating') and restaurant.get('vicinity')]

for restaurant in restaurant_results[:10]:
    name = restaurant['name']
    if restaurant.get('name_en'):
        name += f" ({restaurant['name_en']})"
    
    # 웹 검색 결과 가져오기
    query = f"{name} {city} restaurant"
    search_results = service.cse().list(q=query, cx=search_engine_id, num=1).execute()
    search_snippet = search_results['items'][0]['snippet'] if search_results['items'] else ""
    
    places.append({
        'name': name,
        'address': restaurant['vicinity'],
        'rating': restaurant['rating'],
        'search_snippet': search_snippet,
        'type': 'restaurant'
    })

# 관광지 검색
attractions = gmaps.places_nearby(location=search_location, radius=radius, type='tourist_attraction', language='ko', rank_by='prominence')
attraction_results = [attraction for attraction in attractions['results'] if attraction.get('rating') and attraction.get('vicinity')]

for attraction in attraction_results[:10]:
    name = attraction['name']
    if attraction.get('name_en'):
        name += f" ({attraction['name_en']})"
    
    # 웹 검색 결과 가져오기
    query = f"{name} {city} tourist attraction"
    search_results = service.cse().list(q=query, cx=search_engine_id, num=1).execute()
    search_snippet = search_results['items'][0]['snippet'] if search_results['items'] else ""
    
    places.append({
        'name': name,
        'address': attraction['vicinity'],
        'rating': attraction['rating'],
        'search_snippet': search_snippet,
        'type': 'attraction'
    })

# Claude API를 사용하여 여행 코스 계획 생성
prompt = f"""
You are a travel planner assistant. Based on the following information about hotels, restaurants, and tourist attractions in {city}, create an optimal travel itinerary for a {num_days}-day trip. Consider factors such as ratings, location, and relevance to create a well-rounded and enjoyable experience.

Places:
{str(places)}
"""

itinerary = claude.generate([prompt]).generations[0][0].text

print(f"Here is your suggested travel itinerary for {city}:")
print(itinerary)