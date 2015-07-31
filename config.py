###########################################################################
##                                                                       ##
##  o2p Version 0.2                                                      ##
##  Licensed under MIT License: http://choosealicense.com/licenses/mit/  ##
## --------------------------------------------------------------------- ##
##  o2p is a Python script which takes an OPML file containing links to  ##
##  RSS feeds and pushes the feed items to http://getpocket.com/.        ##
##  Done for: https://www.codersclan.net/ticket/1135.                    ##
##                                                                       ##
###########################################################################

# URL to the OPML file to parse. HTTPS is currently not supported.
opml_path = "opml.xml"

# Only fetch items newer than this time. Only relevant for first execution if you only want to import new items to Pocket.
# Create UNIX timestamp here: http://www.gaijin.at/olsutc.php
min_time = 0

# Path to .sqlite file for logs
sqlite_path = "./o2p.sqlite"

# Pocket API login details.
# Get a consumer key by creating a new app at http://getpocket.com/developer/
# Get access token here: http://reader.fxneumann.de/plugins/oneclickpocket/auth.php
pocket_consumer_key = ""
pocket_access_token = ""

# Timeout for requests to pocket. Set to 0 for infinite timeout.
pocket_timeout = 15
