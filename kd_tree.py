from scipy.spatial import KDTree
import json
import pprint


bus_stops_to_coordinates = json.loads(open('bus_stops_to_coordinates.json').read())
bus_stop_names = list(bus_stops_to_coordinates.keys())
bus_stop_coords = []
for coordinates in bus_stops_to_coordinates.values():
    coordinates = coordinates.split(", ")
    coordinate = [float(coordinate) for coordinate in coordinates]
    bus_stop_coords.append(coordinate)

# pprint.pprint(bus_stop_coords)

bus_stop_tree = KDTree(bus_stop_coords)

def find_nearest_bus_stop(latitude, longitude):
    query_point = (latitude, longitude)
    distance, index = bus_stop_tree.query(query_point)
    nearest_bus_stop_name = bus_stop_names[index]
    return nearest_bus_stop_name

# starting_location = (1.50101, 103.74738)
# nearest_bus_stop, distance = find_nearest_bus_stop(*starting_location)
# print(f"The nearest bus stop is {nearest_bus_stop} at a distance of {distance}")