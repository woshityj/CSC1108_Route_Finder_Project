import sys
import json
import pprint
import requests
from queue import Queue
import openrouteservice as ors
import math

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

bus_routes = json.loads(open('bus_stops_cleaned.json').read())
graph = generateGraphWithDistance(bus_routes)
graph_json = json.dumps(graph, indent = 4)
with open("graph.json", "w") as outfile:
    outfile.write(graph_json)