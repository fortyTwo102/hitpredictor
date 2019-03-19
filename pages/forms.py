from django import forms


class HomeForm(forms.Form):

	title = forms.CharField(label="    Title ")
	artist = forms.CharField(label="Artist ")


