#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DEVELOPMENT NOTES
-----------------
* Ideally use pyenv to ensure to not break your Python installion https://github.com/pyenv/pyenv#homebrew-on-mac-os-x
* Python v2 is supported - v3 not yet
* Install the missing libraries as defined in provision.sh
"""

import collections
import re
import requests
import sys
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
        print('There was a problem loading the yml file...')
        print(exception)

"""
# find regulatory code changes
print('\nLOOKING FOR CODE CHANGES')
for indication in data:

    # what indication?
    print('\n' + indication)

    for website in data[indication]:

        # what website?
        print(website)

        # try and get the html
        trys = 0
        while True:
            try:

                # make the request
                url = 'http://' + website
                headers = {'user-agent': 'Moai'}
                html_content = requests.get(url, headers=headers, timeout=5).text

                # search for the code using the regex defined per website
                live_matches = re.findall(data[indication][website]['regex'], re.sub('<[^<]+?>', '', html_content));

                # get the most recent date with a code
                for date in reversed(data[indication][website]['dates']):
                    if data[indication][website]['dates'][date].has_key('code'):
                        most_recent_date = date
                        break
                    else:
                        most_recent_date =''
                # get the most recent data code
                if data[indication][website]['dates'][most_recent_date].has_key('code'):
                    most_recent_date_code = data[indication][website]['dates'][most_recent_date]['code']
                else:
                    most_recent_date_code = ''

                # if we find a match
                if len(live_matches) > 0:
                    if str(most_recent_date_code) == str(live_matches[0]):
                        print('\t- The most recent code that we have [' + str(most_recent_date) + '][' + str(most_recent_date_code) + '] matches what we just found [' + str(live_matches[0]) + ']')
                    else:
                        print('\t- Found a different code than the one we have, writing [' + str(live_matches[0]) + '] to data.yml')
                        data[indication][website]['dates'][int(time.strftime("%Y%m%d"))] = { 'code' : str(live_matches[0]) }
                        with open('data.yml', 'w') as outfile:
                            yaml.dump(data, outfile, default_flow_style=False)

                # if we dont find a match
                else:
                    print('\t- Did not find any live matches, please check that the regex is current.')

                break

            # catch any exceptions
            except requests.exceptions.RequestException as e:
                print('\t- Exception: ' + str(e))
            finally:
                trys = trys + 1
                time.sleep(3)
                if trys == 2:
                    print('\t- Tried getting the content ' + str(trys) + ' times, skipping...')
                    break
"""

# determine if there is a 443 listener
print('\nLOOKING FOR HTTPS SUPPORT')
for indication in data:

    # what indication?
    print('\n' + indication)

    for website in data[indication]:

        # what website?
        print(website)

        # try and get the html
        trys = 0
        https = False
        while True:
            try:

                # make the request
                url = 'https://' + website
                headers = {'user-agent': 'Moai'}
                requests.get(url, headers=headers, timeout=5)
                https = True
                break

            # catch any exceptions
            except requests.exceptions.RequestException as e:
                print('\t- Exception: ' + str(e))
                https = False
            finally:
                trys = trys + 1
                time.sleep(3)
                if trys == 2:
                    print('\t- Tried validating HTTPS support ' + str(trys) + ' times, skipping...')
                    break

        # get the most recent date
        most_recent_date = data[indication][website]['dates'].keys()[-1]
        # get the most recent https status
        if data[indication][website]['dates'][most_recent_date].has_key('https'):
            most_recent_date_https = data[indication][website]['dates'][most_recent_date]['https']
        else:
            most_recent_date_https = ''

        if str(most_recent_date_https) == str(https):
            print('\t- The most recent https status that we have [' + str(most_recent_date) + '][' + str(most_recent_date_https) + '] matches what we just found [' + str(https) + ']')
        else:
            print('\t- Found a different https status than the one we have, writing [' + str(https) + '] to data.yml')
            if data[indication][website]['dates'].has_key(int(time.strftime("%Y%m%d"))) and data[indication][website]['dates'][int(time.strftime("%Y%m%d"))].has_key('code'):
                data[indication][website]['dates'][int(time.strftime("%Y%m%d"))] = { 'code' : data[indication][website]['dates'][int(time.strftime("%Y%m%d"))]['code'], 'https' : str(https) }
            else:
                data[indication][website]['dates'][int(time.strftime("%Y%m%d"))] = { 'https' : str(https) }
            with open('data.yml', 'w') as outfile:
                yaml.dump(data, outfile, default_flow_style=False)


# generate images and README content
print('\nGENERATING IMAGES')
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
    content += '\n| Drug | Company | Generic | HTTPS | Update frequency |'
    content += '\n| ---- | ------- | ------- | ----- | ---------------- |'

    for website in data[indication]:

        # what website?
        print(website)

        dates = []

        for date in data[indication][website]['dates']:
            if data[indication][website]['dates'][date].has_key('code'):
                dates.append(str(date))

        X = pd.to_datetime(dates)
        print(X)
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

        # get the most recent date with https status
        for date in reversed(data[indication][website]['dates']):
            if data[indication][website]['dates'][date].has_key('https'):
                https = data[indication][website]['dates'][date]['https']
                if https == 'True':
                    https = ':white_check_mark:'
                else:
                    https = ':x:'
                break

        content += '\n| [{0}](http://{0}) | {1} | {2} | [{3}](https://{0}) | ![{4}](data/{4}.png) |'.format( website , data[indication][website]['drug']['company'] , data[indication][website]['drug']['generic'] , https , website.replace("/","-") )


# generate README.md
f = open('README.md', 'w')
f.write('''
# moai
:moyai: Pharmaceutical competitive intelligence through product website FDA OPDP update frequency.

![Moai](moai.jpg)

Moai /ˈmoʊ.aɪ/ provides competitive intelligence by tracking the unique regulatory code on United States pharmaceutical websites that are mandated by the FDA. This provides insight as to when, and how often, a website is updated.

HTTPS is also tracked. Sadly, many website infrastructures do not provide HTTPS and subsequently [provides no data security](https://www.chromium.org/Home/chromium-security/marking-http-as-non-secure) to its visitors. Here's a shameless plug for our website and workflow management platform [Catapult](https://github.com/devopsgroup-io/catapult), which enforces best practice security.

| ![Charles](moai-charles.jpg) | Meet Charles, the moaiBOT. He scours websites daily, looking for changes.<br>Charles likes fishing and long walks on the beach. |
| -- | -- |

The below data is free, looking for a complete picture with valuable insights? Please contact us at info@devopsgroup.io to learn more.
{0}
'''.format(content))
f.close()
