import openrouteservice as ors
import json
import requests
from math import radians, sin, cos, sqrt, atan2

api_cache = {} #API cache to store previous API calls to improve code efficiency and prevent wasted API calls

def haversine(lat1, lon1, lat2, lon2): #function to generate and return the euclidean distance between 2 gps coordinates
    R = 6371

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = (sin(dlat / 2) ** 2) + cos(radians(lat1)) * cos(radians(lat2)) * (sin(dlon / 2) ** 2)
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c

    return distance

def get_route_between_points(coord1, coord2): #function to identify and return the route between 2 points with an API call for driving
    lat1, lon1 = map(float, coord1.split(','))
    lat2, lon2 = map(float, coord2.split(','))
    client = ors.Client(key = '5b3ce3597851110001cf6248879e3b378ae54ee4b018db203ab99e9b')
    coords = [[lon1, lat1], [lon2, lat2]]
    route = client.directions(coords, profile = 'driving-car', format = 'geojson')
    route = route["features"][0]["geometry"]["coordinates"]
    return route

def get_walking_route_between_points(coord1, coord2): #function to identify and return the route between 2 points with an API call for walking
    lat1, lon1 = map(float, coord1.split(','))
    lat2, lon2 = map(float, coord2.split(','))
    client = ors.Client(key = '5b3ce3597851110001cf6248879e3b378ae54ee4b018db203ab99e9b')
    coords = [[lon1, lat1], [lon2, lat2]]
    route = client.directions(coords, profile = 'foot-walking', format = 'geojson')
    route = route["features"][0]["geometry"]["coordinates"]
    return route

def get_traffic_light_count_along_route(route): #function to identify and return the number of traffic lights with an API

    overpass_url = "http://overpass-api.de/api/interpreter"

    route_str = ' '.join(f"{lat} {lon}" for lon, lat in route)

    overpass_query = f"""
    [out:json];
    way(poly:"{route_str}")["highway"];
    node(w)["highway"="traffic_signals"];
    out count;
    """

    response = requests.get(overpass_url, params={"data": overpass_query})

    if response.status_code == 200:
        data = response.json()
        traffic_light_count = data["elements"][0]["tags"]["nodes"]
        return int(traffic_light_count)
    else:
        return "problem"
    
def calculateDistance_api(start_lat, start_lon, end_lat, end_lon): #function to generate and return the driving distance between 2 gps coordinates 

    client = ors.Client(key = '5b3ce3597851110001cf6248879e3b378ae54ee4b018db203ab99e9b')
    coords = [[start_lon, start_lat], [end_lon, end_lat]]
    route = client.directions(coords, profile = 'driving-car', format = 'geojson')
    distance = route['features'][0]['properties']['segments'][0]['distance']
    return distance

def generate_graph(input_json):

    output = {} #graph variable

    def distance_between_coordinates(coord1, coord2): #helper function to invoke haversine() function
        lat1, lon1 = map(float, coord1.split(','))
        lat2, lon2 = map(float, coord2.split(','))
        return haversine(lat1, lon1, lat2, lon2)
    
    def distance_between_coordinates_api(coord1, coord2): #helper function to invoke calculateDistance_api() function
        cache_key = tuple(sorted((coord1, coord2)))
        if cache_key in api_cache:
            return api_cache[cache_key]
        lat1, lon1 = map(float, coord1.split(','))
        lat2, lon2 = map(float, coord2.split(','))
        distance = calculateDistance_api(lat1, lon1, lat2, lon2)
        api_cache[cache_key] = distance
        return distance
    
    def generate_bus_stop_list(input_json): #generate a dictionary of bus stops and their gps to be used later on
        bus_stop_list = {}
        for bus_service, bus_stop in input_json.items():
            bus_stop_names = bus_stop["Bus stop"]
            gps = bus_stop["GPS Location"]
            for i in range(len(bus_stop_names)):
                current_stop_name = bus_stop_names[str(i)]
                current_stop_gps = gps[str(i)]
                bus_stop_list[current_stop_name] = current_stop_gps

        return bus_stop_list

    bus_stop_list = generate_bus_stop_list(input_json)

    for bus_service, bus_stops in input_json.items():
        bus_stop_ids = bus_stops["Stop ID"]
        bus_stop_names = bus_stops["Bus stop"]
        gps = bus_stops["GPS Location"]

        for i in range(len(bus_stop_ids) - 1): #iterate till before the last stop as we only need to connect to the last stop
            current_stop_name = bus_stop_names[str(i)] #identify current stop and gps
            current_stop_gps = gps[str(i)]

            if current_stop_name not in output: #add key if it does not exist inside the current graph
                output[current_stop_name] = {}

            adjacent_stops = output[current_stop_name]

            next_stop_name = bus_stop_names[str(i+1)] #identify next stop and gps
            next_stop_gps = gps[str(i+1)]

            distance_between_stops = distance_between_coordinates_api(current_stop_gps,next_stop_gps)/1000 #get distance between current stop and next stop
            route_between_stops = get_route_between_points(current_stop_gps, next_stop_gps) #get route between the current stop and next stop
            trafficlight_between_stops = get_traffic_light_count_along_route(route_between_stops) #get number of traffic lights between current stop and next stop based on the route
            timetaken_between_stops = (distance_between_stops / 40) * 60 #get time taken to go from current stop to next stop via driving

            #create a connection containing details between current stop and next stop
            connection = {"Distance": distance_between_stops, "Bus Service": bus_service, "Time": timetaken_between_stops, "Traffic Lights Count": trafficlight_between_stops, "Road Route": route_between_stops}
            if next_stop_name not in adjacent_stops: #add new connection for the key adjacent stop if it does not exist yet
                adjacent_stops[next_stop_name] = [connection]
            else: #append the connection as it represents another bus service heading from the current stop to the next stop
                adjacent_stops[next_stop_name].append(connection)

            for bus_stop_name, bus_stop_gps in bus_stop_list.items(): #iterate through our bus stop list to identify any other bus stops within a 500 radius from the current bus stop as an adjacent node
                if bus_stop_name == current_stop_name:
                    continue
                walking_distance_between_stops = distance_between_coordinates(current_stop_gps,bus_stop_gps) #get euclidean distance between the current stop and bus stop in the list
                if walking_distance_between_stops <= 0.5: #check euclidean distance between the current stop and bus stop in the list if within 500m radius
                    walking_route_between_stops = get_walking_route_between_points(current_stop_gps, bus_stop_gps) #get the walking route for walking
                    trafficlight_between_walking_route = get_traffic_light_count_along_route(walking_route_between_stops) #get traffic light count for the identified route
                    timetaken_walk_between_stops = (walking_distance_between_stops/4.4) * 60 #get time taken to go from current stop to next stop via walking

                    #create a walking connection containing details between the current stop and next stop
                    walk_connection = {"Distance": walking_distance_between_stops, "Bus Service": "Walking", "Time": timetaken_walk_between_stops, "Traffic Lights Count": trafficlight_between_walking_route, "Road Route": walking_route_between_stops}
                    existing_walk_connections = [conn for conn in adjacent_stops.get(bus_stop_name, []) if conn["Bus Service"] == "Walking"]
                    if not existing_walk_connections: #check for duplicate walking connections
                        if bus_stop_name not in adjacent_stops:
                            adjacent_stops[bus_stop_name] = [walk_connection]
                        else:
                            adjacent_stops[bus_stop_name].append(walk_connection)


    return output

input_json = json.loads(open('bus_stops_cleaned_revised.json').read())
output_json = generate_graph(input_json)

with open("test_revised.json", "w") as outfile:     
    json.dump(output_json, outfile, indent=4)