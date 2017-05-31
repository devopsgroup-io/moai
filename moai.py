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
for indication in data:
        
    # what indication?
    print indication

    for website in data[indication]:

        # what website?
        print website

        # get the html
        request = urllib2.Request('http://' + website, headers={'User-Agent' : "Moai"})
        html_content = urllib2.urlopen(request).read()
        # search for the code using the regex defined per website
        live_matches = re.findall(data[indication][website]['regex'], html_content);

        # get the most recent date
        most_recent_date = data[indication][website]['dates'].keys()[-1]
        # get the most recent data code
        most_recent_date_code = data[indication][website]['dates'][most_recent_date]['code']

        # if we find a match
        if len(live_matches) > 0:
            if str(most_recent_date_code) == str(live_matches[0]):
                print '\t- The most recent code that we have ' + str(most_recent_date) + ':' + str(most_recent_date_code) + ' matches what we just found ' + str(live_matches[0])
            else:
                print '\t- Found a different code than the one we have, writing ' + str(live_matches[0]) + ' to data.yml'
                data[indication][website]['dates'][int(time.strftime("%Y%m%d"))] = { 'code' : str(live_matches[0]) }
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

content = ''

for indication in data:

    content += '\n'
    content += '\n### ' + str(indication)
    content += '\n| Drug | Company | Generic | Update frequency |'
    content += '\n| ---- | ------- | ------- | ---------------- |'

    for website in data[indication]:

        dates = []

        for date in data[indication][website]['dates']:

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
        plt.savefig('data/' + website.replace("/","-") + '.png', bbox_inches='tight')

        plt.close('all')
        
        content += '\n| [{0}](http://{0}) | {1} | {2} | ![{3}](data/{3}.png) |'.format(website, data[indication][website]['drug']['company'], data[indication][website]['drug']['generic'], website.replace("/","-"))


# generate  README.md
f = open('README.md', 'w')
f.write('''
# moai
:moyai: Pharmaceutical competitive intelligence through product website FDA OPDP update frequency.

![Moai](moai.jpg)

Moai /ˈmoʊ.aɪ/ provides competitive intelligence by tracking the unique regulatory code on United States pharmaceutical websites that are mandated by the FDA. This provides insight as to when, and how often, a website is updated.

| ![Charles](moai-charles.jpg) | Meet Charles, the moaiBOT. He scours websites daily, looking for changes.<br>Charles likes fishing and long walks on the beach. |
| -- | -- |

The below data is free, looking for a complete picture with valuable insights? Please contact us at info@devopsgroup.io to learn more.
{0}
'''.format(content))
f.close()
