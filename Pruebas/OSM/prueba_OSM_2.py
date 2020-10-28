import numpy as np
import matplotlib.pyplot as plt
import requests
import json

overpass_url = "http://overpass-api.de/api/interpreter"
overpass_query = """
[out:json];
area(3600339549);
(node["amenity"="bar"](area);
 way["amenity"="bar"](area);
 rel["amenity"="bar"](area);
);
out center;
"""
# Area de España
#  area["ISO3166-1"="ES"][admin_level=2];

response = requests.get(overpass_url, 
                        params={'data': overpass_query})
data = response.json()
# Collect coords into list
coords = []
for element in data['elements']:
  if element['type'] == 'node':
    lon = element['lon']
    lat = element['lat']
    coords.append((lon, lat))
  elif 'center' in element:
    lon = element['center']['lon']
    lat = element['center']['lat']
    coords.append((lon, lat))
# Convert coordinates into numpy array
X = np.array(coords)
plt.plot(X[:, 0], X[:, 1], 'o')
plt.title('Bares en Bilbao')
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.axis('equal')
plt.show()