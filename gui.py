import io
import folium
import sys
import json
import numpy as np
import pprint
import openrouteservice as ors
import osmnx as ox
import math
import branca

from PyQt6.QtGui import QColor, QPainter
from geopy.geocoders import Nominatim
import geopy.distance
from PyQt6 import QtWidgets, uic
from PyQt6.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QVBoxLayout, QWidget, QCompleter, QBoxLayout, \
    QPushButton, QTextBrowser, QLabel, QTextEdit, QLineEdit, QListWidget, QListWidgetItem
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import Qt

import a_star
import kd_tree

client = ors.Client(key = '5b3ce3597851110001cf62483b2035bb64ee4d0080a2aeb8bd28d07e')
global walking_speed

walking_speed = 4.4 #km/h

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
        global bus_routes, bus_stops_to_coordinates, graph
        bus_routes = json.loads(open('bus_stops_cleaned.json').read())
        bus_stops_to_coordinates = json.loads(open('bus_stops_to_coordinates.json').read())
        graph = json.loads(open('test_revised.json').read())


        super().__init__()
        uic.loadUi('MainGUI.ui', self)

        self.map = QWebEngineView()
        self.map2 = QWebEngineView()
        self.map3 = QWebEngineView()

        bus_stops=json.loads(open('graph.json').read()).keys()
        bus_stops = list(bus_stops)
        autocompleter = QCompleter(bus_stops)
        bus_services = self.getBusServices()
        for i in range(len(bus_services)):
            self.busServiceList.addItem(bus_services[i])

        self.fromTextField.setCompleter(autocompleter)
        self.toTextField.setCompleter(autocompleter)
        self.getBusRoute.clicked.connect(lambda: self.getBusServiceRoute(self.busServiceList.currentItem().text()))
        self.gridLayout1.addWidget(self.map, 0, 0, 0, 0)
        self.gridLayout2.addWidget(self.map2, 0, 0, 0, 0)
        self.gridLayout3.addWidget(self.map3, 0, 0, 0, 0)
        self.getRouteButton.clicked.connect(lambda: self.getRoute(self.fromTextField.text(), self.toTextField.text(), self.mapTabWidget.currentIndex()))

        m = folium.Map(location=[1.49523932121696,103.743347921416], tiles = 'cartodbpositron', zoom_start=13)

        data = io.BytesIO()
        m.save(data, close_file = False)
        self.show()
        self.map.setHtml(data.getvalue().decode())


    def checkIfUserInputIsBusStop(self, input):
        if input in bus_stops_to_coordinates:
            return True
        else:
            return False
    
    def getWalkingPathToBusStop(self, from_location, to_location):
        lat1 = from_location[0]
        lon1 = from_location[1]

        lat2 = to_location[0]
        lon2 = to_location[1]
        client = ors.Client(key = '5b3ce3597851110001cf6248bf0ad84e6c5043fe86802711166fdf40')
        coords = [[lon1, lat1], [lon2, lat2]]
        route = client.directions(coords, profile = 'foot-walking', format = 'geojson')
        distance = route["features"][0]["properties"]["segments"][0]["distance"]
        distance = distance / 1000
        route = route["features"][0]["geometry"]["coordinates"]
        for i in range(len(route)):
            route[i].reverse()
        return route, distance

    def getRoute(self, from_location, to_location, current_index):
        """Plots out the route the user should take on the User Interface

        Parameters
        ----------
        from_location : str
            The name of the starting location that the user has entered via the User Interface
        to_location: str
            The name of the ending location that the user has entered via the User Interface
        """
        if from_location == '' or to_location == '':
            raise Exception("No location is inserted")
        
        print(current_index)
        # try:
        direction_text = ""
        total_time = 0
        coordinates = None
        pprint.pprint(coordinates)
        geolocator = Nominatim(user_agent = 'MyApp')
        if self.checkIfUserInputIsBusStop(from_location):
            from_coordinates = self.getBusCoordinates(from_location)
            fromLat = from_coordinates[0]
            fromLon = from_coordinates[1]
            startingBusStop = from_location
        else:
            from_location = geolocator.geocode(from_location + " Malaysia")
            fromLat, fromLon = from_location.latitude, from_location.longitude
            # Gets the nearest bus stop from the starting point and ending point of where the user indicated
            startingBusStop, distance = kd_tree.find_nearest_bus_stop(fromLat, fromLon)
            start_walk_time = round((distance / walking_speed) * 60, 2)
            total_time += start_walk_time
            direction_text += f"Walk {distance}km to Nearest Bus Stop {startingBusStop} \n({start_walk_time} minutes)\n\n"
        if self.checkIfUserInputIsBusStop(to_location):
            to_coordinates = self.getBusCoordinates(to_location)
            toLat = to_coordinates[0]
            toLon = to_coordinates[1]
            endingBusStop = to_location
        else:
            to_location = geolocator.geocode(to_location + " Malaysia")
            toLat, toLon = to_location.latitude, to_location.longitude
            endingBusStop, end_distance_from_destination = kd_tree.find_nearest_bus_stop(toLat, toLon)
            end_walk_time = round((end_distance_from_destination / walking_speed) * 60, 2)
            total_time += end_walk_time

        folium_map = folium.Map(location = [fromLat, fromLon], tiles = 'cartodbpositron', zoom_start = 14)
        if self.checkIfUserInputIsBusStop(str(from_location)) == False:
            start_marker = folium.Marker([fromLat, fromLon]).add_to(folium_map)
            popup_html = f"""
                                    <div>
                                        <h3>Walk</h3>
                                        <p>{from_location}</p>
                                    </div>
                                    """
            popup = folium.Popup(html=popup_html, max_width=200)
            start_marker.add_child(popup)
            start_marker.add_to(folium_map)
        
        if self.checkIfUserInputIsBusStop(str(to_location)) == False:
            end_marker = folium.Marker([toLat, toLon]).add_to(folium_map)
            popup_html = f"""
                                        <div>
                                            <h3>Walk</h3>
                                            <p>{to_location}</p>
                                        </div>
                                        """
            popup = folium.Popup(html=popup_html, max_width=200)
            end_marker.add_child(popup)
            end_marker.add_to(folium_map)


        path = self.getUserRoute(startingBusStop, endingBusStop, current_index)
        coordinates = []
        # try:
        for idx, (location, bus_service, time, route) in enumerate(path):
            if idx == 0:
                direction_text += f"{location} {path[idx + 1][1]} (Start)\n\n"
            elif idx == len(path) - 1:
                direction_text += f"{location} {path[idx - 1][1]} (Estimated Arrival Time: {round(time, 2)}) (Goal) \n\n"
                total_time = time
            else:
                direction_text += f"{location} \n(Bus Service: {bus_service})\n(Estimated Arrival Time: {round(time, 2)} minutes)\n\n"

            coordinates += route
            bus_stop_coordinate = self.getBusCoordinates(location)
            marker = folium.Marker([bus_stop_coordinate[0], bus_stop_coordinate[1]]).add_to(folium_map)
            popup_html = f"""
                        <div>
                            <h3>{bus_service}</h3>
                            <p>{location}</p>
                        </div>
                        """
            popup = folium.Popup(html=popup_html, max_width=200)
            marker.add_child(popup)
            marker.add_to(folium_map)
        # except:
        #     print("Error Getting Path from Algorithm")
        #     marker = folium.Marker([fromLat, fromLon]).add_to(folium_map)


        # coordinates = []
        # for id, (bus_stop, bus_service, time) in enumerate(path):
        #     coordinate = self.getBusCoordinates(bus_stop)
        #     coordinates.append(coordinate)
        # print(coordinates)
        
        # Add the User's start position and end position to the front and end of the list respectively
        if self.checkIfUserInputIsBusStop(str(from_location)) == False:
            starting_bus_stop_coordinates = self.getBusCoordinates(startingBusStop)
            walking_route_coordinates, walking_distance = self.getWalkingPathToBusStop([fromLat, fromLon], starting_bus_stop_coordinates)
            direction_text = direction_text + f"Walk to the nearest bus stop {startingBusStop} Distance: {walking_distance} ({round((walking_distance / walking_speed) * 60, 2)})"
            for i in range(len(walking_route_coordinates)):
                coordinates.insert(0 + i, [walking_route_coordinates[i][0], walking_route_coordinates[i][1]])
        
        if self.checkIfUserInputIsBusStop(str(to_location)) == False:
            ending_bus_stop_coordinates = self.getBusCoordinates(endingBusStop)
            walking_route_coordinates, walking_distance = self.getWalkingPathToBusStop([toLat, toLon], ending_bus_stop_coordinates)
            direction_text += f"Walk to your destination {to_location} Distance: {walking_distance} ({round((walking_distance / walking_speed) * 60, 2)})"
            pprint.pprint(walking_route_coordinates)
            coordinates += walking_route_coordinates
            # for i in range(len(walking_route_coordinates)):
            #     coordinates.insert((len(coordinates) - 1) + i, [walking_route_coordinates[i][1], walking_route_coordinates[i][0]])

        direction_text = f"Total estimated travel time: {round(total_time, 2)} minutes\n\n" + direction_text
        floatingWindow.directions.setText(direction_text)
        floatingWindow.show()
        folium.PolyLine(locations = [[coords[1], coords[0]] for coords in coordinates], weight = 3, color = 'blue').add_to(folium_map)


        data = io.BytesIO()
        folium_map.save(data, close_file = False)
        if current_index == 0:
            self.map.setHtml(data.getvalue().decode())
        elif current_index == 1:
            self.map2.setHtml(data.getvalue().decode())
        elif current_index == 2:
            self.map3.setHtml(data.getvalue().decode())
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
    
    def getUserRoute(self, start_bus_stop, end_bus_stop, option):
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
        if option == 0:
            path = a_star.a_star(graph, start_bus_stop, end_bus_stop, 0, "least transfer")
        elif option == 1:
            path = a_star.a_star(graph, start_bus_stop, end_bus_stop, 0, "shortest distance")
        elif option == 2:
            path = a_star.a_star(graph, start_bus_stop, end_bus_stop, 0, "least walking")
        return path

    def getBusCoordinates(self, bus_stop):
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

        route_coordinates, bus_stop_coordinates, path = self.getBusRouteCoordinatesAndStopCoordinates(bus_service)
        reversed_route_coordinates = []
        for i in range(len(route_coordinates)):
            reversed_route_coordinates.append([route_coordinates[i][1], route_coordinates[i][0]])
        folium_map = folium.Map(location = reversed_route_coordinates[0], tiles = 'cartodbpositron', zoom_start = 14)
        for i in range(len(path)):
            marker = folium.Marker([bus_stop_coordinates[i][0], bus_stop_coordinates[i][1]])
            popup_html = f"""
            <div>
                <h3>{path[i]}</h3>
                <p>Bus Stop No: {i + 1}</p>
            </div>
            """
            popup = folium.Popup(html=popup_html,max_width=200)
            marker.add_child(popup)
            marker.add_to(folium_map)

        folium.PolyLine(locations = [list(coords) for coords in reversed_route_coordinates], weight = 3, color = 'blue').add_to(folium_map)

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

    def getBusRouteCoordinatesAndStopCoordinates(self, bus_service):
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

        route_coordinates = []
        path = []
        bus_stop_coordinates = []
        bus_routes = json.loads(open('bus_stops_cleaned_revised.json').read())
        number_of_bus_stops = len(bus_routes[bus_service]["Bus stop"].keys())
        for i in range(number_of_bus_stops):
            path.append(bus_routes[bus_service]["Bus stop"][str(i)])
        for i in range(len(path)):
            current_stop_coords = bus_routes[bus_service]['GPS Location'][str(i)]
            current_stop_coords = current_stop_coords.split(", ")
            current_stop_coords = [float(coord) for coord in current_stop_coords]
            bus_stop_coordinates.append(current_stop_coords)
        for i in range(len(path) - 1):
            for key in graph[path[i]][path[i + 1]]:
                if (key['Bus Service'] == bus_service and 'Road Route' in key):
                    route_coordinates += key['Road Route']

        return route_coordinates, bus_stop_coordinates, path

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor('white'))


class AutoCompleteLineEdit(QLineEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.suggestions = []
        self.suggestion_list = QListWidget()
        self.suggestion_list.setWindowFlag(Qt.WindowType.Popup)

        self.editingFinished.connect(self.update_suggestions)
        self.suggestion_list.itemClicked.connect(self.complete_text)

    def update_suggestions(self):
        text = self.text()
        self.suggestion_list.clear()
        self.suggestions = []
        if len(text) > 0:
            for suggestion in self.get_suggestions(text):
                item = QListWidgetItem(suggestion)
                self.suggestion_list.addItem(item)
                self.suggestions.append(suggestion)
            self.show_suggestion_list()
        else:
            self.hide_suggestion_list()

    def get_suggestions(self, text):
        # Implement the KMP algorithm to search for suggestions
        suggestions = []
        for suggestion in self.all_suggestions:
            if self.kmp_match(text, suggestion):
                suggestions.append(suggestion)
        return suggestions

    def kmp_match(self, pattern, text):
        # KMP algorithm implementation
        m = len(pattern)
        n = len(text)
        if m == 0:
            return True
        if n == 0:
            return False
        lps = self.compute_lps(pattern)
        i = 0
        j = 0
        while i < n:
            if pattern[j] == text[i]:
                i += 1
                j += 1
            if j == m:
                return True
            elif i < n and pattern[j] != text[i]:
                if j != 0:
                    j = lps[j-1]
                else:
                    i += 1
        return False

    def compute_lps(self, pattern):
        # Compute the Longest Prefix Suffix (LPS) array for the pattern
        m = len(pattern)
        lps = [0] * m
        i = 1
        j = 0
        while i < m:
            if pattern[i] == pattern[j]:
                j += 1
                lps[i] = j
                i += 1
            elif j != 0:
                j = lps[j-1]
            else:
                lps[i] = 0
                i += 1
        return lps

    def complete_text(self, item):
        self.setText(item.text())
        self.hide_suggestion_list()

    def show_suggestion_list(self):
        self.suggestion_list.setGeometry(self.geometry().x(), self.geometry().y() + self.geometry().height(), self.geometry().width(), self.suggestion_list.sizeHintForRow(0) * self.suggestion_list.count())
        self.suggestion_list.show()

    def hide_suggestion_list(self):
        self.suggestion_list.hide()


class Window(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        layout = QVBoxLayout(self)
        self.line_edit = AutoCompleteLineEdit()
        self.line_edit.all_suggestions = list(json.loads(open('graph.json').read()).keys())
        layout.addWidget(self.line_edit)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    myApp = MyApp()
    myApp.setWindowTitle("Bas Muafakat Johor")
    myApp.show()

    floatingWindow = FloatingWindow()
    floatingWindow.setGeometry(100, 100, 300, 200)
    floatingWindow.setWindowTitle("Directions")

    searchbus = Window()
    searchbus.show()

    try:
        sys.exit(app.exec())
    except SystemExit:
        print('Closing Window')