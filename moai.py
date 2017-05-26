#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections
import urllib2
import re
import time
import yaml

# fun hack to order yaml by key
# @todo - master plan is to move from yaml to mongodb
_mapping_tag = yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG
def dict_representer(dumper, data):
    return dumper.represent_dict(data.iteritems())
def dict_constructor(loader, node):
    return collections.OrderedDict(loader.construct_pairs(node))
yaml.add_representer(collections.OrderedDict, dict_representer)
yaml.add_constructor(_mapping_tag, dict_constructor)

# get our data
with open('data.yml', 'r') as stream:
    try:
        data = yaml.load(stream)
    except yaml.YAMLError as exception:
        print 'There was a problem loading the yml file...'
        print(exception)

# find regulatory code changes
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
            print '\t- Found a different code than the one we have, writing ' + str(live_matches[0]) + ' to data.yml'
            data['websites'][website]['dates'][int(time.strftime("%Y%m%d"))] = { 'code' : str(live_matches[0]) }
            with open('data.yml', 'w') as outfile:
                yaml.dump(data, outfile, default_flow_style=False)

    # if we dont find a match
    else:
        print '\t- Did not find any live matches, please check that the regex is current.'


# generate images
import matplotlib
# force matplotlib to not use any Xwindows backend
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
# set global styles
matplotlib.rcParams.update({'font.size': 6})

content = "| Drug | Indication | Generic | Update frequency |"
content += "\n| ---- | ---------- | ------ | ---------------- |"

for website in data['websites']:

    dates = []

    for date in data['websites'][website]['dates']:

        dates.append(str(date))

    X = pd.to_datetime(dates)
    print X
    fig, ax = plt.subplots(figsize=(6,0.4))
    ax.scatter(X, [1]*len(X), marker='v', s=50, color='#306caa')
    fig.autofmt_xdate()

    # turn off unncessary items
    ax.yaxis.set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.xaxis.set_ticks_position('bottom')

    ax.get_yaxis().set_ticklabels([])
    day = pd.to_timedelta("1", unit='D')
    plt.xlim(X[0] - day, X[-1] + day)
    plt.savefig('data/' + website + '.png', bbox_inches='tight')

    content += '\n| [{0}](http://{0})<br>{1} | {2} | {3} | ![{0}](data/{0}.png) |'.format(website, data['websites'][website]['drug']['company'], data['websites'][website]['drug']['indication'], data['websites'][website]['drug']['generic'])


# generate  README.md
f = open('README.md', 'w')
f.write('''
# moai
:moyai: Pharmaceutical competitive intelligence through product website FDA OPDP update frequency.

![Moai](moai.jpg)

Moai /ˈmoʊ.aɪ/ provides competitive intelligence by tracking the unique regulatory code on United States pharmaceutical websites that are mandated by the FDA. This provides insight as to when, and how often, a website is updated.

The below data is free, looking for a complete picture with valuable insights? Please contact us at info@devopsgroup.io to learn more.

{0}
'''.format(content))
f.close()
