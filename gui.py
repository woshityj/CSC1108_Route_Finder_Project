import io
import folium
import sys
import json
import numpy as np
import pprint
import openrouteservice as ors
import osmnx as ox
import math

from PyQt6.QtGui import QColor, QPainter
from geopy.geocoders import Nominatim
import geopy.distance
from PyQt6 import QtWidgets, uic
from PyQt6.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QVBoxLayout, QWidget, QCompleter, QBoxLayout, \
    QPushButton, QTextBrowser
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import Qt

import gpt_generated_a_star

client = ors.Client(key = '5b3ce3597851110001cf62483b2035bb64ee4d0080a2aeb8bd28d07e')

class FloatingWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.directions = QTextBrowser(self)
        self.directions.setGeometry(50, 50, 200, 300)

        # Create a button to close the window
        #close_button = QPushButton('Close', self)
        #close_button.setGeometry(0,0,20,20)
        #close_button.clicked.connect(self.close)

        # Create a layout and add the widget to it
        layout = QVBoxLayout(self)
        #layout.addWidget(close_button)
        layout.addWidget(self.directions)
        # Set the window flags to make the window stay on top and not have a frame
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)


class MyApp(QWidget):
    def __init__(self):
        global bus_routes, bus_stops_to_coordinates
        bus_routes = json.loads(open('bus_stops_cleaned.json').read())
        bus_stops_to_coordinates = json.loads(open('bus_stops_to_coordinates.json').read())
        super().__init__()
        uic.loadUi('MainGUI.ui', self)

        self.map = QWebEngineView()

        bus_stops=json.loads(open('gpt_generated_graph.json').read()).keys()
        bus_stops = list(bus_stops)
        autocompleter = QCompleter(bus_stops)
        bus_services = self.getBusServices()
        for i in range(len(bus_services)):
            self.busServiceList.addItem(bus_services[i])

        self.fromTextField.setCompleter(autocompleter)
        self.toTextField.setCompleter(autocompleter)
        self.getBusRoute.clicked.connect(lambda: self.getBusServiceRoute(self.busServiceList.currentItem().text()))
        self.gridLayout1.addWidget(self.map, 0, 0, 0, 0)

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

        # try:
        geolocator = Nominatim(user_agent = 'MyApp')
        from_location = geolocator.geocode(from_location + " Malaysia")
        fromLat, fromLon = from_location.latitude, from_location.longitude
        to_location = geolocator.geocode(to_location + " Malaysia")
        toLat, toLon = to_location.latitude, to_location.longitude

        folium_map = folium.Map(location = [fromLat, fromLon], tiles = 'cartodbpositron', zoom_start = 14)
        start_marker = folium.Marker([fromLat, fromLon]).add_to(folium_map)
        popup_html = """
                                <div>
                                    <h3>Marker clicked</h3>
                                    <p>Hello, world!</p>
                                </div>
                                """
        popup = folium.Popup(html=popup_html, max_width=200)
        start_marker.add_child(popup)
        start_marker.add_to(folium_map)
        end_marker = folium.Marker([toLat, toLon]).add_to(folium_map)
        popup_html = """
                                       <div>
                                           <h3>Marker clicked</h3>
                                           <p>Hello, world!</p>
                                       </div>
                                       """
        popup = folium.Popup(html=popup_html, max_width=200)
        end_marker.add_child(popup)
        end_marker.add_to(folium_map)


        # Gets the nearest bus stop from the starting point and ending point of where the user indicated
        startingBusStop = self.getNearestBusStopFromUser(fromLat, fromLon)
        endingBusStop = self.getNearestBusStopFromUser(toLat, toLon)
        path = self.getUserRoute(startingBusStop, endingBusStop)
        direction_text = ""
        for idx, (location, bus_service, time) in enumerate(path):
            if idx == 0:
                direction_text += f"{location} (Start)\n\n"
            elif idx == len(path) - 1:
                direction_text += f"{location} (Goal)"
            else:
                direction_text += f"{location} \n(Bus Service: {bus_service})\n\n"

        floatingWindow.directions.setText(direction_text)
        floatingWindow.show()

        coordinates = []
        for id, (bus_stop, bus_service, time) in enumerate(path):
            coordinate = self.getCoordinates(bus_stop)
            coordinates.append(coordinate)
        print(coordinates)

        # coordinates = []
        # for i in range(len(path)):
        #     bus_stop = path[i]
        #     coordinate = self.getCoordinates(bus_stop)
        #     coordinates.append(coordinate)
        # print(coordinates)

        for i in range(len(coordinates)):
            marker = folium.Marker([coordinates[i][0], coordinates[i][1]]).add_to(folium_map)
            popup_html = """
                        <div>
                            <h3>Marker clicked</h3>
                            <p>Hello, world!</p>
                        </div>
                        """
            popup = folium.Popup(html=popup_html, max_width=200)
            marker.add_child(popup)
            marker.add_to(folium_map)
        
        # Add the User's start position and end position to the front and end of the list respectively
        coordinates.insert(0, [fromLat, fromLon])
        coordinates.insert(len(coordinates), [toLat, toLon])
        
        folium.PolyLine(locations = [list(coords) for coords in coordinates], weight = 3, color = 'blue').add_to(folium_map)


        data = io.BytesIO()
        folium_map.save(data, close_file = False)
        self.map.setHtml(data.getvalue().decode())
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)


        # except:
        #     print("No such location")
    
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

        graph = json.loads(open('test_graph.json').read())
        path = gpt_generated_a_star.a_star(graph, start_bus_stop, end_bus_stop, 0)
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
            marker = folium.Marker([coordinates[i][0], coordinates[i][1]])
            popup_html = """
            <div>
                <h3>Marker clicked</h3>
                <p>Hello, world!</p>
            </div>
            """
            popup = folium.Popup(html=popup_html,max_width=200)
            marker.add_child(popup)
            marker.add_to(folium_map)
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
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    
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

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor('white'))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    myApp = MyApp()
    myApp.setWindowTitle("Bas Muafakat Johor")
    myApp.show()

    floatingWindow = FloatingWindow()
    floatingWindow.setGeometry(100, 100, 300, 200)
    floatingWindow.setWindowTitle("Directions")

    try:
        sys.exit(app.exec())
    except SystemExit:
        print('Closing Window')