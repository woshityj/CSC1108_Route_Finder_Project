import pprint
import openrouteservice as ors
import folium

def get_route(start_lat, start_lon, end_lat, end_lon):
    client = ors.Client(key = '5b3ce3597851110001cf62483b2035bb64ee4d0080a2aeb8bd28d07e')
    folium_map = folium.Map(location = list([start_lat, start_lon]), tiles = 'cartodbpositron', zoom_start = 13)

    # Coordinates for Open Route Service takes in Longitutde, Latitude
    coords = [[start_lon, start_lat], [end_lon, end_lat]]
    route = client.directions(coords, profile = 'driving-car', format = 'geojson')
    pprint.pprint(route)
    folium.PolyLine(locations = [list(reversed(coord)) for coord in route['features'][0]['geometry']['coordinates']], color = 'blue').add_to(folium_map)
    folium_map.save("map.html")


import folium

# Initialize the map
m = folium.Map(location=[45.523, -122.675], zoom_start=13)

# Define the JavaScript callback function for handling clicks
click_handler_code = '''
let start_marker;
let end_marker;

function onMapClick(e) {
    if (!start_marker) {
        start_marker = L.marker(e.latlng).addTo(this)
            .bindPopup('Start: ' + e.latlng.toString()).openPopup();
    } else if (!end_marker) {
        end_marker = L.marker(e.latlng).addTo(this)
            .bindPopup('End: ' + e.latlng.toString()).openPopup();
    } else {
        this.removeLayer(start_marker);
        this.removeLayer(end_marker);

        start_marker = L.marker(e.latlng).addTo(this)
            .bindPopup('Start: ' + e.latlng.toString()).openPopup();
        end_marker = null;
    }
}

'''

# Add JavaScript callback to the map
map_click_handler = folium.Html('<script type="text/javascript">' + click_handler_code + '</script>', script=True)
m.get_root().header.add_child(map_click_handler)

# Attach the click event handler to the map
m.add_child(folium.ClickForMarker(popup=None, onclick=folium.JSCallback(code="onMapClick(event);")))

# Display the map

# Display the map
m.save("map.html")
# get_route(1.4964559999542668, 103.74374661113058, 1.6125013180073793, 103.65816892145304)
