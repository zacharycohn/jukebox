#!/usr/bin/env python3

####
# Setup
# pip3 install beautifulsoup4
# pip3 install soco
# pip3 install pysftp
# manually install the raspberry pi pn532 python package. Get that from https://www.waveshare.com/wiki/PN532_NFC_HAT#Resources
#
# Buy some CD jewel cases from Amazon. I used the thin ones.
# Make album art with https://pixlr.com/
# Use Apple Music to create PDF templates of album art
# buy these magnets: https://www.kjmagnetics.com/proddetail.asp?prod=DA1 
# glue magnets in the jewel cases and in your container for the pi/NFC reader
#
# I used https://en.makercase.com/ to generate an SVG for lasercutting a box to house the pi/NFC reader
####


#### TODO's ####
# General
# + play a Spotify playlist (http://docs.python-soco.com/en/latest/api/soco.plugins.sharelink.html or https://github.com/avantrec/soco-cli#albums-and-playlists)
# + play a Spotify song
# + determine whether it's pandora/spotify then do the right thing
# + get speaker groupings working
# + replace for loop discovery with http://docs.python-soco.com/en/latest/api/soco.discovery.html
# + periodically sync databases
# + Make an improvementin setSpeakerGroup to avoid unnecessary joining and unjoining
# + Refactor setSpeakerGroup

# NFC stuff: https://www.waveshare.com/wiki/PN532_NFC_HAT#Resources
# + read NFC tag
# + add NFC tags to playlist db
# - special NFC tag to trigger a manually db sync (probably not going to do this)



from operator import truediv
import threading
import time #this is only used for debug and SyncSchedule. If you aren't using SyncSchedule, this can be removed.
import os

## Control the Sonos with python: https://github.com/SoCo/SoCo
import soco 
from soco.snapshot import Snapshot
from soco.plugins import sharelink

#Scrape webserver to sync the database 
from bs4 import BeautifulSoup 
import requests

# NFC Reader 
import RPi.GPIO as GPIO
from pn532 import *

speakerGroup = ["Kitchen", "Living Room"] # the Sonos names of the speakers you want to use
databaseFile = "database.txt" # name of the local database text file
# You could remove remoteDB code out if you don't want to sync multiple devices/sync db off your raspberry pi.
remoteDBUrl = 'https://zaccohn.com/misc/audio/musicbox/database.txt' #URL of the remote database text file. 


# Uncomment when there are multiple devices to keep in sync with remote database
# also uncomment the line in main()
# class SyncSchedule(object):
# 	def __init__(self, interval=1):
# 		self.interval = interval

# 		thread = threading.Thread(target=self.run, args=())
# 		thread.daemon = True
# 		thread.start()

# 	def run(self):
#		# sync every 4 hours
# 		seconds = 14400

# 		while True: 
# 			time.sleep(seconds)
# 			syncWithRemoteDB()
# 			print("going to sleep for " + str(seconds) + " seconds.")


class NFCReader(object):
	def __init__(self, interval=1):
		self.interval = interval

		thread = threading.Thread(target=self.run, args=())
		thread.daemon = True
		thread.start()

	def run(self):
		nfcActive = 0
		global speakerGroup

		try:
			pn532 = PN532_SPI(debug=False, reset=20, cs=4)

			ic, ver, rev, support = pn532.get_firmware_version()
			print('Found PN532 with firmware version: {0}.{1}'.format(ver, rev))

			# Configure PN532 to communicate with MiFare cards
			pn532.SAM_configuration()

			print('Waiting for RFID/NFC card...')
			while True:
				uid = ""

				# Check if a card is available to read
				rawuid = pn532.read_passive_target(timeout=0.5)
				#print('.', end="")

				#if there is a card and it hasn't taken an action on that card yet.
				if rawuid is not None and nfcActive == 0:
					for i in rawuid:
						bit = str(hex(i)).lower()[2:]
						if len(bit) == 1:
							bit = "0" + bit
						uid += bit + ":"

					uid = uid[:-1]
					nfcActive = 1
					#print("found a card: " + uid)
					writeActivityLog("found a card: " + uid)
					playNFCStream(uid)

				#if no card is available.
				if rawuid is None:
					
					# if an NFC tag is removed. 
					if nfcActive == 1:
						# if it's already paused or stopped, don't do anything
						devices = {device.player_name: device for device in soco.discover()}
						deviceStatus = devices[speakerGroup[0]].get_current_transport_info()
						if deviceStatus == "PAUSED_PLAYBACK" or deviceStatus == "STOPPED":
							continue
						# pause the speakers
						else:
							#print("NFC removed. Pausing Sonos.")
							writeActivityLog("NFC removed. Pausing Sonos.")
							devices[speakerGroup[0]].pause()
							nfcActive = 0
					else:
						print("nothin' here " + time.strftime("%H:%M:%S", time.localtime()))
						continue

					# If you want to be able to remove the NFC tag without pausing the music.
				# 	nfcActive = 0
				# 	print("nothin' here " + time.strftime("%H:%M:%S", time.localtime()))
				# 	continue

		except Exception as e:
			print(e)
			with open("errorlog.txt", "a") as dbFile:
				dbFile.write(time.strftime("%H:%M:%S", time.localtime()))
				dbFile.write(": ")
				dbFile.write(str(e))
				dbFile.write("\n\n*****************\n\n")
			os.system('systemctl reboot -i')
		finally:
			GPIO.cleanup()






def main():
	# the sleep is not necessary, but since the program auto-runs when you log into the pi, i found it useful to give myself
	# some time to kill the program when SSH'ing in.
	time.sleep(3) 

	syncWithRemoteDB()
	# uncomment if you want to sync with remote on a regular schedule. Important if you have multiple jukeboxes
	#sync = SyncSchedule() 
	reader = NFCReader()

	while True:
		continue


def playNFCStream(nfcUID):

	playlists = getPlaylists()
	speaker = getSpeaker()
	setSpeakerGroup()

	x = 0
	for i in playlists:
		dbNFC = str(i[0]).lower()
		
		if dbNFC == nfcUID:
			if identifyService(playlists[x]) == "spotify":
				playSpotifyPlaylist(playlists[x])
			elif identifyService(playlists[x]) == "pandora":
				playPandoraPlaylist(playlists[x])
			else:
				print("uhhhh whoops need to build this")
			
			break

		x = x + 1


# def playStream():
	#this function is deprecated and is no longer used. 
	#it was replaced by playNFCStream

	# playlists = getPlaylists()
	# speaker = getSpeaker()

	# printPlaylists()

	# selection = int(input("Which number would you like to listen to? "))

	# setSpeakerGroup()
	# if identifyService(playlists[selection]) == "spotify":
	# 	print("do some spotify stuff")
	# 	playSpotifyPlaylist(playlists[selection][2])
	# elif identifyService(playlists[selection]) == "pandora":
	# 	print("do some pandora stuff")
	# 	playPandoraPlaylist(playlists[selection])
	# else:
	# 	print("uhhhh whoops need to build this")

def playSpotifyPlaylist(playlists):

	playlistURL = playlists[3]

	media_uri = sharelink.SpotifyShare().canonical_uri(playlistURL)

	speaker = getSpeaker()
	speaker.clear_queue()

	sharelink.ShareLinkPlugin(speaker).add_share_link_to_queue(media_uri, position=1,as_next=True)


	speaker.play_from_queue(0, start=True)
	#print("Playing the Spotify playlist.")
	writeActivityLog("Playing Spotify: " + playlists[2])

def playPandoraPlaylist(playlists):
	speaker = getSpeaker()
	speaker.clear_queue()

	media_uri = playlists[3]
	media_metadata = playlists[4]

	speaker.play_uri(media_uri, media_metadata, start=True)

	#print("Playing your Pandora jams")
	writeActivityLog("Playing Pandora: " + playlists[2])


# Maybe delete this since it lives in the admin script now? 
# def addToDatabase():
# 	#only works with Pandora right now

# 	speaker = getSpeaker()
	
# 	text = input("What is this station called? ")

# 	snap = Snapshot(speaker)  #create snapshot class
# 	snap.snapshot()           #take a snapshot of current state

# 	playlist = text + "," + snap.media_uri + "," + snap.media_metadata

# 	database = open(databaseFile, "a")
# 	database.write(playlist + "\n")
# 	database.close()


###
# Utilities
###

# def printPlaylists():

# 	playlists = getPlaylists()

# 	x = 0
# 	for p in playlists:
# 		print(str(x) + ". " + p[1])
# 		x = x + 1

# def printCurrentInfo():
# 	global speakerGroup
# 	speaker = getSpeaker()
# 	info = speaker.get_current_track_info()
# 	print ("Now listening to: " + info["title"] + " by " + info["artist"] + " on " + speakerGroup[0] + " speaker.")

def writeActivityLog(msg):
	with open("activitylog.txt", "a") as dbFile:
		dbFile.write(time.strftime("%H:%M:%S", time.localtime()))
		dbFile.write(": ")
		dbFile.write(msg)

def identifyService(playlists):
	result = playlists[1]

	return result

def syncWithRemoteDB():
	global remoteDBUrl
	global databaseFile

	remotedb = requests.get(remoteDBUrl).text

	with open(databaseFile, "w") as dbFile:
		dbFile.write(remotedb)

	print("Remote database sync complete.")


#####
# Setters
#####


def setSpeakerGroup():
	global speakerGroup

	# get a dict of devices
	devices = {device.player_name: device for device in soco.discover()}
	numOfSpeakersInGroup = len(devices[speakerGroup[0]].group.members)

	# this is hacky, but if the main speaker is in a group
	# that is the same size as the group it's supposed to be in, 
	# it assumes its in the right size and does nothing. 
	# This works for my setup and is a nice speed boost, 
	# but it may not work for your setup. 
	if numOfSpeakersInGroup != len(speakerGroup):
		print("unjoin some stuff")
		for speaker in speakerGroup:
			print("Unjoin " + speaker)
			devices[speaker].unjoin()
			devices[speaker].stop()

		for speaker in speakerGroup:
			for apparatus in devices:
				if speaker == apparatus and speaker != speakerGroup[0]:
					print("Joining " + apparatus)
					devices[apparatus].join(devices[speakerGroup[0]])	
					break
		




#######DEPRECATED#######
# keeping it for now until the replacement proves itself worthy.
# this was an inefficient hot mess of similar sounding variable names.
########################

# def oldsetSpeakerGroup():
# 	global speakerGroup 

# 	config = open("config.txt", "r")
# 	speakersNameList = config.read().rstrip().split(",")
# 	config.close()


# 	speakersList = []
# 	speakers = soco.discover()

# 	devices = {device.player_name: device for device in soco.discover()}
# 	devicesLength = len(devices['Living Room'].group.members)

# 	# match the list of devices to the string list of speaker names
# 	for n in speakersNameList:
# 		for s in speakers:
# 			if s.player_name == n:
# 				speakersList.append(s)
# 				break
	
# 	speakerName = speakersList[0].player_name	

#	print("speakerNameListLen: " + str(len(speakersNameList)))
#	print("devicesLength: " + str(devicesLength))

	# if len(speakersNameList) != devicesLength:
	# 	# we aren't in our standard configuration, so ungroup everything and start over
	# 	speakersList[0].unjoin()

	# 	#if there's more than one speaker in config, group an infinite number of speakers
	# 	if len(speakersList) > 1:
	# 		length = len(speakersList)
	# 		x = 1
	# 		while x < length:
	# 			#print("x: " + str(x) + " adding: " + speakersList[x].player_name)
	# 			speakersList[x].unjoin()
	# 			speakersList[x].join(speakersList[0])
	# 			x = x + 1


#####
# Getters
#####

def getPlaylists():
	global databaseFile

	database = open(databaseFile, "r")
	playlists = []

	for p in database:
		playlists.append(p.split(","))

	database.close()

	return playlists

def getSpeaker():
	global speakerGroup

	# speakers = soco.discover()
	# for val in speakers:
	# 	if str(val.player_name) == speakerName:
	# 		speaker = val
	# 		break

	speaker = soco.discovery.by_name(speakerGroup[0])
	#print("speaker: " + str(speaker))

	return speaker





if __name__ == "__main__":
	main()