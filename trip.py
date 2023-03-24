import sys
import json
import pprint
import requests
from queue import Queue
import openrouteservice as ors
import math

# stop = {}
bus_routes = json.loads(open('bus_stops.json').read())

# Maps out a dictionary which consists of the list of Bus Stops that are adjacent to the current Bus Stop
def generateGraph(bus_routes):
    """Generate a Dictionary which consists of a list of Bus Stops that are adjacent to the specified Bus Stop.
       This Dictionary is used for the breadth first search algorithm.

    Parameters
    ----------
    bus_routes : dict
        A Dictionary version of the bus_stops.xlsx file generated from bus_stops.py

    Returns
    -------
    dictionary
        A list of Bus Stops that are adjacent to the specified Bus Stop
    """

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
    """Get the road distance between the starting Bus Stop and the ending Bus Stop.
       The road distance is calculated via the OpenRouteService API.

    Parameters
    ----------
    start_lat : float
        The lat of the starting position
    start_lon : float
        The lon of the starting position
    end_lat : float
        The lat of the ending position
    end_lon : float
        The lon of the ending position

    Returns
    -------
    float
        The road distance between the starting Bus Stop and its ending adjacent Bus Stop
    """

    client = ors.Client(key = '5b3ce3597851110001cf62483b2035bb64ee4d0080a2aeb8bd28d07e')
    coords = [[start_lon, start_lat], [end_lon, end_lat]]
    route = client.directions(coords, profile = 'driving-car', format = 'geojson')
    distance = route['features'][0]['properties']['segments'][0]['distance']
    return distance

def generateGraphWithDistance(bus_routes):
    """Generate a Dictionary which consists of a list of Bus Stops that are adjacent to the specified Bus Stop with its distance
       This Dictionary is used for Dijkstra's Algorithm

    Parameters
    ----------
    bus_routes : dict
        A Dictionary version of the bus_stops.xlsx file generated from bus_stops.py

    Returns
    -------
    dictionary
        A list of Bus Stops that are adjacent to the specified Bus Stop with the distance between them
    """

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
            if graph[bus_stop].get(next_bus_stop) is None:
                graph[bus_stop][next_bus_stop] = {"Distance": distance, "Bus Service": [bus_service_index]}
            else:
                graph[bus_stop][next_bus_stop]["Bus Service"].append(bus_service_index)
    return graph

# bus_routes = json.loads(open('bus_stops_cleaned.json').read())
# graph = generateGraphWithDistance(bus_routes)
# graph_json = json.dumps(graph, indent = 4)
# with open("graph.json", "w") as outfile:
#     outfile.write(graph_json)

## Commands to generate a json file with distance to adjacent bus stops
# graph_with_distance_json = json.dumps(generateGraphWithDistance(bus_routes), indent = 4)
# with open("graph_with_distance_and_transfer_cleaned.json", "w") as outfile:
#     outfile.write(graph_with_distance_json)

# Maps out a dictionary which consists of the list of Bus Services which the Bus Stop has
# E.g. 'aft Lorong Betik': ['P211-01', 'P411-01']
def generateBusStopstoBusServices(bus_routes):
    """Generate a Dictionary which consists of a list of Bus Services that can reach a specified Bus Stop
       This Dictionary is used to map out the Bus Service the User should take to travel from starting Bus Stop to the ending
       Bus Stop

    Parameters
    ----------
    bus_routes : dict
        A Dictionary version of the bus_stops.xlsx file generated from bus_stops.py

    Returns
    -------
    dictionary
        A list of Bus Services that stops at a specified Bus Stop
        Example:
        aft Lorong Betik': ['P211-01', 'P411-01']
    """

    service_routes_map = {}
    for bus_service in bus_routes.keys():
        for bus_stop in bus_routes[bus_service]["Bus stop"].values():
            if bus_stop not in service_routes_map:
                service_routes_map[bus_stop] = []
            if bus_service not in service_routes_map[bus_stop]:
                service_routes_map[bus_stop] += [bus_service]
    return service_routes_map


# bus_stops = generateBusStopstoBusServices(bus_routes)
# bus_stop_json = json.dumps(bus_stops, indent = 8)
# with open('bus_service_routes_map.json', 'w') as outfile:
#     outfile.write(bus_stop_json)

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
# path = dijkstra(graph, "Kulai Terminal", "Senai Airport Terminal")
# pprint.pprint(path)
# print(len(path))
# printRoute(generateBusStopstoBusServices(), path)