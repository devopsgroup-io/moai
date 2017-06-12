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


# define globals
todays_date = int(time.strftime("%Y%m%d"))


# get our data
with open('data.yml', 'r') as stream:
    try:
        data = yaml.load(stream)
    except yaml.YAMLError as exception:
        print('There was a problem loading the yml file...')
        print(exception)


# find regulatory code changes
print('\nLOOKING FOR CODE CHANGES')
for indication in data:

    # what indication?
    print('\n' + indication + '\n==============================').upper()

    for website in data[indication]:

        # what website?
        print('\n' + website + '\n------------------------------').upper()

        # try and get the html
        trys = 0
        while True:
            try:

                # make the request
                url = 'http://' + website
                headers = {'user-agent': 'Moai'}
                request = requests.get(url, headers=headers, timeout=5)
                html_content = request.text

                ############
                # FDA CODE #
                ############

                # try and find the most recent code
                code_most_recent =''
                code_most_recent_date = ''
                for date in reversed(data[indication][website]['dates']):
                    if data[indication][website]['dates'][date].has_key('code'):
                        code_most_recent = data[indication][website]['dates'][date]['code']
                        code_most_recent_date = date
                        break

                # define the match
                code_match = re.findall(data[indication][website]['regex'], re.sub('<[^<]+?>', '', html_content));

                # handle the match
                if len(code_match) > 0:
                    print('[CODE]\nOLD [' + str(code_most_recent_date) + '][' + str(code_most_recent) + ']\nNEW [' + str(todays_date) + '][' + str(code_match[0]) + ']')
                    if str(code_most_recent) == str(code_match[0]):
                        print('* NO CHANGE')
                    else:
                        print('* CHANGE')
                        if todays_date in data[indication][website]['dates']:
                            data[indication][website]['dates'][todays_date].update( { 'code' : str(code_match[0]) } )
                        else:
                            data[indication][website]['dates'].update( { todays_date : { 'code' : str(code_match[0]) } } )
                else:
                    print('* NO MATCH (please confirm correct regex)')

                ###############
                # HTTP SERVER #
                ###############

                # try and find the most recent server
                server_most_recent =''
                server_most_recent_date = ''
                for date in reversed(data[indication][website]['dates']):
                    if data[indication][website]['dates'][date].has_key('server'):
                        server_most_recent = data[indication][website]['dates'][date]['server']
                        server_most_recent_date = date
                        break

                # define the match
                if 'server' in request.headers:
                    server_match = str(request.headers['Server'])
                else:
                    server_match = ''

                # handle the match
                print('[SERVER]\nOLD [' + str(server_most_recent_date) + '][' + str(server_most_recent) + ']\nNEW [' + str(todays_date) + '][' + server_match + ']')
                if str(server_most_recent) == server_match:
                    print('* NO CHANGE')
                else:
                    print('* CHANGE')
                    if todays_date in data[indication][website]['dates']:
                        data[indication][website]['dates'][todays_date].update( { 'server' : str(server_match) } )
                    else:
                        data[indication][website]['dates'].update( { todays_date : { 'server' : str(server_match) } } )


                break

            # catch any exceptions
            except requests.exceptions.RequestException as e:
                print('Exception: ' + str(e))
            finally:
                trys = trys + 1
                time.sleep(3)
                if trys == 2:
                    print('Tried getting the content ' + str(trys) + ' times, skipping...')
                    break

exit


# determine if there is a 443 listener
print('\nLOOKING FOR HTTPS SUPPORT')
for indication in data:

    # what indication?
    print('\n' + indication + '\n==============================').upper()

    for website in data[indication]:

        # what website?
        print('\n' + website + '\n------------------------------').upper()

        # try and request https
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
                print('Exception: ' + str(e))
                https = False
            finally:
                trys = trys + 1
                time.sleep(3)
                if trys == 2:
                    print('Tried validating HTTPS support ' + str(trys) + ' times, skipping...')
                    break

        # try and find the most recent https
        https_most_recent =''
        https_most_recent_date = ''
        for date in reversed(data[indication][website]['dates']):
            if data[indication][website]['dates'][date].has_key('https'):
                https_most_recent = data[indication][website]['dates'][date]['https']
                https_most_recent_date = date
                break

        # handle the match
        print('[HTTPS]\nOLD [' + str(https_most_recent_date) + '][' + str(https_most_recent) + ']\nNEW [' + str(todays_date) + '][' + str(https) + ']')
        if str(https_most_recent) == str(https):
            print('* NO CHANGE')
        else:
            print('* CHANGE')
            if todays_date in data[indication][website]['dates']:
                data[indication][website]['dates'][todays_date].update( { 'https' : str(https) } )
            else:
                data[indication][website]['dates'].update( { todays_date : { 'https' : str(https) } } )


# write changes to data.yml
print('\nWRITING CHANGES TO THE DATA.YML FILE')
with open('data.yml', 'w') as outfile:
    yaml.dump(data, outfile, default_flow_style=False)


# generate images and README content
print('\nGENERATING CONTENT')
import matplotlib
# force matplotlib to not use any Xwindows backend
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
# set global styles
matplotlib.rcParams.update({'font.size': 6})

content = '<table>'

for indication in data:

    # what indication?
    print('\n' + indication + '\n==============================').upper()

    content += '\n<tr>'
    content += '<td colspan="3"><strong>' + str(indication) + '</strong></td>'
    content += '</tr>'
    content += '\n<tr>'
    content += '<td>Drug \ generic \ company</td><td>HTTPS</td><td>Update frequency</td>'
    content += '</tr>'

    for website in data[indication]:

        # what website?
        print('\n' + website + '\n------------------------------').upper()

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

        # get the most recent https
        for date in reversed(data[indication][website]['dates']):
            if 'https' in data[indication][website]['dates'][date]:
                https = data[indication][website]['dates'][date]['https']
                if https == 'True':
                    https = ':white_check_mark:'
                else:
                    https = ':x:'
                break

        # get the most recent server
        for date in reversed(data[indication][website]['dates']):
            if 'server' in data[indication][website]['dates'][date]:
                server = data[indication][website]['dates'][date]['server']
                break

        content += '\n<tr>'
        content += '<td><a href="http://{0}" target="_blank">{0}</a><br/>{1}<br/>{2}</td>'.format( website , data[indication][website]['drug']['generic'] , data[indication][website]['drug']['company'] )
        content += '<td><a href="https://www.ssllabs.com/ssltest/analyze.html?d={0}" target="_blank">{1}</a><br/>{2}</td>'.format( website , https, server )
        content += '<td><img src="data/{0}.png"/></td>'.format( website.replace("/","-") )
        content += '</tr>'

content += '\n</table>'

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
