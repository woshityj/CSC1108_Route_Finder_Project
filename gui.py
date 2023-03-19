import io
import folium
import sys
import json
import numpy as np
import pprint
import openrouteservice as ors
import osmnx as ox
import networkx as nx
import math
from geopy.geocoders import Nominatim
import geopy.distance
from PyQt6 import QtWidgets, uic
from PyQt6.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QVBoxLayout, QWidget
from PyQt6.QtWebEngineWidgets import QWebEngineView

import trip

client = ors.Client(key = '5b3ce3597851110001cf62483b2035bb64ee4d0080a2aeb8bd28d07e')


class MyApp(QWidget):
    def __init__(self):
        global bus_routes, bus_stops_to_coordinates
        bus_routes = json.loads(open('bus_stops_cleaned.json').read())
        bus_stops_to_coordinates = json.loads(open('bus_stops_to_coordinates.json').read())
        super().__init__()
        uic.loadUi('MainGUI.ui', self)

        self.map = QWebEngineView()

        bus_services = self.getBusServices()
        for i in range(len(bus_services)):
            self.busServiceList.addItem(bus_services[i])


        self.getBusRoute.clicked.connect(lambda: self.getBusServiceRoute(self.busServiceList.currentItem().text()))
        self.gridLayout.addWidget(self.map, 0, 0, 0, 0)

        self.getRouteButton.clicked.connect(lambda: self.getRoute(self.fromTextField.text(), self.toTextField.text()))

        self.show()


    def getRoute(self, from_location, to_location):
        """Plots out the route the user should take on the User Interface

        Parameters
        ----------
        from_location : str
            The name of the starting location that the user has entered via the User Interface
        to_location: str
            The name of the ending location that the user has entered via the User Interface
        """

        try:
            geolocator = Nominatim(user_agent = 'MyApp')
            from_location = geolocator.geocode(from_location + " Malaysia")
            fromLat, fromLon = from_location.latitude, from_location.longitude
            to_location = geolocator.geocode(to_location + " Malaysia")
            toLat, toLon = to_location.latitude, to_location.longitude

            folium_map = folium.Map(location = [fromLat, fromLon], tiles = 'cartodbpositron', zoom_start = 14)
            folium.Marker([fromLat, fromLon]).add_to(folium_map)
            folium.Marker([toLat, toLon]).add_to(folium_map)

            # Gets the nearest bus stop from the starting point and ending point of where the user indicated
            startingBusStop = self.getNearestBusStopFromUser(fromLat, fromLon)
            endingBusStop = self.getNearestBusStopFromUser(toLat, toLon)
            path = self.getUserRoute(startingBusStop, endingBusStop)
            
            coordinates = []
            for i in range(len(path)):
                bus_stop = path[i]
                coordinate = self.getCoordinates(bus_stop)
                coordinates.append(coordinate)
            print(coordinates)

            for i in range(len(coordinates)):
                folium.Marker([coordinates[i][0], coordinates[i][1]]).add_to(folium_map)
            
            # Add the User's start position and end position to the front and end of the list respectively
            coordinates.insert(0, [fromLat, fromLon])
            coordinates.insert(len(coordinates), [toLat, toLon])
            
            folium.PolyLine(locations = [list(coords) for coords in coordinates], weight = 3, color = 'blue').add_to(folium_map)


            data = io.BytesIO()
            folium_map.save(data, close_file = False)
            self.map.setHtml(data.getvalue().decode())
        except:
            print("No such location")
    
    #Function to find the nearest bus stop based on the ending position of the user
    def getNearestBusStopFromUser(self, location_lat, location_lon):
        """Get the nearest Bus Stop based on the start/end position of the user

        Parameters
        ----------
        location_lat : float
            The lat of the user's position
        location_lon : float
            The lon of the user's position

        Returns
        -------
        string
            The name of the closest Bus Stop from the start/end position of the User
        """

        bus_stop = None
        min_distance = math.inf
        for bus_service in bus_routes.keys():
            number_of_bus_stops = len(bus_routes[bus_service]["Bus stop"].keys())
            for i in range(number_of_bus_stops):
                bus_stop_coordinates = bus_routes[bus_service]["GPS Location"][str(i)]
                bus_stop_coordinates = bus_stop_coordinates.split(", ")
                distance_from_user_to_bus_stop = geopy.distance.distance((location_lat, location_lon), bus_stop_coordinates).kilometers
                if min_distance > distance_from_user_to_bus_stop:
                    min_distance = distance_from_user_to_bus_stop
                    bus_stop = bus_routes[bus_service]["Bus stop"][str(i)]
        
        return bus_stop
    
    def getUserRoute(self, start_bus_stop, end_bus_stop):
        """Makes use of Dijkstra's Algorithm to return a list of Bus Stops the user should travel in
           sequential order to reach his destination
           
        Parameters
        ----------
        start_bus_stop : str
            The name of the starting Bus Stop
        end_bus_stop : str
            The name of the ending Bus Stop

        Returns
        -------
        list
            A list of the names of Bus Stops the user should travel via to reach to his destination
        """

        graph = json.loads(open('graph_with_distance_cleaned.json').read())
        path = trip.dijkstra(graph, start_bus_stop, end_bus_stop)
        return path

    def getCoordinates(self, bus_stop):
        """Get the coordinate of a specified Bus Stop

        Parameters
        ----------
        bus_stop : str
            The name of the Bus Stop

        Returns
        -------
        list
            Contains the lat and lon of a specific Bus Stop
        """

        coordinate = bus_stops_to_coordinates[bus_stop]
        coordinate = coordinate.split(", ")
        coordinate = [float(coord) for coord in coordinate]
        return coordinate

    def getBusServiceRoute(self, bus_service): 
        """Plots out the route of the specified Bus Service onto a Map for the User Interface

        Parameters
        ----------
        bus_service : str
            The name of the Bus Service

        Returns
        -------
        list
            A list of coordinates based on the route of a Bus Service
        """

        coordinates = self.getBusRouteCoordinates(bus_service)
        reversed_coordinates = []
        for i in range(len(coordinates)):
            reversed_coordinates.append([coordinates[i][1], coordinates[i][0]])
        folium_map = folium.Map(location = coordinates[0], tiles = 'cartodbpositron', zoom_start = 14)
        for i in range(len(coordinates)):
            folium.Marker([coordinates[i][0], coordinates[i][1]]).add_to(folium_map)

        ## Code for plotting route according to road but its laggy ;c 
        # G = ox.graph_from_point(coordinates[0], dist = 90000, network_type = 'drive')

        # orig_node = ox.nearest_nodes(G, coordinates[0][1], coordinates[0][0])
        # dest_node = ox.nearest_nodes(G, coordinates[5][1], coordinates[5][0])
        # route = nx.shortest_path(G, orig_node, dest_node)
        # ox.plot_route_folium(G, route, folium_map)
        folium.PolyLine(locations = [list(coords) for coords in coordinates], weight = 3, color = 'blue').add_to(folium_map)

        data = io.BytesIO()
        folium_map.save(data, close_file = False)
        self.map.setHtml(data.getvalue().decode())

    
    def getBusServices(self):
        """Get a list of Bus Services available

        Returns
        -------
        list
            A list of bus services available
        """

        bus_services = list(bus_routes.keys())
        return bus_services

    def getBusRouteCoordinates(self, bus_service):
        """Get a list of Coordinates based on the route of a Bus Service

        Parameters
        ----------
        bus_service : str
            The name of the Bus Service

        Returns
        -------
        list
            A list of coordinates based on the route of a Bus Service
        """

        coordinates = []
        bus_routes = json.loads(open('bus_stops_cleaned.json').read())
        number_of_bus_stops = len(bus_routes[bus_service]["Bus stop"].keys())
        for i in range(number_of_bus_stops):
            current_stop_coords = bus_routes[bus_service]['GPS Location'][str(i)]
            current_stop_coords = current_stop_coords.split(", ")
            current_stop_coords = [float(coord) for coord in current_stop_coords]
            coordinates.append(current_stop_coords)
        return coordinates

if __name__ == '__main__':
    app = QApplication(sys.argv)

    myApp = MyApp()
    myApp.show()

    try:
        sys.exit(app.exec())
    except SystemExit:
        print('Closing Window')