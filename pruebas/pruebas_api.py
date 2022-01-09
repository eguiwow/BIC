import requests
import json
import datetime
import sys

sys.path.insert(0, '/home/eguiwow/BIC/bic/datacentre')

from sck_api import generate_tracks_time

#"2021-05-26T00:01:00"
#"2021-05-26T15:01:00"

generate_tracks_time("2021-05-26T00:01:00", "2021-05-26T21:00:00", "10s", 14061)