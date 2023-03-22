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
    # Example: Use the shortest distance as heuristic
    min_cost = float('inf')
    for edge in bus_service_routes[goal]:
        cost = euclidean_distance(node, goal)
        if current_bus_service is not None and edge != current_bus_service:
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
            return path + [current]

        if current not in closed_set:
            closed_set.add(current)
            for neighbor, edges in graph[current].items():
                for edge in edges:
                    g_cost = edge["Weight"]
                    h_cost = heuristic(neighbor, goal, edge["Bus Service"])
                    f_cost = g_cost + h_cost
                    heapq.heappush(open_set, (f_cost, neighbor, path + [current], edge["Bus Service"]))

    return None

start = "Kulai Terminal"
goal = "Senai Airport Terminal"
result = a_star(graph, start, goal)
pprint.pprint(result)