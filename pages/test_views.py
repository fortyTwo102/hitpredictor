import pytest
from django.urls import reverse # To reverse URL names
from django.test import Client # Django's test client
from unittest.mock import patch

pytestmark = pytest.mark.django_db

class TestHomeView:
    def test_home_get_request(self, client: Client):
        """Test GET request to home view."""
        url = reverse('home')
        response = client.get(url)
        
        assert response.status_code == 200
        assert 'homeInput.html' in [t.name for t in response.templates]
        # args = {} is passed, so context should be "empty" from view's perspective
        # (Django defaults like csrf_token will be there)
        assert 'banner' not in response.context # Check specific keys from POST are not there
        assert 'perc' not in response.context
        assert 'error' not in response.context

    @patch('pages.views.hitpredictor.main')
    def test_home_post_request_hit(self, mock_hitpredictor_main, client: Client):
        """Test POST request to home view with a successful 'HIT' prediction."""
        mock_hitpredictor_main.return_value = (75.0, "Test Track", "Test Artist")
        url = reverse('home')
        data = {'track': 'Test Track', 'artist': 'Test Artist'}
        response = client.post(url, data)
        
        assert response.status_code == 200
        assert 'home.html' in [t.name for t in response.templates]
        assert response.context['banner'] == "IT'S A HIT!"
        assert response.context['perc'] == "75.0%"
        assert response.context['trackName'] == "Test Track"
        assert response.context['artistName'] == "Test Artist"
        mock_hitpredictor_main.assert_called_once_with('Test Track', 'Test Artist')

    @patch('pages.views.hitpredictor.main')
    def test_home_post_request_not_a_hit(self, mock_hitpredictor_main, client: Client):
        """Test POST request to home view with a 'NOT A HIT' prediction."""
        mock_hitpredictor_main.return_value = (30.0, "Test Track", "Test Artist")
        url = reverse('home')
        data = {'track': 'Test Track', 'artist': 'Test Artist'}
        response = client.post(url, data)
        
        assert response.status_code == 200
        assert 'home.html' in [t.name for t in response.templates]
        assert response.context['banner'] == "It might not do well. "
        assert response.context['perc'] == "30.0%"
        assert response.context['trackName'] == "Test Track"
        assert response.context['artistName'] == "Test Artist"
        mock_hitpredictor_main.assert_called_once_with('Test Track', 'Test Artist')

    @patch('pages.views.hitpredictor.main')
    def test_home_post_request_hitpredictor_returns_zero_perc_no_exception(self, mock_hitpredictor_main, client: Client):
        """Test POST request when hitpredictor.main returns 0.0 probability without an exception."""
        # According to view logic, 0.0% is treated like any other percentage < 50.
        mock_hitpredictor_main.return_value = (0.0, "Zero Perc Track", "Zero Perc Artist") 
        url = reverse('home')
        data = {'track': 'Zero Perc Track', 'artist': 'Zero Perc Artist'}
        response = client.post(url, data)
        
        assert response.status_code == 200
        assert 'home.html' in [t.name for t in response.templates] # Should render home.html
        assert response.context['banner'] == "It might not do well. " # Banner for < 50%
        assert response.context['perc'] == "0.0%"
        assert response.context['trackName'] == "Zero Perc Track"
        assert response.context['artistName'] == "Zero Perc Artist"
        assert 'error' not in response.context # No error message should be set here
        mock_hitpredictor_main.assert_called_once_with('Zero Perc Track', 'Zero Perc Artist')

    @patch('pages.views.hitpredictor.main')
    def test_home_post_request_missing_track(self, mock_hitpredictor_main, client: Client):
        """Test POST request with missing 'track' data."""
        url = reverse('home')
        data = {'artist': 'Test Artist'} 
        response = client.post(url, data)
        
        assert response.status_code == 200
        assert 'homeInput.html' in [t.name for t in response.templates]
        assert 'error' not in response.context # View sets args={}
        mock_hitpredictor_main.assert_not_called()

    @patch('pages.views.hitpredictor.main')
    def test_home_post_request_missing_artist(self, mock_hitpredictor_main, client: Client):
        """Test POST request with missing 'artist' data."""
        url = reverse('home')
        data = {'track': 'Test Track'} 
        response = client.post(url, data)
        
        assert response.status_code == 200
        assert 'homeInput.html' in [t.name for t in response.templates]
        assert 'error' not in response.context
        mock_hitpredictor_main.assert_not_called()
        
    @patch('pages.views.hitpredictor.main')
    def test_home_post_request_missing_both(self, mock_hitpredictor_main, client: Client):
        """Test POST request with missing 'track' and 'artist' data."""
        url = reverse('home')
        data = {}
        response = client.post(url, data)
        
        assert response.status_code == 200
        assert 'homeInput.html' in [t.name for t in response.templates]
        assert 'error' not in response.context
        mock_hitpredictor_main.assert_not_called()

    @patch('pages.views.hitpredictor.main')
    def test_home_post_hitpredictor_raises_exception(self, mock_hitpredictor_main, client: Client):
        """Test POST when hitpredictor.main raises a direct exception."""
        mock_hitpredictor_main.side_effect = Exception("Simulated hitpredictor crash")
        url = reverse('home')
        data = {'track': 'Any Track', 'artist': 'Any Artist'}
        response = client.post(url, data)

        assert response.status_code == 200
        assert 'homeInput.html' in [t.name for t in response.templates]
        # This is the error message from the `except` block in the view
        assert response.context['error'] == "Sorry :( your song is not available on Spotify servers, please check if there are any spelling mistakes; or the information you provided is correct."
        mock_hitpredictor_main.assert_called_once_with('Any Track', 'Any Artist')


class TestStaticViews:
    def test_about_view(self, client: Client):
        """Test the about view."""
        url = reverse('about')
        response = client.get(url)
        
        assert response.status_code == 200
        assert 'about.html' in [t.name for t in response.templates]
        # View passes args={}, so no view-specific keys in context
        assert 'error' not in response.context 
        assert 'banner' not in response.context

    def test_home_input_view_dedicated_route(self, client: Client):
        """Test the dedicated /homeInput/ route."""
        url = reverse('homeInput') # This URL is defined in pages/urls.py
        response = client.get(url)
        
        assert response.status_code == 200
        assert 'homeInput.html' in [t.name for t in response.templates]
        # View function homeInput passes args={}, so context is "empty" from view's perspective
        assert 'error' not in response.context
        assert 'banner' not in response.context

    def test_contact_view(self, client: Client):
        """Test the contact view."""
        url = reverse('contact')
        response = client.get(url)
        
        assert response.status_code == 200
        assert 'contact.html' in [t.name for t in response.templates]
        assert 'error' not in response.context
        assert 'banner' not in response.context
