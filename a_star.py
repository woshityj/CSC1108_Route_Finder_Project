import heapq
from collections import defaultdict
import json
import pprint
import math

from datetime import datetime, timedelta
import datetime

graph = json.loads(open('test.json').read())
bus_service_routes = json.loads(open('bus_service_routes_map.json').read())
bus_stops_coordinates = json.loads(open('bus_stops_to_coordinates.json').read())

global bus_speed, walk_speed
bus_speed = 17 # km/h
walk_speed = 4.4 #km/h

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

def heuristic(node, goal, current_bus_service, current_time):
    min_cost = float('inf')
    ## Euclidean Distance
    distance = euclidean_distance(node, goal)
    cost = distance

    for bus_service in bus_service_routes[node]:
        if current_bus_service is not None and bus_service != current_bus_service:
            penalty = 10
            cost += penalty

        time_cost = get_time_cost(distance, bus_service)
        time_cost += current_time
        if bus_service == "Walking":
            print("Yes")
        min_cost = min(min_cost, cost + time_cost)
    return min_cost

def get_time_cost(distance, bus_service):
    if bus_service == "Walking":
        speed = walk_speed
    else:
        speed = bus_speed
    time_cost = distance / speed
    if bus_service == "Walking":
        print(time_cost)
    return time_cost

def a_star(graph, start, goal, start_time, option = "least transfer"):
    open_set = [(0, start, [], None, start_time)]

    closed_set = set()
    traffic_light_penalty = 2
    traffic_light_time = 1.5
    if option == "least transfer":
        while open_set:
            open_set.sort(key=lambda x: x[0])
            _, current, path, current_bus_service, current_time = open_set.pop(0)
            if current == goal:
                return path + [(current, current_bus_service, current_time, [])]

            if current not in closed_set:
                closed_set.add(current)
                for neighbor, edges in graph[current].items():
                    for edge in edges:
                        g_cost = edge["Distance"] + (edge["Traffic Lights Count"]if "Traffic Lights Count" in edge else 0) * traffic_light_penalty
                        h_cost = heuristic(neighbor, goal, edge["Bus Service"], current_time)
                        f_cost = g_cost + h_cost
                        new_path = path + [(current, current_bus_service, current_time, edge["Road Route"] if "Road Route" in edge else [])]
                        bus_change_penalty = 10 if current_bus_service is not None and current_bus_service != edge["Bus Service"] and current_bus_service != "Walking" else 0
                        new_time = current_time + edge["Time"] + bus_change_penalty + (edge["Traffic Lights Count"] if "Traffic Lights Count" in edge else 0) * traffic_light_time
                        open_set.append((f_cost, neighbor, new_path, edge["Bus Service"], new_time))
    
    if option == "fastest":
        pass

    if option == "least walking":
        pass

    return None


start = "Kulai Terminal"
goal = "Senai Airport Terminal"
path = a_star(graph, start, goal, 0)
pprint.pprint(path)
print(len(path))

print("Path with bus services:")
for idx, (location, bus_service, time, route) in enumerate(path):
    if idx == 0:
        print(f"{location} {path[idx + 1][1]}(Start)")
        break
    elif idx == len(path) - 1:
        print(f"{location} (Goal)")
    else:
        print(f"{location} (Bus Service: {bus_service})")

# def a_star(graph, start, goal):
#     open_set = []
#     heapq.heappush(open_set, (0, start, [], None))

#     closed_set = set()

#     while open_set:
#         _, current, path, current_bus_service = heapq.heappop(open_set)
#         if current == goal:
#             return path + [(current, current_bus_service)]

#         if current not in closed_set:
#             closed_set.add(current)
#             for neighbor, edges in graph[current].items():
#                 for edge in edges:
#                     g_cost = edge["Distance"]
#                     h_cost = heuristic(neighbor, goal, edge["Bus Service"])
#                     f_cost = g_cost + h_cost
#                     new_path = path + [(current, current_bus_service)]
#                     heapq.heappush(open_set, (f_cost, neighbor, new_path, edge["Bus Service"]))

#     return None

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

