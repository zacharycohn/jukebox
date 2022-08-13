Disclaimer: As I say frequently at work, I am not a software engineer. Some of the code contained herein is hacky and gross. This was a hobby project and a fun way to learn some more python, primarily via Googling and StackOverflow. Happy to receive constructive feedback about more efficient/proper ways to do things through Issues and PRs. There's a bit of debug code, a decent amount of commented out code, and some "project management" comments I'm leaving for educational purposes.

# Background
This is a Raspberry Pi powered Jukebox that controls one or more Sonos speakers via NFC tags. [See a demo video of it in action.](https://www.youtube.com/watch?v=HJCB1uUh_KM)

![Jukebox](https://github.com/zacharycohn/jukebox/blob/main/demoimage.jpeg)
*(The lid fits, I just didn't attach it yet.)*

Sometimes I find it inconvenient to pull out my phone/computer to control the music playing on my Sonos, so I decided to build an analog control interface.

I used my Glowforge to lasercut a box and mounted it on the wall, then stuffed a Raspberry Pi 3B inside with an NFC shield. The musicBox.py code listens for an NFC tag (embedded in a jewel case), then plays the appropriate Pandora or Spotify playlist. 

I glued magnets in the jewel case and in the enclosure, so the jewel case snaps into alignment for the nfc reader and holds the jewel case up to show off the album art/what is playing right now. I use the soco python library to interface with my local sonos devices.

This code is built to support multiple jukeboxes syncing to the same remote database.

![Music Library](https://github.com/zacharycohn/jukebox/blob/main/musiclibrary.jpeg)

# Setup
## Software:
- pip3 install beautifulsoup4
- pip3 install soco
- pip3 install pysftp
- This repo comes with the pn532 package to control the NFC hat, but you can also find it on https://www.waveshare.com/wiki/PN532_NFC_HAT#Resources
- Change the values of global variables to fit your Sonos setup and remote database URL.
- Change the sftp info in `syncLocalDBWithRemote()` in musicBox.py and admin_musicBox.py
- The database.txt file included in this repo is just an example. You'll want to replace it with your own NFC IDs, URIs, etc. You can just delete the contents - the admin script will populate it with the right formatting for you.


## Hardware:
- Raspberry pi (I used a 3B+, but any that fit the NFC hat should work)
- Waveshare pn532 NFC hat: https://www.waveshare.com/pn532-nfc-hat.htm
- Use https://en.makercase.com/ to generate an SVG for lasercutting an enclosure to house the pi/NFC reader
- Buy some CD jewel cases from Amazon. I used the thin ones.
- Make album art with https://pixlr.com/
- Use Apple Music to create PDF templates of album art
- Buy these thin/powerful magnets: https://www.kjmagnetics.com/proddetail.asp?prod=DA1 
- Glue magnets in the jewel cases and in your enclosure for the pi/NFC reader
- I used these NFC tags: https://www.amazon.com/gp/product/B07PC3YYM8/ref=crt_ewc_title_oth_1?ie=UTF8&psc=1&smid=A33CLVZLRZ5QMR

# Configuration and Usage
## Step 1:
SSH into your raspberry pi. Either scp the contents of this repo to it or clone the repo directly there.

## Step 2: 
Set up musicbox.py to run when your pi boots up. I use the .bashrc method found here: https://www.dexterindustries.com/howto/run-a-program-on-your-raspberry-pi-at-startup/

Add the following to the end of your .bashrc file:

```
cd ~/jukebox
sudo PYTHONPATH=:/home/pi/.local/lib/python3.9/site-packages python -m musicBox
#sudo python3 -m musicBox.py
```

## Step 3:
Run admin_musicBox.py on your pi. Follow the prompts to associate your NFC tags with pandora stations or spotify playlists (use the Spotify Share URL).

If you don't reboot the pi from the admin script, run `sudo reboot` to reboot the pi.

## Step 4: 
Touch the NFC tag against the reader and jam out to your music.
