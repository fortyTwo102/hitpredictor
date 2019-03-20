import numpy as np
from sklearn.linear_model import LogisticRegression
from scipy import stats
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os

database = {}

trackFetched = "" 
artistFetched = ""

def getSongURI(trackName,artistName):

	client_credentials_manager = SpotifyClientCredentials(client_id='ad3b6e58606c4b1d91832ecd0c160557',client_secret='e3f68c9f1c2b42e5a48a1d61e10fa0ab')
	sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
	

	try:
		track = sp.search(q='artist:' + artistName+' track:'+trackName,type='track',limit=10)

		result = track['tracks']['items']
		
		for each in result:
			if each['artists'][0]['name'].lower() == artistName.lower():
				uri = each['uri']
				break

		return uri		

		
	except:
		try:
			track = sp.search(trackName,type='track',limit=50)

			result = track['tracks']['items']
			
			for each in result:
				if each['artists'][0]['name'].lower() == artistName.lower():
					uri = each['uri']
					break

			return uri

		except:
			
			print(trackName+ " is not found.")	
	
	

def featureNorm(X):
	mean = []
	std = []

	for i in range(X.shape[1]):
		col = X[:,i]

		mean.append(np.mean(col))
		std.append(np.std(col))

		X[:,i] = (col - np.mean(col))  / np.std(col)

	return mean, std, X	

def getSongFeatures(trackID):

	global trackFetched
	global artistFetched

	

	client_credentials_manager = SpotifyClientCredentials(client_id='ad3b6e58606c4b1d91832ecd0c160557',client_secret='e3f68c9f1c2b42e5a48a1d61e10fa0ab')
	sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

	data = []
	#FETCHING TRACK NAME AND ARTIST NAME
	try:

		#FETCHING POPULARITY
		respTrack = sp.track(trackID)

		artistID = respTrack['artists'][0]['id']

		artistFetched = respTrack['artists'][0]['name']
		trackFetched =  respTrack['name']

		respArtist = sp.artist(artistID)
		data.append(respArtist['popularity'])


		#FETCHING AUDIO FEATURES

		respFeature = sp.audio_features(trackID)
		featureFields = list(respFeature[0].keys())

		for key in featureFields:
			if key in {'type','track_href','uri','id','analysis_url'}:
				pass
			else:	
				data.append(respFeature[0][key])
	


		#FETCHING AUDIO ANALYSIS

		respAnalysis = sp.audio_analysis(trackID)
		chorusHit = respAnalysis['sections'][2]['start']
		sections = len(respAnalysis['sections'])
		data.append(chorusHit)
		data.append(sections)
		
	except:
		print("Error in fetching "+ trackID)
		
		
	return data

def Predict(feature):
	
	global trackFetched
	global artistFetched

	if len(feature) == 18:
		trackFetched = feature[-2]
		artistFetched = feature[-1]
		feature = feature[:-2]
	
	dirpath = os.path.dirname(os.path.abspath(__file__))

	data = np.loadtxt(dirpath + "\\songdatabase1.txt", delimiter='\t')
	
	#Removing Outliers
	z = np.abs(stats.zscore(data))
	data = data[(z < 3).all(axis=1)]

	X, y = data[:, :16], data[:, 16]

	mean, sigma, X = featureNorm(X)

	feature = np.array(feature)
	mean = np.array(mean)
	sigma = np.array(sigma) 

	feature = (feature - mean) / sigma #getting the scaled feature
	feature = feature.reshape(-1,feature.shape[0])

	#X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=1/3, random_state=1)

	model = LogisticRegression(solver='lbfgs')

	model.fit(X, y)

	#feature = feature.reshape(-1,feature.shape[0])

	

	y_pred = model.predict(feature)

	probability = round((model.predict_proba(feature)[0][1])*100,1)
	#print("There's a",probability,"% chance of "+trackFetched + " by "+artistFetched+ " being a hit!")

	return probability, trackFetched, artistFetched

def main(track, artist):

	print("Fetching Track URI from Spotify....",end="")
	spotifyURI = getSongURI(track, artist)
	print("Fetched!")
	print("Fetching Track features from Spotify....",end="")
	songFeature = getSongFeatures(spotifyURI)
	print("Fetched!")

	r, t, a = Predict(songFeature)

	return r, t, a	
