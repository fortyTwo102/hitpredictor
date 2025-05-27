import numpy as np
from sklearn.linear_model import LogisticRegression # Not actually used for prediction in the provided Predict function
from scipy import stats # Not actually used in the provided Predict function
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
import math

# Define MY_ID and MY_SECRET at the module level, to be loaded from environment variables
MY_ID = os.environ.get('MY_ID')
MY_SECRET = os.environ.get('MY_SECRET')

def sigmoid(x):
  return 1 / (1 + math.exp(-x))

# database = {} # This global variable is not used

trackFetched = "" 
artistFetched = ""

def getSongURI(trackName, artistName):
    # Ensure MY_ID and MY_SECRET are available; if not, Spotipy will raise an error.
    if not MY_ID or not MY_SECRET:
        print("Spotify API credentials (MY_ID, MY_SECRET) not found in environment variables.")
        return None, None
    
    client_credentials_manager = SpotifyClientCredentials(client_id=MY_ID, client_secret=MY_SECRET)
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    
    # Primary search: specific artist and track
    # Original query: 'artist:' + artistName+' track:'+trackName
    # Spotipy's q field format is more like 'track:TRACKNAME artist:ARTISTNAME'
    query1 = f'track:{trackName} artist:{artistName}'
    try:
        results1 = sp.search(q=query1, type='track', limit=1) # Limit 1 is usually enough if expecting direct match
        if results1['tracks']['items']:
            item = results1['tracks']['items'][0]
            # Check if the main artist matches (case-insensitive)
            if item['artists'] and item['artists'][0]['name'].lower() == artistName.lower():
                return item['uri'], item['artists'][0]['name'] # Return Spotify's capitalization

        # Secondary search: just track name (broader)
        # Original query: trackName (which sp.search handles as q=trackName)
        query2 = f'track:{trackName}'
        results2 = sp.search(q=query2, type='track', limit=10) # Broader search, might need to check more items
        for item in results2['tracks']['items']:
            if item['artists'] and item['artists'][0]['name'].lower() == artistName.lower():
                return item['uri'], item['artists'][0]['name']
    except Exception as e:
        print(f"Error during Spotify search: {e}")
        return None, None
        
    return None, None # If no suitable track found

# featureNorm is defined but not used by the provided Predict function directly.
# Predict uses hardcoded mean/sigma.
# def featureNorm(X):
# 	mean = []
# 	std = []
# 	for i in range(X.shape[1]):
# 		col = X[:,i]
# 		mean.append(np.mean(col))
# 		std.append(np.std(col))
# 		X[:,i] = (col - np.mean(col))  / np.std(col)
# 	return mean, std, X	

def getSongFeatures(trackID):
    global trackFetched
    global artistFetched

    if not MY_ID or not MY_SECRET:
        print("Spotify API credentials (MY_ID, MY_SECRET) not found in environment variables for getSongFeatures.")
        return []

    client_credentials_manager = SpotifyClientCredentials(client_id=MY_ID, client_secret=MY_SECRET)
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

    features_list = [] # Renamed 'data' to 'features_list' for clarity
    try:
        respTrack = sp.track(trackID)
        if not respTrack: return [] # Handle track not found

        artistID = respTrack['artists'][0]['id']
        # These globals are updated here
        artistFetched = respTrack['artists'][0]['name']
        trackFetched =  respTrack['name']

        # respArtist = sp.artist(artistID) # This call was not used for features.
        # data.append(respArtist['popularity']) # This line was commented out.

        respFeature = sp.audio_features(trackID)
        if not respFeature or not respFeature[0]: return [] # Handle audio features not found

        # Ordered list of features based on typical audio feature sets
        # danceability, energy, key, loudness, mode, speechiness, acousticness,
        # instrumentalness, liveness, valence, tempo, duration_ms
        feature_order = [
            'danceability', 'energy', 'key', 'loudness', 'mode', 
            'speechiness', 'acousticness', 'instrumentalness', 
            'liveness', 'valence', 'tempo', 'duration_ms'
        ]
        for key in feature_order:
            features_list.append(respFeature[0].get(key))
        
        # Audio analysis for time signature
        respAnalysis = sp.audio_analysis(trackID)
        if not respAnalysis: return [] # Handle audio analysis not found
        
        time_signature = respAnalysis['track'].get('time_signature', 0) # Default to 0 if not found

        # Add time signature features (example: one-hot encode common time signatures)
        if time_signature == 3: features_list += [1,0,0] # 3/4 time
        elif time_signature == 4: features_list += [0,1,0] # 4/4 time
        elif time_signature == 5: features_list += [0,0,1] # 5/4 time
        else: features_list += [0,0,0] # Other or unknown

        # The original code had chorusHit and sections from respAnalysis,
        # but the Predict function uses 15 features, and the 12 audio features + 3 time_sig = 15.
        # chorusHit = respAnalysis['sections'][2]['start'] # Potential IndexError if <3 sections
        # sections = len(respAnalysis['sections'])
        # features_list.append(chorusHit)
        # features_list.append(sections)
        # If these were intended, the hardcoded mean/sigma in Predict would need to be 17 elements.
        # For now, sticking to 15 numerical features.

    except Exception as e:
        # Print a more specific error message if possible
        print(f"Error processing track {trackID}: {e}")
        return [] # Return empty list on any error
        
    # Append track and artist names for potential use, making it 17 elements if successful
    if features_list and len(features_list) == 15 : # Ensure 15 numerical features were collected
        features_list.append(trackFetched)
        features_list.append(artistFetched)
        return features_list
    else: # If something went wrong and we didn't get 15 features
        print(f"Feature collection for {trackID} resulted in incomplete data.")
        return []


def Predict(feature_input): # Renamed 'feature' to 'feature_input' to avoid conflict
    global trackFetched
    global artistFetched

    # Ensure feature_input is a list, as expected from getSongFeatures
    if not isinstance(feature_input, list):
        print("Error: Predict function expects a list.")
        return 0.0, trackFetched, artistFetched # Return current globals or empty if not set

    numerical_features = []
    if len(feature_input) == 17: # 15 numerical + track + artist
        trackFetched = feature_input[-2]
        artistFetched = feature_input[-1]
        numerical_features = feature_input[:-2]
    elif len(feature_input) == 15: # Only numerical features
        numerical_features = feature_input
    else:
        print(f"Error: Predict function received list of unexpected length {len(feature_input)}.")
        # Return current global track/artist names, or empty strings if not set.
        return 0.0, trackFetched if trackFetched else "", artistFetched if artistFetched else ""

    if not all(isinstance(x, (int, float)) for x in numerical_features):
        print("Error: Numerical features list contains non-numeric values.")
        return 0.0, trackFetched, artistFetched

    feature_array = np.array(numerical_features, dtype=float)

    # These are the hardcoded mean and sigma values from the original script
    mean = np.array([0.5835781324582339, 0.654001223150358, 5.230608591885441, -7.460534307875895, 0.6781026252983293, 0.08133218973747017, 0.21211613053400952, 0.1537536808711217, 0.16788397971360383, 0.4597849940334129, 119.74174433174225, 238704.5886038186, 3.9388424821002386, 40.00194386933174, 10.279534606205251])
    sigma = np.array([0.1752319536831673, 0.21679968258791865, 3.5672343581732098, 3.494355651030302, 0.4672038686289347, 0.07525371619350751, 0.26861114395875435, 0.30849449096614123, 0.11428926622921333, 0.2520444019009235, 28.655790678789145, 63031.36109581164, 0.2819461796498358, 16.42316566194086, 2.849291043273701])

    if feature_array.shape[0] != mean.shape[0]: # Should be 15
        print(f"Error: Feature array length {feature_array.shape[0]} does not match model's expected 15 features.")
        return 0.0, trackFetched, artistFetched

    feature_array = (feature_array - mean) / sigma 
    
    # Coefficients for the logistic regression model
    trained_coeffs = np.array([0.65881293,-0.75794374,0.07299699,0.6198677,-0.06943223,-0.16899984,
                              -0.48260568,-1.39537618,0.025739,0.65874328,0.13511095,0.43418161,
                               0.10174503,-0.13353629,0.14347876])
    intercept = np.array([0.87542461]) # Single element array

    # Calculate prediction
    # Note: feature_array is 1D, trained_coeffs is 1D. Dot product is fine.
    raw_prediction = np.dot(feature_array, trained_coeffs) + intercept[0] # Add scalar intercept
    
    probability_value = sigmoid(raw_prediction) * 100
    
    return round(probability_value, 1), trackFetched, artistFetched

def main(track, artist):
    # These will hold the initially searched/passed track and artist name
    # to be returned if subsequent steps fail.
    original_track_name = track
    original_artist_name = artist

    print("Fetching Track URI from Spotify....", end="")
    uri, artist_from_uri = getSongURI(track, artist) # artist_from_uri is Spotify's capitalization
    if artist_from_uri: # If URI found, getSongURI returns Spotify's artist name
        original_artist_name = artist_from_uri # Update to Spotify's version for consistency

    if uri:
        print("Fetched!")
        print("Fetching Track features from Spotify....", end="")
        songFeature_list = getSongFeatures(uri) # This list will include track/artist if successful
        if songFeature_list:
            print("Fetched!")
            # Predict will use trackFetched/artistFetched updated by getSongFeatures
            prob, final_track, final_artist = Predict(songFeature_list)
            # final_track, final_artist are from globals updated by Predict (if 17 features) or getSongFeatures
            return prob, final_track, final_artist
        else:
            print("Failed to get song features.")
            # Return 0.0 prob and the original track/artist (artist name potentially updated by getSongURI)
            return 0.0, original_track_name, original_artist_name
    else:
        print("Song not found / error in input.")
        return 0.0, original_track_name, original_artist_name
