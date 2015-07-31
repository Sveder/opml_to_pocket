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

from pocket import *
from config import *

class TimeoutedPocket(Pocket):
   @staticmethod
   def _post_request(url, payload, headers):
      global pocket_timeout
      r = None
      if pocket_timeout > 0:
         r = requests.post(url, data=payload, headers=headers, timeout=pocket_timeout)
      else:
         r = requests.post(url, data=payload, headers=headers)
      return r
