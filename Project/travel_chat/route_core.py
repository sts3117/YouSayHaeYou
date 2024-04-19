import googlemaps
import requests
import os, json
import folium
from streamlit_folium import folium_static
from datetime import datetime
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
    route = router.get_route((geocode_result_start1, geocode_result_start2),
                             (geocode_result_dest1, geocode_result_dest2))

    df = route.get_route_geopandas()

    return df, route
