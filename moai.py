#!/usr/bin/env python

import urllib2
import re
import time
import yaml

with open('data.yml', 'r') as stream:
    try:
        data = yaml.load(stream)
    except yaml.YAMLError as exception:
        print 'There was a problem loading the yml file...'
        print(exception)

for website in data['websites']:
    # what website?
    print website

    # get the html
    html_content = urllib2.urlopen('http://' + website).read()
    # search for the code using the regex defined per website
    live_matches = re.findall(data['websites'][website]['regex'], html_content);

    # get the most recent date
    most_recent_date = data['websites'][website]['dates'].keys()[-1]
    # get the most recent data code
    most_recent_date_code = data['websites'][website]['dates'][most_recent_date]['code']

    # if we find a match
    if len(live_matches) > 0:
        if str(most_recent_date_code) == str(live_matches[0]):
            print '\t- The most recent code that we have ' + str(most_recent_date) + ':' + str(most_recent_date_code) + ' matches what we just found ' + str(live_matches[0])
        else:
            print '\t- Found a different code than the one we have, writing to data.yml'
            data['websites'][website]['dates'][int(time.strftime("%Y%m%d"))] = { 'code' : str(live_matches[0]) }
            with open('data.yml', 'w') as outfile:
                yaml.dump(data, outfile, default_flow_style=False)

    # if we dont find a match
    else:
        print '\t- Did not find any live matches, please check that the regex is current.'
