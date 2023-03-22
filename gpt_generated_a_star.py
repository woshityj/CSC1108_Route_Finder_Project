import heapq
from collections import defaultdict
import json
import pprint
import math

graph = json.loads(open('gpt_generated_graph.json').read())
bus_service_routes = json.loads(open('bus_service_routes_map.json').read())
bus_stops_coordinates = json.loads(open('bus_stops_to_coordinates.json').read())

def haversine(lat1, lon1, lat2, lon2):
    # Convert latitude and longitude from degrees to radians
    lat1 = math.radians(float(lat1))
    lon1 = math.radians(float(lon1))
    lat2 = math.radians(float(lat2))
    lon2 = math.radians(float(lon2))

    # Calculate differences
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    # Apply the Haversine formula
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Earth's radius in kilometers (approx.)
    R = 6371

    # Calculate the distance
    distance = R * c
    return distance

def euclidean_distance(start, end):
    start_coordinates = bus_stops_coordinates[start].split(", ")
    end_coordinates = bus_stops_coordinates[end].split(", ")
    distance = haversine(start_coordinates[0], start_coordinates[1], end_coordinates[0], end_coordinates[1])
    return distance


def heuristic(node, goal, current_bus_service):
    min_cost = float('inf')
    ## Euclidean Distance
    distance = euclidean_distance(node, goal)
    cost = distance
    for bus_service in bus_service_routes[node]:
        if current_bus_service is not "Walking" and bus_service != current_bus_service:
            penalty = 10
            cost += penalty
        min_cost = min(min_cost, cost)
    return min_cost

def a_star(graph, start, goal):
    open_set = []
    heapq.heappush(open_set, (0, start, [], None))

    closed_set = set()

    while open_set:
        _, current, path, current_bus_service = heapq.heappop(open_set)
        if current == goal:
            return path + [(current, current_bus_service)]

        if current not in closed_set:
            closed_set.add(current)
            for neighbor, edges in graph[current].items():
                for edge in edges:
                    g_cost = edge["Distance"]
                    h_cost = heuristic(neighbor, goal, edge["Bus Service"])
                    f_cost = g_cost + h_cost
                    new_path = path + [(current, current_bus_service)]
                    heapq.heappush(open_set, (f_cost, neighbor, new_path, edge["Bus Service"]))

    return None

# def get_bus_services(graph, bus_stop):
#     bus_services = []
#     for neighbor, edges in graph[bus_stop].items():
#         for edge in edges:
#             bus_services.append(edge['Bus Service'])
#     return bus_services

# def find_service(i, graph, path):
#     min_index = 0
#     bus_services = get_bus_services(graph, path[i])
#     next_bus_services = get_bus_services(graph, path[i + 1])
#     for j in range(len(bus_services)):
#         if bus_services[j] in next_bus_services:
#             return(bus_services[j], path[i], path[i + 1])

# def printRoute(graph, path):
#     for i in range(len(path) - 1):
#         print(find_service(i, graph, path))
#     print(len(path), "stops")

start = "Kulai Terminal"
goal = "Senai Airport Terminal"
path = a_star(graph, start, goal)
pprint.pprint(path)
print(len(path))

print("Path with bus services:")
for idx, (location, bus_service) in enumerate(path):
    if idx == 0:
        print(f"{location} (Start)")
    elif idx == len(path) - 1:
        print(f"{location} (Goal)")
    else:
        print(f"{location} (Bus Service: {bus_service})")