#!/usr/bin/env python
# encoding: utf-8

###########################################################################
##                                                                       ##
##  o2p Version 0.5                                                      ##
##  Â© Copyright Moritz Marquardt 2015                                    ##
##  Licensed under MIT License: http://choosealicense.com/licenses/mit/  ##
## --------------------------------------------------------------------- ##
##  o2p is a Python script which takes an OPML file containing links to  ##
##  RSS feeds and pushes the feed items to http://getpocket.com/.        ##
##  Done for: https://www.codersclan.net/ticket/1135.                    ##
##                                                                       ##
###########################################################################

import opml, feedparser, jsonpickle, timeouted_pocket

from colorama import init, Fore, Back, Style
init()

import sqlite3, calendar, time, re, sys, signal, os
import config


def get_timestamp( utc_date ):
   "Get the UNIX timestamp from a tuple"
   timestamp = calendar.timegm(utc_date)
   return timestamp


def parse_outline( o ):
   "Parses an OPML outline element and pushes the RSS feeds to Pocket"
   global sql_feeds_count, sql_new_count, json_failed_items, json_failed_feeds, sql_status_string

   if ( len(o) == 0 and o.xmlUrl ): # Element is a single RSS feed
      f = None
      try:
         # Parse and push to Pocket
         f = feedparser.parse(o.xmlUrl)
         if hasattr(f.feed, "title"):
            print(Fore.CYAN + Style.BRIGHT + "[INFO] Processing feed: " + Style.RESET_ALL + f.feed.title + Style.DIM + " [" + o.xmlUrl + "]" + Style.RESET_ALL)
         else:
            print(Fore.CYAN + Style.BRIGHT + "[INFO] Processing feed: " + Style.RESET_ALL + Style.DIM + o.xmlUrl + Style.RESET_ALL)
         for i in f.entries:
            try:
               latest_timestamp = 0
               if (hasattr(i, "created_parsed")):
                  latest_timestamp = get_timestamp(i.created_parsed)
               if (hasattr(i, "published_parsed")):
                  latest_timestamp = get_timestamp(i.published_parsed)
               if (hasattr(i, "updated_parsed")):
                  latest_timestamp = get_timestamp(i.updated_parsed)

               if (latest_timestamp == 0):
                  raise Exception("No timestamp supplied by feed.")

               if ( latest_timestamp > config.min_time and latest_timestamp > last_check ): # Added since last scan
                  print(Fore.CYAN + Style.BRIGHT + "[INFO] Submitting item to pocket: " + Style.RESET_ALL + i.title + Style.DIM + " [" + i.link + "]" + Style.RESET_ALL);

                  try:
                     p.add(i.link, title=i.title, time=latest_timestamp)
                     sql_new_count += 1
                  except timeouted_pocket.RateLimitException:
                     print(Fore.RED + Style.BRIGHT + "[ERROR] Rate limit exceeded. " + Style.RESET_ALL + Style.DIM + "https://getpocket.com/developer/docs/rate-limits" + Style.RESET_ALL)
                     sql_status_string = "rate limit exceeded"
                     write_database()
                     exit(4)
                  except KeyboardInterrupt:
                     print(Fore.YELLOW + Style.BRIGHT + "[WARNING] Interrupted by user." + Style.RESET_ALL)
                     sql_status_string = "interrupted"
                     write_database()
                     exit(130)
                  except:
                     if hasattr(i, "title"):
                        print(Fore.YELLOW + Style.BRIGHT + "[WARNING] Could not post element to pocket: " + Style.RESET_ALL + Style.DIM + i.title)
                     else:
                        print(Fore.YELLOW + Style.BRIGHT + "[WARNING] Could not post element to pocket:" + Style.RESET_ALL)
                        print("  " + Style.DIM + str(i))
                     print("  " + str(sys.exc_info()[0]))
                     print("  -> " + str(sys.exc_info()[1]) + Style.RESET_ALL)
                     sql_status_string = "done with errors"
                     json_failed_items += jsonpickle.encode(i, unpicklable=False, make_refs=False) + ","

            except KeyboardInterrupt:
               print(Fore.CYAN + Style.BRIGHT + "[INFO] Interrupted by user." + Style.RESET_ALL)
               sql_status_string = "interrupted"
               write_database()
               exit(130)

            except SystemExit:
               raise

            except:
               if hasattr(i, "title"):
                  print(Fore.YELLOW + Style.BRIGHT + "[WARNING] Invalid element: " + Style.RESET_ALL + Style.DIM + i.title)
               else:
                  print(Fore.YELLOW + Style.BRIGHT + "[WARNING] Invalid element:" + Style.RESET_ALL)
                  print("  " + Style.DIM + str(i))
               print("  " + str(sys.exc_info()[0]))
               print("  -> " + str(sys.exc_info()[1]) + Style.RESET_ALL)
               sql_status_string = "done with errors"
               json_failed_items += jsonpickle.encode(i, unpicklable=False, make_refs=False) + ","

         sql_feeds_count += 1

      except KeyboardInterrupt:
         print(Fore.CYAN + Style.BRIGHT + "[INFO] Interrupted by user." + Style.RESET_ALL)
         sql_status_string = "interrupted"
         write_database()
         exit(130)

      except SystemExit:
         raise

      except:
         print(Fore.YELLOW + Style.BRIGHT + "[WARNING] Could not process feed: " + Style.RESET_ALL + Style.DIM + o.xmlUrl + Style.RESET_ALL)
         print("  " + Style.DIM + str(sys.exc_info()[0]))
         print("  -> " + str(sys.exc_info()[1]) + Style.RESET_ALL)
         sql_status_string = "done with errors"
         json_failed_feeds += jsonpickle.encode({"url": o.xmlUrl, "feed": f.feed}, unpicklable=False, make_refs=False) + ","
   elif len(o) > 0: # Element has children
      for i in o:
         parse_outline(i)
   else: # Element does not have an RSS URL or children
      print(Fore.CYAN + Style.BRIGHT + "[INFO] OPML Element is empty: " + Style.RESET_ALL + Style.DIM + str(o) + Style.RESET_ALL)

# Database helpers
def write_database():
    global json_failed_feeds, json_failed_items
    sql_scan_end_time = get_timestamp(time.gmtime(time.time()))
    json_failed_feeds = re.sub(r",$", "", json_failed_feeds)
    json_failed_items = re.sub(r",$", "", json_failed_feeds)
    sql_status_extras = "{\"failedFeeds\":[" + json_failed_feeds + "],\"failedItems\":[" + json_failed_items + "]}"
    try:
       dbc.executemany("INSERT INTO log (scan_start_time, scan_end_time, new_count, feeds_count, status_string, status_extras) VALUES(?, ?, ?, ?, ?, ?)", [(sql_scan_start_time, sql_scan_end_time, sql_new_count, sql_feeds_count, sql_status_string, sql_status_extras)])
       db.commit()
       db.close()
       print(Fore.CYAN + Style.BRIGHT + "[INFO] Database written." + Style.RESET_ALL)
    except:
       print(Fore.RED + Style.BRIGHT + "[ERROR] Could not insert log entry to database!"  + Style.RESET_ALL)
       print("  " + Style.DIM + str(sys.exc_info()[0]))
       print("  -> " + str(sys.exc_info()[1])  + Style.RESET_ALL)
       exit(2)

sql_scan_start_time = get_timestamp(time.gmtime(time.time()))
sql_new_count = 0
sql_feeds_count = 0
sql_status_string = "done"
json_failed_feeds = ""
json_failed_items = ""

# Connect to SQLite 3
db = None
dbc = None
try:
   if not os.path.isfile(config.sqlite_path):
      raise Exception("Can't find the sqlite file.")

   db = sqlite3.connect(config.sqlite_path)
   dbc = db.cursor()
   dbc.execute("CREATE TABLE IF NOT EXISTS log (scan_start_time TIMESTAMP NOT NULL, scan_end_time TIMESTAMP NOT NULL, new_count INT NOT NULL, feeds_count INT NOT NULL, status_string VARCHAR(32) NOT NULL, status_extras MEDIUMTEXT NOT NULL)")
   dbc.execute("SELECT scan_start_time FROM log ORDER BY scan_start_time DESC LIMIT 1")
   last_check = dbc.fetchone()
   if (last_check != None):
      last_check = last_check[0]
   else:
      last_check = 0



except:
   print(Fore.RED + Style.BRIGHT + "[ERROR] Could not connect to SQLite 3 database!" + Style.RESET_ALL)
   print("  " + Style.DIM + str(sys.exc_info()[0]))
   print("  -> " + str(sys.exc_info()[1]) + Style.RESET_ALL)
   sql_status_string = "failed"
   write_database()
   exit(2)

# Login to Pocket
p = timeouted_pocket.TimeoutedPocket(config.pocket_consumer_key, config.pocket_access_token)

# Parse OPML file
try:
   outline = opml.parse(config.opml_path)

except:
   print(Fore.RED + Style.BRIGHT + "[ERROR] Could not parse OPML file!" + Style.RESET_ALL)
   print("  " + Style.DIM + str(sys.exc_info()[0]))
   print("  -> " + str(sys.exc_info()[1]) + Style.RESET_ALL)
   sql_status_string = "failed"
   write_database()
   exit(1)

# Push OPML feeds to Pocket
parse_outline(outline)
write_database()
exit(0)
