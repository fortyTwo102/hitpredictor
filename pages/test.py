import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

def getSongURI(artistName, trackName):

	client_credentials_manager = SpotifyClientCredentials(client_id='ad3b6e58606c4b1d91832ecd0c160557',client_secret='e3f68c9f1c2b42e5a48a1d61e10fa0ab')
	sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

	try:
		track = sp.search(trackName,type='track',limit=50)
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
	

print(getSongURI("drake","god's plan"))