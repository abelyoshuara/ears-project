# -*- coding: utf-8 -*-
"""filtering.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1etm2Axa1uI-j0fPEuou6VgkYYb9YjXev
"""

import numpy as np
from scipy.spatial.distance import cdist
import json
import folium
import requests
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# Initialize Firestore
cred = credentials.Certificate('serviceaccountkey.json')
firebase_admin.initialize_app(cred, name='ears-project')
db = firestore.client(app=firebase_admin.get_app(name='ears-project'))

# Function to load hospital data from Firestore
def load_hospital_data():
    hospital_data = {}
    hospitals_docs = hospitals_ref.get()
    for doc in hospitals_docs:
        hospital = doc.to_dict()
        hospital_name = hospital['name']
        latitude = hospital['coordinate'].latitude
        longitude = hospital['coordinate'].longitude
        hospital_data[hospital_name] = [latitude, longitude]
    return hospital_data


# Load hospital data from Firestore
hospital_data = load_hospital_data()

# Data preferences for users (example)
user_preferences = {
    "User 1": {
        # "RSIA Medika Husada": 4,
        "RSU Griya Husada": 5,
        # "RSIA Aria Medika": 2,
    },
    "User 2": {
        "RSIA Medika Husada": 2,
        "RSU Griya Husada": 4,
        "RSIA Aria Medika": 3,
    },
}

# Function for collaborative filtering using Item-based CF approach
def collaborative_filtering(item_preferences, target_item):
    distances = []
    ratings = []
    for item, rating in item_preferences.items():
        if item != target_item:
            distances.append(cdist([[hospital_data[item][0], hospital_data[item][1]]], [[hospital_data[target_item][0], hospital_data[target_item][1]]]))
            ratings.append(rating)
    distances = np.array(distances)
    ratings = np.array(ratings)
    similarities = 1 / (1 + distances)  # Using a simple similarity function
    weighted_ratings = np.dot(similarities, ratings) / np.sum(similarities)
    return weighted_ratings

# Function to find the nearest hospital based on user location
def find_nearest_hospital(latitude, longitude):
    user_location = np.array([[latitude, longitude]])
    distances = cdist(user_location, list(hospital_data.values()))
    nearest_hospital_idx = np.argmin(distances)
    nearest_hospital = list(hospital_data.keys())[nearest_hospital_idx]
    return nearest_hospital

# Function to recommend the nearest hospital based on user preferences
def recommend_nearest_hospital(user_id):
    user_preferences_data = user_preferences[user_id]
    hospital_scores = {}
    for hospital in hospital_data:
        if hospital not in user_preferences_data:
            hospital_scores[hospital] = collaborative_filtering(user_preferences_data, hospital)
    if not hospital_scores:
        return "No hospitals have been rated by the user yet"
    recommended_hospital = max(hospital_scores, key=hospital_scores.get)
    return recommended_hospital

# Function to get distance and travel duration using the Distance Matrix API
def get_distance_duration(user_latitude, user_longitude, destination_latitude, destination_longitude, api_key):
    url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={user_latitude},{user_longitude}&destinations={destination_latitude},{destination_longitude}&key={api_key}"
    response = requests.get(url)
    data = response.json()
    distance = data['rows'][0]['elements'][0]['distance']['text']
    duration = data['rows'][0]['elements'][0]['duration']['text']
    return distance, duration

# Function to display the map with the nearest hospital location and route from user location
def show_hospital_location_with_route(user_latitude, user_longitude, hospital_name, api_key):
    user_location = [user_latitude, user_longitude]
    hospital_location = hospital_data[hospital_name]

    distance, duration = get_distance_duration(user_latitude, user_longitude, hospital_location[0], hospital_location[1], api_key)

    map_hospital = folium.Map(location=user_location, zoom_start=12)
    folium.Marker(user_location, popup='Your Location', icon=folium.Icon(color='blue')).add_to(map_hospital)
    folium.Marker(hospital_location, popup=hospital_name, icon=folium.Icon(color='red')).add_to(map_hospital)
    folium.PolyLine(locations=[user_location, hospital_location], color='green').add_to(map_hospital)

    folium.Popup(f"Distance: {distance}, Duration: {duration}").add_to(folium.Marker(hospital_location))

    return map_hospital

# Example usage
user_latitude = -7.266913
user_longitude = 111.798422
nearest_hospital = find_nearest_hospital(user_latitude, user_longitude)
recommended_hospital = recommend_nearest_hospital("User 1")

print("Nearest Hospital:", nearest_hospital)
print("Recommended Hospital:", recommended_hospital)

# Display the map with the nearest hospital location and route from user location
api_key = 'AIzaSyBSqQ90xfdoyQNG3ldpMI9M4hlOhk3BFM0'
hospital_map = show_hospital_location_with_route(user_latitude, user_longitude, nearest_hospital, api_key)
hospital_map

