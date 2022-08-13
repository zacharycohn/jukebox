#!/usr/bin/env python3

################
# Setup: 
# pip3 install beautifulsoup4
# pip3 install soco
# pip3 install pysftp
#
# change the directory paths in syncLocalDBWithRemote()


#Todos: 
# + incorporate getPandoraURI and getSpotifyURI into a single script
# + sync remote playlist db locally periodically
# + script to upload playlist db to remote
# - add "replace db entry with something new" functionality
# - Remove playlist and decommission an NFC tag. 
# + figure out how to get NFC tag ID into the DB.
# - modify so this script can run on the pi or on your local computer (and paste in NFC id)
################

import os
import time #this can be removed, it's only used for debug purposes.
import pysftp

#Sonos/soco related imports
import soco
from soco.plugins import sharelink
from soco.snapshot import Snapshot


#BeautifulSoup - used for getting the database.txt file from the webserver
import requests


# NFC Reader 
import RPi.GPIO as GPIO
from pn532 import *

remoteDBUrl = 'https://zaccohn.com/misc/audio/musicbox/database.txt'
databaseFile = "database.txt"


def main():
	keepGoing = 1

	while keepGoing == 1:
		print("Menu of options: ")
		print("1. Add a new playlist or station.")
		print("2. Manually sync database.")
		print("3. Replace an existing NFC tag with something new.") # TODO
		print("4. Remove playlist and decommission an NFC tag.") # TODO
		option = input("Please enter the number of the action you'd like to take: ")

		if option == "1":
			addEntry()
		elif option == "2":
			syncDatabase()

		keepGoing = int(input("Do another (1), or sync and quit (0)? "))
		if keepGoing == 0:
			syncLocalDBWithRemote()
			os.system('systemctl reboot -i')

		


###### Options
def addEntry():

	print("Please tap NFC tag for this playlist now.")
	tag = readNFCTag()


	service = input("Which service would you like to use? Pandora or Spotify? ")
	if service.lower() == "pandora":
		getPandoraURI(tag)
	elif service.lower() == "spotify":
		getSpotifyURI(tag)


def syncDatabase():
	option = input("Do you want to: \n1. Pull the remote db down \n2. Upload the local db to remote?\n")

	if option == "1":
		getRemoteDatabase()
	elif option == "2":
		syncLocalDBWithRemote()


###### Utilities

def getRemoteDatabase():
	global remoteDBUrl
	global databaseFile

	remotedb = requests.get(remoteDBUrl).text

	with open(databaseFile, "w") as dbFile:
		dbFile.write(remotedb)

	print("Pulled remote database down to local.")


def syncLocalDBWithRemote():
	global databaseFile
	
	remoteUser = input("What's the sftp username? ")
	pwd = input("What's the sftp password? ")

	with pysftp.Connection('zaccohn.com', username=remoteUser, password=pwd) as sftp:

		with sftp.cd('zaccohn.com/misc/audio/musicbox/'):
			sftp.put(databaseFile)
	
	print("Local file sync'd to remote.")


def readNFCTag():
	print("Reading the NFC tag")
	uid = ""
	keepGoing = 1

	try:
		pn532 = PN532_SPI(debug=False, reset=20, cs=4)

		ic, ver, rev, support = pn532.get_firmware_version()
		print('Found PN532 with firmware version: {0}.{1}'.format(ver, rev))

		# Configure PN532 to communicate with MiFare cards
		pn532.SAM_configuration()

		print('Waiting for RFID/NFC card...')
		while keepGoing == 1:
			# Check if a card is available to read
			rawuid = pn532.read_passive_target(timeout=0.5)
			#print('.', end="")

			#if there is a tag and it hasn't taken an action on that tag yet.
			if rawuid is not None:
				#read and assemble the hex UID into a consistent string 
				for i in rawuid:
					bit = str(hex(i)).lower()[2:]
					if len(bit) == 1:
						bit = "0" + bit
					uid += bit + ":"

				#chop off the last : added in the loop above
				uid = uid[:-1]

				print("found a card: " + uid)
				keepGoing = 0

			#if no card is available.
			if rawuid is None:
				print("nothin' here " + time.strftime("%H:%M:%S", time.localtime()))
				continue

	except Exception as e:
		print("readNFCTag() problem: " + e)
	finally:
		GPIO.cleanup()
	
	print("returning UID: " + uid)
	return uid


def getPandoraURI(tag):
	speakers = soco.discover()

	print("Here's a list of available speakers: ")
	for val in speakers:
		print(val.player_name)

	targetSpeaker = input("Which speaker would you like to target? ")

	for val in speakers:
		if str(val.player_name.lower()) == targetSpeaker.lower():
			speaker = val
			break

	info = speaker.get_current_track_info()
	print ("Now listening to: " + info["title"] + " by " + info["artist"])

	stationName = input("What is this station called? ")


	snap = Snapshot(speaker)
	snap.snapshot()

	playlist = tag + ",pandora," + stationName + "," + snap.media_uri + "," + snap.media_metadata + "\n" 

	database = open(databaseFile, "a")
	database.write(playlist + "\n")
	database.close()


def getSpotifyURI(tag):
	playlistURL = input("Please paste Spotify Share URL now: ")
	media_uri = sharelink.SpotifyShare().canonical_uri(playlistURL)

	playlistName = input("What is this playlist called? ")

	playlist = tag + ",spotify," + playlistName + "," + media_uri + "\n"

	database = open(databaseFile, "a")
	database.write(playlist + "\n")
	database.close()






if __name__ == "__main__":
	main()