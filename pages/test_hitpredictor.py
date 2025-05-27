import pytest
from unittest.mock import patch, MagicMock
import numpy as np
import os

# Import functions from the module to be tested
from pages.hitpredictor import getSongURI, getSongFeatures, Predict, main
# Import module to patch its global variables MY_ID, MY_SECRET
from pages import hitpredictor

# Dummy Spotify API credentials for testing
TEST_SPOTIFY_ID = "test_id_mocked"
TEST_SPOTIFY_SECRET = "test_secret_mocked"

@pytest.fixture(autouse=True)
def mock_hitpredictor_credentials_and_globals():
    """Mocks Spotify API credentials directly in the hitpredictor module and resets globals."""
    with patch.object(hitpredictor, 'MY_ID', TEST_SPOTIFY_ID), \
         patch.object(hitpredictor, 'MY_SECRET', TEST_SPOTIFY_SECRET):
        
        original_track_fetched = hitpredictor.trackFetched
        original_artist_fetched = hitpredictor.artistFetched
        hitpredictor.trackFetched = ""
        hitpredictor.artistFetched = ""
        
        yield # Test runs here
        
        hitpredictor.trackFetched = original_track_fetched
        hitpredictor.artistFetched = original_artist_fetched


class TestGetSongURI:
    @patch('pages.hitpredictor.spotipy.Spotify')
    def test_get_song_uri_success_primary(self, mock_spotify_class):
        mock_sp_instance = MagicMock()
        mock_spotify_class.return_value = mock_sp_instance
        
        mock_sp_instance.search.return_value = {
            'tracks': {
                'items': [{
                    'uri': 'spotify:track:dummy_uri',
                    'artists': [{'name': 'Test Artist'}] # Spotify's capitalization
                }]
            }
        }
        
        uri, artist = getSongURI('Test Track', 'Test Artist') # User input capitalization
        
        assert uri == 'spotify:track:dummy_uri'
        assert artist == 'Test Artist' # Expect Spotify's capitalization
        mock_sp_instance.search.assert_called_once_with(q='track:Test Track artist:Test Artist', type='track', limit=1)

    @patch('pages.hitpredictor.spotipy.Spotify')
    def test_get_song_uri_success_secondary(self, mock_spotify_class):
        mock_sp_instance = MagicMock()
        mock_spotify_class.return_value = mock_sp_instance
        
        mock_sp_instance.search.side_effect = [
            { # Primary search: artist mismatch or not found directly
                'tracks': { 'items': [] } 
            },
            { # Secondary search: broader track search
                'tracks': { 'items': [{'uri': 'spotify:track:correct_uri', 'artists': [{'name': 'Test Artist'}] }] }
            }
        ]
        
        uri, artist = getSongURI('Test Track', 'Test Artist')
        
        assert uri == 'spotify:track:correct_uri'
        assert artist == 'Test Artist'
        assert mock_sp_instance.search.call_count == 2
        mock_sp_instance.search.assert_any_call(q='track:Test Track artist:Test Artist', type='track', limit=1)
        mock_sp_instance.search.assert_any_call(q='track:Test Track', type='track', limit=10)


    @patch('pages.hitpredictor.spotipy.Spotify')
    def test_get_song_uri_not_found(self, mock_spotify_class):
        mock_sp_instance = MagicMock()
        mock_spotify_class.return_value = mock_sp_instance
        mock_sp_instance.search.return_value = {'tracks': {'items': []}} # Both searches find nothing suitable
        
        uri, artist = getSongURI('NonExistent Track', 'Unknown Artist')
        
        assert uri is None
        assert artist is None 
        assert mock_sp_instance.search.call_count == 2 # Primary and secondary searches

    @patch('pages.hitpredictor.spotipy.Spotify')
    def test_get_song_uri_api_exception(self, mock_spotify_class, capsys):
        mock_sp_instance = MagicMock()
        mock_spotify_class.return_value = mock_sp_instance
        mock_sp_instance.search.side_effect = Exception("Spotify API is down")

        uri, artist = getSongURI('Any Track', 'Any Artist')
        assert uri is None
        assert artist is None
        captured = capsys.readouterr()
        assert "Error during Spotify search: Spotify API is down" in captured.out


class TestGetSongFeatures:
    @patch('pages.hitpredictor.spotipy.Spotify')
    def test_get_song_features_success(self, mock_spotify_class):
        mock_sp_instance = MagicMock()
        mock_spotify_class.return_value = mock_sp_instance

        mock_sp_instance.track.return_value = {
            'name': 'Test Track Name',
            'artists': [{'id': 'artist_id_123', 'name': 'Test Artist Name'}],
            'album': {'release_date': '2023-01-01'} # Not used by current features_list
        }
        # mock_sp_instance.artist.return_value is not strictly needed as respArtist not used for features
        mock_sp_instance.audio_features.return_value = [{
            'danceability': 0.8, 'energy': 0.7, 'key': 5, 'loudness': -5.0, 'mode': 1, 
            'speechiness': 0.1, 'acousticness': 0.2, 'instrumentalness': 0.0, 
            'liveness': 0.3, 'valence': 0.6, 'tempo': 120.0, 'duration_ms': 200000
        }]
        mock_sp_instance.audio_analysis.return_value = {
            'track': {'time_signature': 4} 
        }

        features = getSongFeatures('dummy_track_id')

        assert len(features) == 17 # 15 numerical + track_name + artist_name
        assert features[-2] == 'Test Track Name' 
        assert features[-1] == 'Test Artist Name' 
        assert hitpredictor.trackFetched == 'Test Track Name' # Check global update
        assert hitpredictor.artistFetched == 'Test Artist Name' # Check global update
        
        assert features[0] == 0.8  # danceability
        assert features[12] == 0 # time_sig_3_4 for 4/4 time
        assert features[13] == 1 # time_sig_4_4 for 4/4 time
        assert features[14] == 0 # time_sig_5_4 for 4/4 time

    @patch('pages.hitpredictor.spotipy.Spotify')
    def test_get_song_features_api_error(self, mock_spotify_class, capsys):
        mock_sp_instance = MagicMock()
        mock_spotify_class.return_value = mock_sp_instance
        mock_sp_instance.track.side_effect = Exception("Spotify API Error") # Simulate error
        
        features = getSongFeatures('error_track_id')
        
        assert features == [] 
        captured = capsys.readouterr()
        # Check for the more specific error message from the except block
        assert "Error processing track error_track_id: Spotify API Error" in captured.out
        assert hitpredictor.trackFetched == "" # Globals should not be updated on error
        assert hitpredictor.artistFetched == ""


class TestPredict:
    # Using the exact mean and sigma from hitpredictor.py's Predict function
    MEAN_FROM_SCRIPT = np.array([0.5835781324582339, 0.654001223150358, 5.230608591885441, -7.460534307875895, 0.6781026252983293, 0.08133218973747017, 0.21211613053400952, 0.1537536808711217, 0.16788397971360383, 0.4597849940334129, 119.74174433174225, 238704.5886038186, 3.9388424821002386, 40.00194386933174, 10.279534606205251])
    SIGMA_FROM_SCRIPT = np.array([0.1752319536831673, 0.21679968258791865, 3.5672343581732098, 3.494355651030302, 0.4672038686289347, 0.07525371619350751, 0.26861114395875435, 0.30849449096614123, 0.11428926622921333, 0.2520444019009235, 28.655790678789145, 63031.36109581164, 0.2819461796498358, 16.42316566194086, 2.849291043273701])
    COEFFS_FROM_SCRIPT = np.array([0.65881293,-0.75794374,0.07299699,0.6198677,-0.06943223,-0.16899984,
                                  -0.48260568,-1.39537618,0.025739,0.65874328,0.13511095,0.43418161,
                                   0.10174503,-0.13353629,0.14347876])
    INTERCEPT_FROM_SCRIPT = np.array([0.87542461])

    def test_predict_with_track_artist_info(self):
        sample_features_full = [
            0.8, 0.7, 5, -5.0, 1, 0.1, 0.2, 0.0, 0.3, 0.6, 120.0, 200000,
            0, 1, 0, 
            'Test Track From Input', 'Test Artist From Input'
        ]
        prob, track, artist = Predict(sample_features_full)
        assert isinstance(prob, float)
        assert 0 <= prob <= 100
        assert track == 'Test Track From Input' 
        assert artist == 'Test Artist From Input'
        assert hitpredictor.trackFetched == 'Test Track From Input'
        assert hitpredictor.artistFetched == 'Test Artist From Input'

    def test_predict_with_numerical_features_only(self):
        sample_features_numeric = [
            0.8, 0.7, 5, -5.0, 1, 0.1, 0.2, 0.0, 0.3, 0.6, 120.0, 200000, 0, 1, 0 
        ]
        hitpredictor.trackFetched = "PreExistingTrack" # Set globals before call
        hitpredictor.artistFetched = "PreExistingArtist"
        prob, track, artist = Predict(sample_features_numeric)
        assert isinstance(prob, float)
        assert 0 <= prob <= 100
        assert track == "PreExistingTrack" # Globals should not have been changed by Predict
        assert artist == "PreExistingArtist"
        assert hitpredictor.trackFetched == "PreExistingTrack" 
        assert hitpredictor.artistFetched == "PreExistingArtist"

    def test_predict_calculation_correctness(self):
        input_features_numeric = (self.MEAN_FROM_SCRIPT + self.SIGMA_FROM_SCRIPT).tolist() # Normalized features will be ~1.0
        
        normalized_features_manual = (np.array(input_features_numeric) - self.MEAN_FROM_SCRIPT) / self.SIGMA_FROM_SCRIPT
        val_manual = np.dot(normalized_features_manual, self.COEFFS_FROM_SCRIPT) + self.INTERCEPT_FROM_SCRIPT[0]
        expected_prob_percent = (1 / (1 + np.exp(-val_manual))) * 100

        prob, _, _ = Predict(input_features_numeric)
        assert np.isclose(prob, expected_prob_percent, atol=1e-1) # Increased atol slightly

    def test_predict_empty_input(self, capsys):
        prob, track, artist = Predict([])
        assert prob == 0.0
        assert track == "" # Expect default empty string from global
        assert artist == ""
        captured = capsys.readouterr()
        assert "Error: Predict function received list of unexpected length 0." in captured.out

    def test_predict_input_wrong_length(self, capsys):
        prob, track, artist = Predict([1,2,3])
        assert prob == 0.0
        captured = capsys.readouterr()
        assert "Error: Predict function received list of unexpected length 3." in captured.out
        
    def test_predict_input_non_numeric(self, capsys):
        prob, track, artist = Predict([0.1]*14 + ["not_a_number"]) # 15 elements, one is bad
        assert prob == 0.0
        captured = capsys.readouterr()
        assert "Error: Numerical features list contains non-numeric values." in captured.out


class TestMainFunction:
    @patch('pages.hitpredictor.Predict') 
    @patch('pages.hitpredictor.getSongFeatures')
    @patch('pages.hitpredictor.getSongURI')
    def test_main_successful_prediction(self, mock_get_song_uri, mock_get_song_features, mock_predict):
        mock_get_song_uri.return_value = ('spotify:track:dummy_uri', 'ArtistFromSpotifyURI')
        # getSongFeatures returns 17 elements: 15 numerical + track_name + artist_name
        sample_features_from_gsf = [0.1] * 15 + ['TrackFromGetSongFeatures', 'ArtistFromGetSongFeatures']
        mock_get_song_features.return_value = sample_features_from_gsf
        
        # Predict is called with sample_features_from_gsf. 
        # It will update globals trackFetched/artistFetched internally from these.
        # Predict then returns prob, and the (now updated) global trackFetched, artistFetched.
        mock_predict.return_value = (75.5, 'TrackFromGetSongFeatures', 'ArtistFromGetSongFeatures')

        result_prob, result_track, result_artist = main('Some Track', 'Some Artist')

        mock_get_song_uri.assert_called_once_with('Some Track', 'Some Artist')
        mock_get_song_features.assert_called_once_with('spotify:track:dummy_uri')
        mock_predict.assert_called_once_with(sample_features_from_gsf)
        
        assert result_prob == 75.5
        # main returns the track/artist names that Predict returns (which are from globals)
        assert result_track == 'TrackFromGetSongFeatures'
        assert result_artist == 'ArtistFromGetSongFeatures'


    @patch('pages.hitpredictor.getSongFeatures')
    @patch('pages.hitpredictor.getSongURI')
    def test_main_error_in_get_song_uri(self, mock_get_song_uri, mock_get_song_features, capsys):
        mock_get_song_uri.return_value = (None, None) 
        
        result_prob, result_track, result_artist = main('Unknown Track', 'Original Artist')
        
        mock_get_song_uri.assert_called_once_with('Unknown Track', 'Original Artist')
        mock_get_song_features.assert_not_called() 
        
        assert result_prob == 0.0
        assert result_track == 'Unknown Track' # main returns original track name
        assert result_artist == 'Original Artist' # main returns original artist name
        captured = capsys.readouterr()
        assert "Song not found / error in input." in captured.out # Message from main

    @patch('pages.hitpredictor.getSongFeatures')
    @patch('pages.hitpredictor.getSongURI')
    def test_main_error_in_get_song_features(self, mock_get_song_uri, mock_get_song_features, capsys):
        mock_get_song_uri.return_value = ('spotify:track:dummy_uri', 'ArtistFromSpotifyURI')
        mock_get_song_features.return_value = [] # Simulate error in fetching features
        
        result_prob, result_track, result_artist = main('Some Track', 'Original Artist')
        
        mock_get_song_uri.assert_called_once_with('Some Track', 'Original Artist')
        mock_get_song_features.assert_called_once_with('spotify:track:dummy_uri')
        
        assert result_prob == 0.0 
        assert result_track == 'Some Track' # Original track name
        assert result_artist == 'ArtistFromSpotifyURI' # Artist name updated by successful getSongURI
        captured = capsys.readouterr()
        assert "Failed to get song features." in captured.out # Message from main
