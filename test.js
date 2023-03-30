function onMapClick(e) {
    if (typeof start_marker === 'undefined') {
        start_marker = L.marker(e.latlng).addTo(map)
            .bindPopup('Start: ' + e.latlng.toString()).openPopup();
    } else if (typeof end_marker === 'undefined') {
        end_marker = L.marker(e.latlng).addTo(map)
            .bindPopup('End: ' + e.latlng.toString()).openPopup();
    } else if (typeof start_marker !== 'undefined' && typeof end_marker !== 'undefined') {
        // Remove existing markers from the map
        map.removeLayer(start_marker);
        map.removeLayer(end_marker);

        // Reset markers
        start_marker = L.marker(e.latlng).addTo(map)
            .bindPopup('Start: ' + e.latlng.toString()).openPopup();
        end_marker = undefined;
    }
}

map.on('click', onMapClick);