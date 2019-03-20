from django.shortcuts import render
from django.views.generic import TemplateView
from pages.forms import HomeForm
from . import hitpredictor

def home(request):

	track = request.POST.get("track")
	artist = request.POST.get("artist")
	banner = ""

	if track and artist:

		try:
			perc, trackName, artistName = hitpredictor.main(track, artist)
		except:
			args = {"error":"Sorry :( your song is not available on Spotify servers, please check if there are any spelling mistakes; or the information you provided is correct."}
			return render(request, "homeInput.html",args)	

		banner = "IT'S A HIT!" if perc >=50 else "It might not do well. "

		perc = str(perc) + "%"

		args = {"banner":banner, "perc":perc, "trackName":trackName, "artistName": artistName}

	else:
		#args = {"banner":"and I'll predict if", "perc":"", "trackName":"any song given","artistName":" you, is gonna end up"}
		args = {}

		return render(request,"homeInput.html",args)

	return render(request,"home.html",args)

def about(request):
	return render(request,"about.html",{})

def homeInput(request):
	return render(request,"homeInput.html",{})

def contact(request):
	return render(request,"contact.html",{})			