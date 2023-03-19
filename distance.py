import pprint
import openrouteservice as ors
import folium

def get_route(start_lat, start_lon, end_lat, end_lon):
    client = ors.Client(key = '5b3ce3597851110001cf62483b2035bb64ee4d0080a2aeb8bd28d07e')
    folium_map = folium.Map(location = list([start_lat, start_lon]), tiles = 'cartodbpositron', zoom_start = 13)

    # Coordinates for Open Route Service takes in Longitutde, Latitude
    coords = [[start_lon, start_lat], [end_lon, end_lat]]
    route = client.directions(coords, profile = 'driving-car', format = 'geojson')
    pprint.pprint(route)
    folium.PolyLine(locations = [list(reversed(coord)) for coord in route['features'][0]['geometry']['coordinates']], color = 'blue').add_to(folium_map)
    folium_map.save("map.html")

# get_route(1.4964559999542668, 103.74374661113058, 1.6125013180073793, 103.65816892145304)
