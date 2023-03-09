import sys
import json
import pprint
import requests
from queue import Queue
import openrouteservice as ors
import math

# stop = {}
# bus_routes = json.loads(open('bus_stops.json').read())

bus_routes = json.loads(open('bus_stops_cleaned.json').read())

# Maps out a dictionary which consists of the list of Bus Stops that are adjacent to the current Bus Stop
def generateGraph(bus_routes):
    graph = {}
    for bus_service_index in bus_routes.keys():
        number_of_bus_stops = len(bus_routes[bus_service_index]["Bus stop"].keys())
        for i in range(number_of_bus_stops - 1):
            bus_stop = bus_routes[bus_service_index]["Bus stop"][str(i)]
            if bus_stop not in graph:
                graph[bus_stop] = []
            next_bus_stop = bus_routes[bus_service_index]["Bus stop"][str(i + 1)]
            if next_bus_stop not in graph[bus_stop]:
                graph[bus_stop] += [next_bus_stop]
    return graph

def calculateDistance(start_lat, start_lon, end_lat, end_lon):
    client = ors.Client(key = '5b3ce3597851110001cf62483b2035bb64ee4d0080a2aeb8bd28d07e')
    coords = [[start_lon, start_lat], [end_lon, end_lat]]
    route = client.directions(coords, profile = 'driving-car', format = 'geojson')
    distance = route['features'][0]['properties']['segments'][0]['distance']
    return distance

def generateGraphWithDistance(bus_routes):
    graph = {}
    for bus_service_index in bus_routes.keys():
        number_of_bus_stops = len(bus_routes[bus_service_index]['Bus stop'].keys())
        for i in range(number_of_bus_stops - 1):
            bus_stop = bus_routes[bus_service_index]['Bus stop'][str(i)]
            current_stop_coords = bus_routes[bus_service_index]["GPS Location"][str(i)]
            next_stop_coords = bus_routes[bus_service_index]["GPS Location"][str(i + 1)]
            if 'ignore' in current_stop_coords or 'ignore' in next_stop_coords:
                continue
            current_stop_coords = current_stop_coords.split(", ")
            next_stop_coords = next_stop_coords.split(", ")
            next_bus_stop = bus_routes[bus_service_index]["Bus stop"][str(i + 1)]
            distance = calculateDistance(current_stop_coords[0], current_stop_coords[1], next_stop_coords[0], next_stop_coords[1])
            if bus_stop not in graph:
                graph[bus_stop] = {}
            graph[bus_stop][next_bus_stop] = {"Distance": distance}, {"Bus Service": bus_service_index}
    return graph


## Commands to generate a json file with distance to adjacent bus stops
graph_with_distance_json = json.dumps(generateGraphWithDistance(bus_routes), indent = 4)
with open("graph_with_distance_and_transfer_cleaned.json", "w") as outfile:
    outfile.write(graph_with_distance_json)

# Maps out a dictionary which consists of the list of Bus Services which the Bus Stop has
# E.g. 'aft Lorong Betik': ['P211-01', 'P411-01']
def generateBusStopstoBusServices():
    service_routes_map = {}
    for bus_service in bus_routes.keys():
        for bus_stop in bus_routes[bus_service]["Bus stop"].values():
            if bus_stop not in service_routes_map:
                service_routes_map[bus_stop] = []
            service_routes_map[bus_stop] += [bus_service]
    return service_routes_map

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

## Reference Page:
## https://algodaily.com/lessons/an-illustrated-guide-to-dijkstras-algorithm/python
def dijkstra(graph, start_node, end_node):
    unvisited_nodes = graph

    shortest_path = {}
    route = []
    path_nodes = {}

    for node in unvisited_nodes:
        shortest_path[node] = math.inf

    shortest_path[start_node] = 0

    while unvisited_nodes:
        min_node = None
        for current_node in unvisited_nodes:
            if min_node is None:
                min_node = current_node
            elif shortest_path[min_node] > shortest_path[current_node]:
                min_node = current_node

        for node, distance in unvisited_nodes[min_node].items():
            if distance + shortest_path[min_node] < shortest_path[node]:
                shortest_path[node] = distance + shortest_path[min_node]
                path_nodes[node] = min_node
        unvisited_nodes.pop(min_node)
    
    pprint.pprint(shortest_path)

    node = end_node
    while node != start_node:
        try:
            route.insert(0, node)
            node = path_nodes[node]
        except Exception:
            print('Path not reachable')
            break
    route.insert(0, start_node)
    return route
    # return route, shortest_path[end_node]


def find_service(i, service_routes_map, path):
    bus_services = service_routes_map[path[i]]
    next_bus_services = service_routes_map[path[i + 1]]
    for j in range(len(bus_services)):
        if bus_services[j] in next_bus_services:
            return(bus_services[j], path[i], path[i + 1])

def printRoute(service_routes_map, path):
    for i in range(len(path) - 1):
        print(find_service(i, service_routes_map, path))
    print(len(path), "stops")

# path = bfs(generateGraph, "Hospital Sultanah Aminah", "Opp Jalan Cermai")
# pprint.pprint(generateGraph())

# graph = json.loads(open('graph_with_distance_cleaned.json').read())
# path = dijkstra(graph, "Hospital Sultanah Aminah", "Opp Jalan Cermai")
# printRoute(generateBusStopstoBusServices(), path)