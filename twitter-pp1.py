import datetime
import json
import logging
import os
import sys
import time # to sleep between requests
import twitter
import urllib # to handle downloads

from logging.handlers import RotatingFileHandler

def main() :
	
	# TODO also look into tweepy, see https://stackoverflow.com/questions/42225364/getting-whole-user-timeline-of-a-twitter-user

	# housekeeping stuff
	folder_name = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
	folder_name += "-twitter-pp1"
	if not os.path.exists(folder_name) : os.makedirs(folder_name) 

	initialize_logging(folder_name)
	logging.info("Created folder for this run, \"%s\"" % folder_name)

	# read all the stuff that we need to start the application
	logging.info("Reading and assigning codes to API...")
	codes = None
	with open("../codes.json", "r") as fp : codes = json.load(fp)
	
	api = twitter.Api(
			consumer_key=codes["API key"],
			consumer_secret=codes["API secret key"],
			access_token_key=codes["Access token"],
			access_token_secret=codes["Access token secret"]
			)
	
	logging.info("Result: %s" % api.VerifyCredentials())
	
	# here starts the real fun stuff
	users = ["@Daddy_AnLi"]
	
	# iterate over the users and get tweets; we are also obtaining their tweets as dictionaries,
	# using this module's "AsDict()" method
	for u in users :
		logging.info("Collecting statuses of user \"" + u + "\"...")
		
		# now, here we need a loop, because we can only recover up to 200 statuses per call
		statuses = [ s.AsDict() for s in api.GetUserTimeline(screen_name=u, count=100) ]
		oldest_status_id = statuses[-1]["id"]
		
		logging.info("Collected %d statuses!" % len(statuses))

		# TODO I should probably use tweepy's stuff here, as the Cursor strategy seems better
		while oldest_status_id != None :
			time.sleep(5)
			older_statuses = [ s.AsDict() for s in api.GetUserTimeline(screen_name=u, count=100, max_id=oldest_status_id) ]
			if len(older_statuses) > 1 : # and len(statuses) < 199: # for quick debugging
				oldest_status_id = older_statuses[-1]["id"]
				oldest_created_at = older_statuses[-1]["created_at"]
				statuses.extend( older_statuses[1:] ) # the tweet with id=max_id is also returned...
				logging.info("Collected %d statuses! Oldest status id: %d (%s)" % (len(statuses), oldest_status_id, oldest_created_at))
			else :
				oldest_status_id = None
				logging.info("Status collection finished, reached oldest status. Total number of statuses: %d" % len(statuses))
			
		# filter out retweets (s["text"] starts with "RT")
		logging.info("Removing retweets...")
		statuses = [ s for s in statuses if not s["text"].startswith("RT") ]
		logging.info("A total of %d tweets have been retained" % len(statuses))

		# create folder(s) for the user
		# to divide media content by category, save into different folders
		user_folder = os.path.join(folder_name, u[1:])
		if not os.path.exists(user_folder) : os.makedirs(user_folder) 
		
		animated_gif_folder = os.path.join(user_folder, "animated_gifs")
		if not os.path.exists(animated_gif_folder) : os.makedirs(animated_gif_folder)
		image_folder = os.path.join(user_folder, "images")
		if not os.path.exists(image_folder) : os.makedirs(image_folder)
		video_folder = os.path.join(user_folder, "videos")
		if not os.path.exists(video_folder) : os.makedirs(video_folder)
		
		statuses_with_media = [ s for s in statuses if "media" in s ]
		logging.info("Of those, %d contain media!" % len(statuses_with_media))

		# and now, let's try to find out the type of media, and eventually download it
		for i, s in enumerate(statuses_with_media) :

			tweet_id = s["id"]
			media = s["media"][0] # it's a list of media, but there is usually only one
			logging.info("Media status #%d/%d (type: %s, url: %s): \"%s\"" % (i+1, len(statuses_with_media), media["type"], media["media_url"], s["text"]))
			
			# download!
			if media["type"] == "video" :
				
				logging.info("Working on video for status %d" % tweet_id)
				# get all the variants
				video_variants = [ v for v in media["video_info"]["variants"] if "bitrate" in v ]

				# select the one with the highest bitrate
				best_variant = max(video_variants, key=lambda v : v["bitrate"])
				logging.info("Selected video variant with bitrate %d" % best_variant["bitrate"]) 
				
				# let's attempt a direct download
				url = best_variant["url"]
				extension = best_variant["content_type"]
				file_name = str(tweet_id) + "." + extension[6:] # skip "video/" in "video/mp4" etc.
				file_name = os.path.join(video_folder, file_name)
			
			elif media["type"] == "photo" :
				
				logging.info("Working on photo for status %d" % tweet_id)
				url = media["media_url"]
				extension = url[-3:]
				file_name = str(tweet_id) + "." + extension
				file_name = os.path.join(image_folder, file_name) 
			
			elif media["type"] == "animated_gif" :
				
				logging.info("Working on animated gif for status %d" % tweet_id )
				url = media["video_info"]["variants"][0]["url"]
				extension = url[-3:]
				file_name = str(tweet_id) + "." + extension
				file_name = os.path.join(animated_gif_folder, file_name)
			
			# attempt download, then sleep a little, just to be sure we are not overreaching
			logging.info("Downloading media to file \"%s\"..." % file_name)
			urllib.request.urlretrieve(url, file_name)
			time.sleep(5)
			
		logging.info("Work on user \"%s\" complete." % u)

	return

def initialize_logging(folderName=None) :
	logger = logging.getLogger()
	logger.setLevel(logging.DEBUG)
	formatter = logging.Formatter('[%(levelname)s %(asctime)s] %(message)s') 

	# the 'RotatingFileHandler' object implements a log file that is automatically limited in size
	if folderName != None :
		fh = RotatingFileHandler( os.path.join(folderName, "log.log"), mode='a', maxBytes=100*1024*1024, backupCount=2, encoding=None, delay=0 )
		fh.setLevel(logging.DEBUG)
		fh.setFormatter(formatter)
		logger.addHandler(fh)

	ch = logging.StreamHandler()
	ch.setLevel(logging.INFO)
	ch.setFormatter(formatter)
	logger.addHandler(ch)

	return

if __name__ == "__main__" :
	sys.exit( main() )
