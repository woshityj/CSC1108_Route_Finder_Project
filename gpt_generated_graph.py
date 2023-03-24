import heapq
import openrouteservice as ors
import json
from math import radians, sin, cos, sqrt, atan2

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth's radius in km

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = (sin(dlat / 2) ** 2) + cos(radians(lat1)) * cos(radians(lat2)) * (sin(dlon / 2) ** 2)
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c

    return distance

def calculateDistance_api(start_lat, start_lon, end_lat, end_lon):

    client = ors.Client(key = '5b3ce3597851110001cf62483b2035bb64ee4d0080a2aeb8bd28d07e')
    coords = [[start_lon, start_lat], [end_lon, end_lat]]
    route = client.directions(coords, profile = 'driving-car', format = 'geojson')
    distance = route['features'][0]['properties']['segments'][0]['distance']
    return distance

def generate_adjacent_stops(input_json):
    output = {}
    
    # Helper function to calculate euclidean distance between two GPS coordinates
    def distance_between_coordinates(coord1, coord2):
        lat1, lon1 = map(float, coord1.split(','))
        lat2, lon2 = map(float, coord2.split(','))
        return haversine(lat1, lon1, lat2, lon2)
    
    # Helper function to calculate road travel distance between two GPS coordinates
    def distance_between_coordinates_api(coord1, coord2):
        lat1, lon1 = map(float, coord1.split(','))
        lat2, lon2 = map(float, coord2.split(','))
        return calculateDistance_api(lat1, lon1, lat2, lon2)

    # First, create a list of all unique bus stops with their GPS coordinates
    bus_stops_list = {}
    for route_key, bus_stops in input_json.items():
        bus_stop_names = bus_stops["Bus stop"]
        gps_locations = bus_stops["GPS Location"]
        for i in range(len(bus_stop_names)):
            stop_name = bus_stop_names[str(i)]
            stop_gps = gps_locations[str(i)]
            bus_stops_list[stop_name] = stop_gps

    for route_key, bus_stops in input_json.items():
        stop_ids = bus_stops["Stop ID"]
        bus_stop_names = bus_stops["Bus stop"]
        gps_locations = bus_stops["GPS Location"]

        for i in range(len(stop_ids) - 1):  # We can stop at the second to last stop since we are connecting to the next one
            stop_name = bus_stop_names[str(i)]
            stop_gps = gps_locations[str(i)]

            if stop_name not in output:
                output[stop_name] = {}

            adjacent_stops = output[stop_name]

            # Connect to the next bus stop in the current route
            next_stop_name = bus_stop_names[str(i + 1)]
            next_stop_gps = gps_locations[str(i + 1)]

            # Calculate the distance between the current and the next bus stops
            print("API CALL ROAD")
            distance = distance_between_coordinates_api(stop_gps, next_stop_gps)/1000

            # Calculate the weight based on bus travel
            weight = distance * 1000 / 20

            time = (distance / 17) * 60

            # Create a connection dictionary and add it to the adjacency list
            connection = {"Distance": distance, "Weight": round(weight, 1), "Bus Service": route_key, "Time": time}
            if next_stop_name not in adjacent_stops:
                adjacent_stops[next_stop_name] = [connection]
            else:
                adjacent_stops[next_stop_name].append(connection)

            # Add walking connections to bus stops within a 500m radius
            for walk_stop_name, walk_stop_gps in bus_stops_list.items():
                if walk_stop_name == stop_name:
                    continue  # Skip the current bus stop
                
                walk_distance = distance_between_coordinates(stop_gps, walk_stop_gps)
                if walk_distance <= 0.5:  # Limit to 500m
                    print("API CALL WALK")
                    walk_road_distance = distance_between_coordinates_api(stop_gps, walk_stop_gps)/1000
                    if walk_road_distance <= 0.5:
                        walk_weight = walk_road_distance * 1000 / 5  # Walking speed: 5 km/h
                        walk_time = (walk_road_distance / 4.4) * 60
                        walk_connection = {"Distance": walk_road_distance, "Weight": round(walk_weight, 1), "Bus Service": "Walking", "Time": walk_time}
                        existing_walk_connections = [conn for conn in adjacent_stops.get(walk_stop_name, []) if conn["Bus Service"] == "Walking"]
                        if not existing_walk_connections: #Check if there's existing connections to the same bus stop to avoid duplicate records
                            if walk_stop_name not in adjacent_stops:
                                adjacent_stops[walk_stop_name] = [walk_connection]
                            else:
                                adjacent_stops[walk_stop_name].append(walk_connection)

    return output

input_json = json.loads(open('bus_stops_cleaned.json').read())
output_json = generate_adjacent_stops(input_json)

with open("new_gpt_generated_graph_with_time.json", "w") as outfile:     
    json.dump(output_json, outfile, indent=4)

def KMPdoesItContain(busStopName, pattern): 
        busStopName = busStopName.upper()
        pattern = pattern.upper()
        if pattern == "":
            return False
        # Will only ever have the same amount of states in the LPS array = to the length of the pattern to look for
        lps = [0]*len(pattern) 
        prevLPS = 0
        i = 1
        while i < len(pattern):
            if pattern[i] == pattern[prevLPS]:
                lps[i] = prevLPS + 1
                prevLPS += 1
                i += 1
            elif prevLPS == 0:
                lps[i] = 0
                i += 1
            else:
                prevLPS = lps[prevLPS-1]
        # Everything above this is setting up the LPS, longest prefix suffix array which tells us which 'state' index to go to
        i = 0 # Pointer for text to search in
        j = 0 # Pointer for pattern
        while i < len(busStopName):
            if busStopName[i] == pattern[j]:
                i, j = i + 1, j+1 #iIf theres a match, increment both pointers
            else:
                if j == 0: # If first letter in pattern doesn't already match, go to the next letter of the busStopName, because j cannot be < 0
                    i += 1
                else:
                    j = lps[j-1]
            if j == len(pattern): # if j == length of the pattern to look for, it means that theres a string matching the busStopName of certain sections eg: 'Taman University' and pattern is 'Taman' (might have to toUpper() the inputs)
                indexOfOccurence = i - len(pattern) # Change the code to return this if you need, otherwise no need
                return True
        return False # Result not found