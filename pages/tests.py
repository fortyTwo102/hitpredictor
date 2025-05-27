from django.test import TestCase
from pages.forms import HomeForm

# Create your tests here.

class TestHomeForm:

    def test_home_form_valid_data(self):
        """Test that the form is valid with correct title and artist."""
        form = HomeForm(data={'title': 'Test Song', 'artist': 'Test Artist'})
        assert form.is_valid()

    def test_home_form_empty_title(self):
        """Test that the form is invalid if title is empty."""
        form = HomeForm(data={'title': '', 'artist': 'Test Artist'})
        assert not form.is_valid()
        assert 'title' in form.errors
        assert 'This field is required.' in form.errors['title']

    def test_home_form_empty_artist(self):
        """Test that the form is invalid if artist is empty."""
        form = HomeForm(data={'title': 'Test Song', 'artist': ''})
        assert not form.is_valid()
        assert 'artist' in form.errors
        assert 'This field is required.' in form.errors['artist']

    def test_home_form_empty_title_and_artist(self):
        """Test that the form is invalid if both title and artist are empty."""
        form = HomeForm(data={'title': '', 'artist': ''})
        assert not form.is_valid()
        assert 'title' in form.errors
        assert 'artist' in form.errors
        assert 'This field is required.' in form.errors['title']
        assert 'This field is required.' in form.errors['artist']

    def test_home_form_no_data(self):
        """Test that the form is invalid if no data is provided."""
        form = HomeForm(data={})
        assert not form.is_valid()
        assert 'title' in form.errors
        assert 'artist' in form.errors
        assert 'This field is required.' in form.errors['title']
        assert 'This field is required.' in form.errors['artist']

    def test_home_form_labels(self):
        """Test that the form fields have the correct labels."""
        form = HomeForm()
        assert form.fields['title'].label == "    Title "
        assert form.fields['artist'].label == "Artist "

    def test_home_form_label_stripping(self):
        """Test that the form field title label has leading/trailing spaces."""
        # This test is more about Django's behavior or a potential custom widget/field,
        # but it's good to be aware of the label as defined.
        # Django by default does not strip spaces from labels.
        form = HomeForm()
        assert form.fields['title'].label == "    Title "
        # If stripping was intended, the label in forms.py should be "Title "
        # or a custom widget/field would handle it.
        # For now, we test the literal value.

# Example of using Django's TestCase if needed, though pytest-style is preferred for this task.
# class HomeFormDjangoTestCase(TestCase):
#     def test_valid_form(self):
#         form = HomeForm(data={'title': 'Hello', 'artist': 'World'})
#         self.assertTrue(form.is_valid())

#     def test_invalid_form_empty_artist(self):
#         form = HomeForm(data={'title': 'Hello', 'artist': ''})
#         self.assertFalse(form.is_valid())
#         self.assertIn('artist', form.errors)

#     def test_invalid_form_empty_title(self):
#         form = HomeForm(data={'title': '', 'artist': 'World'})
#         self.assertFalse(form.is_valid())
#         self.assertIn('title', form.errors)
