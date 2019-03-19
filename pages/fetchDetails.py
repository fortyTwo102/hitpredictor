import asyncio
import spotify

async def getTrackID(track,artist):

	client = spotify.Client('ad3b6e58606c4b1d91832ecd0c160557', 'e3f68c9f1c2b42e5a48a1d61e10fa0ab')
	results = await client.search('drake')

	ids = []
	artistName = []
	trackName = []

	results = await client.search(track, types=['track'])

	for i in range(len(results['tracks'])):
		for j in range(len(results['tracks'][i].artists)):
			if results['tracks'][i].artists[j].name.lower() == artist.lower():

				
				artistName.append(results['tracks'][i].artists[j].name) 
				trackName.append(results['tracks'][i].name)
				ids.append(results['tracks'][i].id)
	    		
	   		

	return ids[0],artistName[0],trackName[0]

async def getTrackFeatures(ID):

	client = spotify.Client('ad3b6e58606c4b1d91832ecd0c160557', 'e3f68c9f1c2b42e5a48a1d61e10fa0ab')

	print("Fetching track features ... ",end="")

	track = await client.get_track(ID)

	audio_features = await track.audio_features()

	print("Fetched!")

	return audio_features


async def getTrackAnalysis(ID):

	client = spotify.Client('ad3b6e58606c4b1d91832ecd0c160557', 'e3f68c9f1c2b42e5a48a1d61e10fa0ab')

	print("Fetching track analysis ... ",end="")

	track = await client.get_track(ID)

	audio_analysis = await track.audio_analysis()

	print("Fetched!")

	return audio_analysis

def fetch(track,artist):

	
	
	ID, trackName, artistName = asyncio.get_event_loop().run_until_complete(getTrackID(track,artist))

	print(trackName, artistName)

	features = asyncio.get_event_loop().run_until_complete(getTrackFeatures(ID))
	analysis = asyncio.get_event_loop().run_until_complete(getTrackAnalysis(ID))

	return features,analysis


fetch("fireflies","owl city")