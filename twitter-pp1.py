import json
import logging
import sys
import time # to sleep between requests
import twitter
import urllib # to handle downloads

def main() :
	
	# housekeeping stuff
	initialize_logging()

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
		statuses = [ s.AsDict() for s in api.GetUserTimeline(screen_name=u, count=100) ]
		
		# TODO filter retweets (s["text"] starts with "RT")
		# TODO create folder for the user
		# TODO divide media content by category, save into different folders
		
		logging.info("Collected %d statuses!" % len(statuses))
		#statuses_with_media = [ s for s in statuses if s.media != None ]
		statuses_with_media = [ s for s in statuses if "media" in s ]
		logging.info("Of those, %d contain media!" % len(statuses_with_media))
		
		# and now, let's try to find out the type of media, and eventually download it
		for i, s in enumerate(statuses_with_media) :
			media = s["media"][0] # it's a list of media, but there is usually only one
			logging.info("Media status #%d (type: %s, url: %s): \"%s\"" % (i, media["type"], media["media_url"], s["text"]))
			#logging.info( str(media) )
			
			# download!
			if media["type"] == "video" :
				# get all the variants
				video_variants = [ v for v in media["video_info"]["variants"] if "bitrate" in v ]
				#for v in video_variants :
				#	logging.info(str(v))
				# select the one with the highest bitrate
				best_variant = max(video_variants, key=lambda v : v["bitrate"])
				logging.info("Selected video variant with bitrate %d" % best_variant["bitrate"]) 
				
				# let's attempt a direct download
				url = best_variant["url"]
				extension = best_variant["content_type"]
				file_name = "video-" + str(i) + "." + extension[6:] # skip "video/" in "video/mp4" etc.
				logging.info("Downloading video to file \"%s\"..." % file_name)
				urllib.request.urlretrieve(url, file_name)
				time.sleep(5)

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
