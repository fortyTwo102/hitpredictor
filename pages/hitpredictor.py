import numpy as np
from sklearn.linear_model import LogisticRegression
from scipy import stats
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os


import math

def sigmoid(x):
  return 1 / (1 + math.exp(-x))


database = {}

trackFetched = "" 
artistFetched = ""

def getSongURI(trackName,artistName):

	client_credentials_manager = SpotifyClientCredentials(client_id='ad3b6e58606c4b1d91832ecd0c160557',client_secret='e3f68c9f1c2b42e5a48a1d61e10fa0ab')
	sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
	

	
	track = sp.search(q='artist:' + artistName+' track:'+trackName,type='track',limit=10)

	result = track['tracks']['items']

	for each in result:
		for artist in each['artists']:			
			if artist['name'].lower() == artistName.lower():
				uri = each['uri']
				artistName = artist['name']
				return uri, artistName

			

	


	track = sp.search(trackName,type='track',limit=50)

	result = track['tracks']['items']

	for each in result:
		for artist in each['artists']:			
			if artist['name'].lower() == artistName.lower():
				uri = each['uri']
				artistName = artist['name']
				return uri,artistName


		

	

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

		#FETCHING ARTIST DETAILS
		respTrack = sp.track(trackID)

		artistID = respTrack['artists'][0]['id']

		artistFetched = respTrack['artists'][0]['name']
		trackFetched =  respTrack['name']

		respArtist = sp.artist(artistID)
		#data.append(respArtist['popularity'])


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

	if len(feature) == 17:
		trackFetched = feature[-2]
		artistFetched = feature[-1]
		feature = feature[:-2]
	
	'''dirpath = os.path.dirname(os.path.abspath(__file__))
			
				data = np.loadtxt(dirpath + "\\songdatabase1.txt", delimiter='\t')
				
				#Removing Outliers
				z = np.abs(stats.zscore(data))
				data = data[(z < 3).all(axis=1)]
			
				X, y = data[:, :16], data[:, 16]
			
				mean, sigma, X = featureNorm(X)'''

	feature = np.array(feature)

	mean = [0.5835781324582339, 0.654001223150358, 5.230608591885441, -7.460534307875895, 0.6781026252983293, 0.08133218973747017, 0.21211613053400952, 0.1537536808711217, 0.16788397971360383, 0.4597849940334129, 119.74174433174225, 238704.5886038186, 3.9388424821002386, 40.00194386933174, 10.279534606205251]
	sigma = [0.1752319536831673, 0.21679968258791865, 3.5672343581732098, 3.494355651030302, 0.4672038686289347, 0.07525371619350751, 0.26861114395875435, 0.30849449096614123, 0.11428926622921333, 0.2520444019009235, 28.655790678789145, 63031.36109581164, 0.2819461796498358, 16.42316566194086, 2.849291043273701]

	mean = np.array(mean)
	sigma = np.array(sigma) 


	feature = (feature - mean) / sigma #getting the scaled feature
	feature = feature.reshape(-1,feature.shape[0])

	#X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=1/3, random_state=1)

	'''model = LogisticRegression(solver='lbfgs')

	

	a = model.fit(X, y)'''

	intercept = np.array([0.87542461])
	#feature = feature.reshape(-1,feature.shape[0])

	# trained = [0.57614029,-0.61779822,0.09654665,0.42180564,-0.04661171,-0.19334932,-0.51271454,-1.24322112,0.03067779,0.6676387,0.11899211,0.35745331,0.10556957,-0.11559462,0.1769944]
	trained = [0.65881293,-0.75794374,0.07299699,0.6198677,-0.06943223,-0.16899984,\
  -0.48260568,-1.39537618,0.025739,0.65874328,0.13511095,0.43418161, \
   0.10174503,-0.13353629,0.14347876]

	trained = np.array(trained)

	feature = feature[0]

	perc = sigmoid(np.dot(feature, trained) + intercept)


	#print(a.coef_)
	#print(feature)

	'''y_pred = model.predict(feature)'''

	#probability = round((model.predict_proba(feature)[0][1])*100,1)
	probability = round(perc*100,1)
	#print("There's a",probability,"% chance of "+trackFetched + " by "+artistFetched+ " being a hit!")

	return probability, trackFetched, artistFetched

def main(track, artist):

	print("Fetching Track URI from Spotify....",end="")
	spotifyURI,a = getSongURI(track, artist)
	print("Fetched!")
	print("Fetching Track features from Spotify....",end="")
	songFeature = getSongFeatures(spotifyURI)
	print("Fetched!")

	r, t, x = Predict(songFeature)

	return r, t, a	
