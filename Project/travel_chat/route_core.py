import googlemaps
import requests
import os, json
import folium
from streamlit_folium import folium_static
import pandas as pd
import polyline
from shapely.geometry import LineString, mapping
import random
import geopandas as gpd
from datetime import datetime, timedelta
from georouting.routers import OSRMRouter, GoogleRouter

url = 'https://places.googleapis.com/v1/places:searchText'


def geocodenate(input):
    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': os.environ["GOOGLE_MAP_API_KEY"],
        'X-Goog-FieldMask': 'places.location',
    }
    data = {
        'textQuery': input,
        'maxResultCount': 1,
    }

    # Convert data to JSON format
    json_data = json.dumps(data)

    # Make the POST request
    response = requests.post(url, data=json_data, headers=headers)

    # Print the response
    result = response.json()

    latitude = result["places"][0]['location']['latitude']
    longitude = result["places"][0]['location']['longitude']

    return latitude, longitude


def s_to_d(start, dest, sel):
    gmaps = googlemaps.Client(key=os.environ["GOOGLE_MAP_API_KEY"])

    # Geocoding an address
    geocode_result_start1, geocode_result_start2 = geocodenate(start)
    geocode_result_dest1, geocode_result_dest2 = geocodenate(dest)

    # # Look up an address with reverse geocoding
    # reverse_geocode_result = gmaps.reverse_geocode((40.714224, -73.961452))

    # Request directions via public transit
    now = datetime.now()
    # directions_result = gmaps.directions("Sydney Town Hall",
    #                                      "Parramatta, NSW",
    #                                      mode="transit",
    #                                      departure_time=now)
    #
    # # Validate an address with address validation
    # addressvalidation_result = gmaps.addressvalidation(['1600 Amphitheatre Pk'],
    #                                                    regionCode='US',
    #                                                    locality='Mountain View',
    #                                                    enableUspsCass=True)

    if sel == '차로':
        mode = "driving"
    elif sel == '걸어서':
        mode = "walking"
    else:
        mode = "transit"

    # create a router object with the google_key
    router = GoogleRouter(os.environ["GOOGLE_MAP_API_KEY"], mode=mode, language='ko')
    # router = OSRMRouter(mode=mode)
    # get the route between the origin and destination, this will return a Route object
    # this will call the Google Maps API
    if mode == "transit":
        gmaps = googlemaps.Client(key=os.environ["GOOGLE_MAP_API_KEY"])
        try:
            directions_result = gmaps.directions((geocode_result_start1, geocode_result_start2),
                                                 (geocode_result_dest1, geocode_result_dest2),
                                                 mode="transit")
            print(directions_result)
        except googlemaps.exceptions.ApiError as e:
            print(f"API Error: {e}")

        gdf = get_route_geopandas_for_transit(directions_result)
        route = router.get_route((geocode_result_start1, geocode_result_start2),
                                 (geocode_result_dest1, geocode_result_dest2))

        distance = route.get_distance() / 1000
        duration = route.get_duration()
        duration = str(timedelta(seconds=duration))

        start_point = geocode_result_start1, geocode_result_start2

        return gdf, route, distance, duration, start_point
    else:
        route = router.get_route((geocode_result_start1, geocode_result_start2),
                                 (geocode_result_dest1, geocode_result_dest2))

        distance = route.get_distance() / 1000
        duration = route.get_duration()
        duration = str(timedelta(seconds=duration))

        df = route.get_route_geopandas()

        return df, route, distance, duration


def get_route_geopandas_for_transit(input):
    """
        Returns a GeoDataFrame with information such as distance, duration, and speed of each step in the route. It is assumed that the polyline module is used for decoding the polyline into a LineString geometry. The GeoDataFrame is created with a specified coordinate reference system (CRS) of "4326".

        """

    steps_google = input[0]["legs"][0]["steps"]

    google_route1 = []
    for step in steps_google:
        step_g = {}
        step_g["distance (m)"] = step["distance"]["value"]
        step_g["duration (s)"] = step["duration"]["value"]
        try:
            decoded_points = polyline.decode(step["polyline"]["points"])
            if len(decoded_points) < 2:
                # If less than 2 points, create an empty LineString
                step_g["geometry"] = LineString()
            else:
                step_g["geometry"] = LineString(decoded_points)
        except Exception as e:
            # Handle any exceptions that occur during decoding
            print("Error decoding polyline:", e)
            continue
        #     step_g["geometry"] = LineString(step_g["geometry"])
        google_route1.append(step_g)
    google_route1 = gpd.GeoDataFrame(google_route1, geometry="geometry", crs="4326")
    google_route1["speed (m/s)"] = (
            google_route1["distance (m)"] / google_route1["duration (s)"]
    )
    data = pd.json_normalize(
        data=input,
        record_path=['legs', ['steps']],
    )

    google_route1['transit_details'] = data['transit_details.line.short_name']
    return google_route1


# GeoDataFrame으로부터 Folium 맵에 라인 그리기
def draw_route_on_folium(gdf, start_point):
    # Folium 맵 생성
    m = folium.Map(location=start_point, zoom_start=12)

    # 각 라인을 Folium 맵에 추가
    for idx, row in gdf.iterrows():
        if not row.geometry.is_empty:
            coordinates = mapping(row.geometry)["coordinates"]
            if len(coordinates) > 0:  # 좌표가 비어 있는지 확인
                transit_details = row['transit_details']

                # 랜덤한 색상 생성
                color = "#{:06x}".format(random.randint(0, 0xFFFFFF))

                # PolyLine으로 라인 그리기
                folium.PolyLine(
                    locations=coordinates,
                    color=color,
                    weight=5,
                    opacity=1,
                    popup=f'Route: {transit_details}'  # transit_details 정보를 팝업에 표시
                ).add_to(m)
            else:
                print("Empty coordinates for row:", idx)  # 좌표가 비어 있으면 인덱스를 출력하여 디버깅
        else:
            print("Empty geometry for row:", idx)  # 빈 라인이 있으면 인덱스를 출력하여 디버깅

    return m
