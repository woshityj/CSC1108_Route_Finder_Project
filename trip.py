import sys
import json
import pprint
import requests
from queue import Queue
from geopy.distance import geodesic

bing_api_key = "ArJeufHtfSV5H0hvAibUP1GoddcYG8uYVJ8y2fz-1Qe1c4IPl5QHp9aqoxBhlHxV"
url = "https://dev.virtualearth.net/REST/v1/Routes/DistanceMatrix?origins=1.5386151368910133,103.62871889454172&destinations=1.5423777121603113,103.62969894227055&travelMode=driving&key=ArJeufHtfSV5H0hvAibUP1GoddcYG8uYVJ8y2fz-1Qe1c4IPl5QHp9aqoxBhlHxV"

payload = {}
headers = {}
json_data = requests.get(url).json()
result = json_data['resourceSets'][0]['resources'][0]['results'][0]['travelDistance']
pprint.pprint(result)


# distance_in_km = geodesic((1.5386151368910133, 103.62871889454172), (1.5423777121603113, 103.62969894227055)).km

# start = sys.argv[1]
# end = sys.argv[2]

stop = {}

bus_routes = json.loads(open('bus_stops.json').read())
# for bus_service in bus_stops:
    
#     # stop = [bus_stops[bus_service]["GPS Location"]]
#     stop_desc_map = {stop["Bus Stop"] : stop[""] for stop in bus_stops}
# # stop_desc_map = {stop["Description"]: stop for stop in bus_stops}

routes_map = {}
for bus_service_index in bus_routes.keys():
    number_of_bus_stops = len(bus_routes[bus_service_index]["Bus stop"].keys())
    for i in range(number_of_bus_stops - 1):
        bus_stop = bus_routes[bus_service_index]["Bus stop"][str(i)]
        if bus_stop not in routes_map:
            routes_map[bus_stop] = []
        next_bus_stop = bus_routes[bus_service_index]["Bus stop"][str(i + 1)]
        if next_bus_stop not in routes_map[bus_stop]:
            routes_map[bus_stop] += [next_bus_stop]

service_routes_map = {}
for bus_service in bus_routes.keys():
    for bus_stop in bus_routes[bus_service]["Bus stop"].values():
        if bus_stop not in service_routes_map:
            service_routes_map[bus_stop] = []
        service_routes_map[bus_stop] += [bus_service]

def bfs(graph, start, end):
    seen = set()
    queue = Queue()
    queue.put([start])

    while queue:
        path = queue.get()
        node = path[-1]
        if node == end:
            return path
        if node in seen:
            continue
        seen.add(node)
        for adjacent in graph.get(node, []):
            new_path = list(path)
            new_path.append(adjacent)
            queue.put(new_path)

path = bfs(routes_map, "Hospital Sultanah Aminah", "Opp Jalan Cermai")
def find_service(i):
    bus_services = service_routes_map[path[i]]
    next_bus_services = service_routes_map[path[i + 1]]
    # print("\n")
    # print(bus_services)
    # print(path[i])
    # print("Next Bus")
    # print(next_bus_services)
    # print(path[i + 1])
    for j in range(len(bus_services)):
        if bus_services[j] in next_bus_services:
            return(bus_services[j], path[i], path[i + 1])
#     for j in range(len(service_routes_map[path[i]])):
#         if service_routes_map[path[i]][j] == service_routes_map[path[i + 1]][j]:
#             return service_routes_map[path[i]], path[i]

# find_service(0)

# for i in range(len(path) - 1):
#     print(find_service(i))
# print(len(path), "stops")

# for i in range(len(path) - 1):
#     pprint.pprint(find_service(i))


# pprint.pprint(bfs(routes_map, "Larkin Terminal", "Taman Universiti Terminal"))



# def distance(coordinate_1, coordinate_2):


