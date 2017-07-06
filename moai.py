#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DEVELOPMENT NOTES
-----------------
* Ideally use pyenv to ensure to not break your Python installion https://github.com/pyenv/pyenv#homebrew-on-mac-os-x
* Python v2 is supported - v3 not yet
* Install the missing libraries as defined in provision.sh
"""

import base64
import collections
import datetime
import gzip
import hashlib
import hmac
import pygeoip
import re
import requests
import sys
import time
from urllib import quote
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

if '--skip-changes' not in sys.argv[1:]:

    # download the most recent GeoIPISP.dat file
    url = 'http://download.maxmind.com/download/geoip/database/asnum/GeoIPASNum.dat.gz'
    response = requests.get(url)
    if response.status_code == 200:
        with open('provision/GeoIPASNum.dat.gz', 'wb') as f:
            f.write(response.content)
            f.close()
    inF = gzip.GzipFile('provision/GeoIPASNum.dat.gz', 'rb')
    s = inF.read()
    inF.close()
    outF = file('provision/GeoIPASNum.dat', 'wb')
    outF.write(s)
    outF.close()
    geoip = pygeoip.GeoIP('provision/GeoIPASNum.dat')


    # find regulatory code changes
    print('\nLOOKING FOR CODE CHANGES')
    for indication in data:

        # what indication?
        print('\n' + indication + '\n==============================').upper()

        for website in data[indication]:

            # what website?
            print('\n' + website + '\n------------------------------').upper()

            ###########
            # 80 HTTP #
            ###########
            ###########
            ###########

            print('[HTTP]')
            trys = 0
            while True:
                try:

                    # make the request
                    url = 'http://' + website
                    headers = {'user-agent': 'Moai'}
                    request_80 = requests.get(url, headers=headers, timeout=5)
                    html_content = request_80.text

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
                    if 'server' in request_80.headers:
                        server_match = str(request_80.headers['Server'])
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

                    ##################################
                    # ASN (Autonomous System Number) #
                    ##################################

                    # try and find the most recent asn
                    asn_most_recent =''
                    asn_most_recent_date = ''
                    for date in reversed(data[indication][website]['dates']):
                        if data[indication][website]['dates'][date].has_key('asn'):
                            asn_most_recent = data[indication][website]['dates'][date]['asn']
                            asn_most_recent_date = date
                            break

                    # define the match
                    domain = website.split("//")[-1].split("/")[0]
                    asn_match = geoip.asn_by_name(domain)

                    # handle the match
                    print('[ASN]\nOLD [' + str(asn_most_recent_date) + '][' + str(asn_most_recent) + ']\nNEW [' + str(todays_date) + '][' + asn_match + ']')
                    if str(asn_most_recent) == asn_match:
                        print('* NO CHANGE')
                    else:
                        print('* CHANGE')
                        if todays_date in data[indication][website]['dates']:
                            data[indication][website]['dates'][todays_date].update( { 'asn' : str(asn_match) } )
                        else:
                            data[indication][website]['dates'].update( { todays_date : { 'asn' : str(asn_match) } } )


                    break

                # catch any exceptions
                except requests.exceptions.RequestException as e:
                    print('Exception: ' + str(e))
                finally:
                    trys = trys + 1
                    time.sleep(3)
                    if trys > 2:
                        print('Tried making the request ' + str(trys) + ' times, skipping...')
                        break


            #############
            # 443 HTTPS #
            #############
            #############
            #############

            print('[HTTPS]')
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
                finally:
                    trys = trys + 1
                    time.sleep(3)
                    if trys > 2:
                        print('Tried making the request ' + str(trys) + ' times, skipping...')
                        break

            #########
            # HTTPS #
            #########

            # try and find the most recent https
            https_most_recent =''
            https_most_recent_date = ''
            for date in reversed(data[indication][website]['dates']):
                if data[indication][website]['dates'][date].has_key('https'):
                    https_most_recent = data[indication][website]['dates'][date]['https']
                    https_most_recent_date = date
                    break

            # handle the match
            print('OLD [' + str(https_most_recent_date) + '][' + str(https_most_recent) + ']\nNEW [' + str(todays_date) + '][' + str(https) + ']')
            if str(https_most_recent) == str(https):
                print('* NO CHANGE')
            else:
                print('* CHANGE')
                if todays_date in data[indication][website]['dates']:
                    data[indication][website]['dates'][todays_date].update( { 'https' : str(https) } )
                else:
                    data[indication][website]['dates'].update( { todays_date : { 'https' : str(https) } } )


            #####################################
            # GOOGLE PAGESPEED INSIGHTS MOBILE #
            #####################################
            #####################################
            #####################################

            print('[GOOGLE PAGESPEED INSIGHTS MOBILE]')
            trys = 0
            google_psi_mobile = ''
            while True:
                try:

                    # make the request
                    url = 'https://www.googleapis.com/pagespeedonline/v2/runPagespeed?url=http://' + website + '&strategy=mobile'
                    headers = {'user-agent': 'Moai'}
                    request = requests.get(url, headers=headers, timeout=30)
                    response = request.json()
                    google_psi_mobile = response['ruleGroups']['SPEED']['score']
                    google_psi_mobile_usability = response['ruleGroups']['USABILITY']['score']
                    break

                # catch any exceptions
                except requests.exceptions.RequestException as e:
                    print('Exception: ' + str(e))
                finally:
                    trys = trys + 1
                    time.sleep(3)
                    if trys > 2:
                        print('Tried making the request ' + str(trys) + ' times, skipping...')
                        break

            ######################
            # GOOGLE PSI MOBILE  #
            ######################

            # try and find the most recent google_psi_mobile
            google_psi_mobile_most_recent =''
            google_psi_mobile_most_recent_date = ''
            for date in reversed(data[indication][website]['dates']):
                if data[indication][website]['dates'][date].has_key('google_psi_mobile'):
                    google_psi_mobile_most_recent = data[indication][website]['dates'][date]['google_psi_mobile']
                    google_psi_mobile_most_recent_date = date
                    break

            # handle the match
            print('OLD [' + str(google_psi_mobile_most_recent_date) + '][' + str(google_psi_mobile_most_recent) + ']\nNEW [' + str(todays_date) + '][' + str(google_psi_mobile) + ']')
            if str(google_psi_mobile_most_recent) == str(google_psi_mobile):
                print('* NO CHANGE')
            else:
                print('* CHANGE')
                if todays_date in data[indication][website]['dates']:
                    data[indication][website]['dates'][todays_date].update( { 'google_psi_mobile' : str(google_psi_mobile) } )
                else:
                    data[indication][website]['dates'].update( { todays_date : { 'google_psi_mobile' : str(google_psi_mobile) } } )

            ################################
            # GOOGLE PSI MOBILE USABILITY  #
            ################################

            # try and find the most recent google_psi_mobile_usability
            google_psi_mobile_usability_most_recent =''
            google_psi_mobile_usability_most_recent_date = ''
            for date in reversed(data[indication][website]['dates']):
                if data[indication][website]['dates'][date].has_key('google_psi_mobile_usability'):
                    google_psi_mobile_usability_most_recent = data[indication][website]['dates'][date]['google_psi_mobile_usability']
                    google_psi_mobile_usability_most_recent_date = date
                    break

            # handle the match
            print('OLD [' + str(google_psi_mobile_usability_most_recent_date) + '][' + str(google_psi_mobile_usability_most_recent) + ']\nNEW [' + str(todays_date) + '][' + str(google_psi_mobile_usability) + ']')
            if str(google_psi_mobile_usability_most_recent) == str(google_psi_mobile_usability):
                print('* NO CHANGE')
            else:
                print('* CHANGE')
                if todays_date in data[indication][website]['dates']:
                    data[indication][website]['dates'][todays_date].update( { 'google_psi_mobile_usability' : str(google_psi_mobile_usability) } )
                else:
                    data[indication][website]['dates'].update( { todays_date : { 'google_psi_mobile_usability' : str(google_psi_mobile_usability) } } )


            #####################################
            # GOOGLE PAGESPEED INSIGHTS DESKTOP #
            #####################################
            #####################################
            #####################################

            print('[GOOGLE PAGESPEED INSIGHTS DESKTOP]')
            trys = 0
            google_psi_desktop = ''
            while True:
                try:

                    # make the request
                    url = 'https://www.googleapis.com/pagespeedonline/v2/runPagespeed?url=http://' + website + '&strategy=desktop'
                    headers = {'user-agent': 'Moai'}
                    request = requests.get(url, headers=headers, timeout=30)
                    response = request.json()
                    google_psi_desktop = response['ruleGroups']['SPEED']['score']
                    break

                # catch any exceptions
                except requests.exceptions.RequestException as e:
                    print('Exception: ' + str(e))
                finally:
                    trys = trys + 1
                    time.sleep(3)
                    if trys > 2:
                        print('Tried making the request ' + str(trys) + ' times, skipping...')
                        break

            ######################
            # GOOGLE PSI DESKTOP #
            ######################

            # try and find the most recent google_psi_desktop
            google_psi_desktop_most_recent =''
            google_psi_desktop_most_recent_date = ''
            for date in reversed(data[indication][website]['dates']):
                if data[indication][website]['dates'][date].has_key('google_psi_desktop'):
                    google_psi_desktop_most_recent = data[indication][website]['dates'][date]['google_psi_desktop']
                    google_psi_desktop_most_recent_date = date
                    break

            # handle the match
            print('OLD [' + str(google_psi_desktop_most_recent_date) + '][' + str(google_psi_desktop_most_recent) + ']\nNEW [' + str(todays_date) + '][' + str(google_psi_desktop) + ']')
            if str(google_psi_desktop_most_recent) == str(google_psi_desktop):
                print('* NO CHANGE')
            else:
                print('* CHANGE')
                if todays_date in data[indication][website]['dates']:
                    data[indication][website]['dates'][todays_date].update( { 'google_psi_desktop' : str(google_psi_desktop) } )
                else:
                    data[indication][website]['dates'].update( { todays_date : { 'google_psi_desktop' : str(google_psi_desktop) } } )


            #######
            # MOZ #
            #######
            #######
            #######

            print('[MOZ]')
            trys = 0
            moz_links = ''
            moz_rank = ''
            while True:
                try:
                    # https://github.com/seomoz/SEOmozAPISamples/blob/master/python/mozscape.py
                    # whaaaa? secret key exposed? yes, i know, we'll fix this later. i don't think there are hackers scouring the internet for moz secret keys (no offense)
                    access_key = 'mozscape-b8fab3b953'
                    secret_key = '1e7aa77ad3797e6637c7097f42e4b7aa'
                    expires = int(time.time() + 300)
                    to_sign = '%s\n%i' % (access_key, expires)
                    signature = base64.b64encode(
                        hmac.new(
                            secret_key.encode('utf-8'),
                            to_sign.encode('utf-8'),
                            hashlib.sha1
                        ).digest()
                    )
                    # request_80.url is the final redirected url
                    domain = quote(request_80.url)
                    # columns links = 2048 and mozRank = 16384
                    columns = 2048 + 16384
                    # make the request
                    url = 'http://lsapi.seomoz.com/linkscape/url-metrics/' + domain + '?Cols=' + str(columns) + '&AccessID=' + access_key + '&Expires=' + str(expires) + '&Signature=' + signature
                    headers = {'user-agent': 'Moai'}
                    request = requests.get(url, headers=headers, timeout=30)
                    response = request.json()
                    if 'uid' in response:
                        moz_links = response['uid']
                        moz_rank = response['umrp']
                        moz_rank = str(moz_rank)[:3]
                    else:
                        # moz free tier only allows 1 request every 10 seconds
                        # 5 seconds for good luck as our trusty advisement of 10 seconds is not 100% accurate
                        time.sleep(15)
                        raise requests.exceptions.RequestException(request.text)
                    break

                # catch any exceptions
                except requests.exceptions.RequestException as e:
                    print('Exception: ' + str(e))
                finally:
                    trys = trys + 1
                    time.sleep(3)
                    if trys > 2:
                        print('Tried making the request ' + str(trys) + ' times, skipping...')
                        break

            #############
            # MOZ LINKS #
            #############

            # try and find the most recent moz_links
            moz_links_most_recent =''
            moz_links_most_recent_date = ''
            for date in reversed(data[indication][website]['dates']):
                if data[indication][website]['dates'][date].has_key('moz_links'):
                    moz_links_most_recent = data[indication][website]['dates'][date]['moz_links']
                    moz_links_most_recent_date = date
                    break

            # handle the match
            print('[MOZ LINKS]')
            if str(moz_links) != '':
                print('OLD [' + str(moz_links_most_recent_date) + '][' + str(moz_links_most_recent) + ']\nNEW [' + str(todays_date) + '][' + str(moz_links) + ']')
                if str(moz_links_most_recent) == str(moz_links):
                    print('* NO CHANGE')
                else:
                    print('* CHANGE')
                    if todays_date in data[indication][website]['dates']:
                        data[indication][website]['dates'][todays_date].update( { 'moz_links' : str(moz_links) } )
                    else:
                        data[indication][website]['dates'].update( { todays_date : { 'moz_links' : str(moz_links) } } )

            ############
            # MOZ RANK #
            ############

            # try and find the most recent moz_rank
            moz_rank_most_recent =''
            moz_rank_most_recent_date = ''
            for date in reversed(data[indication][website]['dates']):
                if data[indication][website]['dates'][date].has_key('moz_rank'):
                    moz_rank_most_recent = data[indication][website]['dates'][date]['moz_rank']
                    moz_rank_most_recent_date = date
                    break

            # handle the match
            print('[MOZ RANK]')
            if str(moz_rank) != '':
                print('OLD [' + str(moz_rank_most_recent_date) + '][' + str(moz_rank_most_recent) + ']\nNEW [' + str(todays_date) + '][' + str(moz_rank) + ']')
                if str(moz_rank_most_recent) == str(moz_rank):
                    print('* NO CHANGE')
                else:
                    print('* CHANGE')
                    if todays_date in data[indication][website]['dates']:
                        data[indication][website]['dates'][todays_date].update( { 'moz_rank' : str(moz_rank) } )
                    else:
                        data[indication][website]['dates'].update( { todays_date : { 'moz_rank' : str(moz_rank) } } )


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

content = '<table>'

for indication in data:

    # what indication?
    print('\n' + indication + '\n==============================').upper()

    content += '\n<tr>'
    content += '<td colspan="11"><strong>' + str(indication) + '</strong></td>'
    content += '</tr>'
    content += '\n<tr>'
    content += '<td><sub>Drug \ generic \ company</sub></td>'
    content += '<td><sub>Regulatory code<br/><img src="https://placehold.it/30x5/cc4c02?text=+"></sub></td>'
    content += '<td><sub>HTTPS<br/><img src="https://placehold.it/30x5/fe9929?text=+"></sub></td>'
    content += '<td>:trophy:<br/><img src="https://placehold.it/30x5/FFDF00?text=+"></td>'
    content += '<td>:link:<br/><img src="https://placehold.it/30x5/C0C0C0?text=+"></td>'
    content += '<td>:iphone:<br/><img src="https://placehold.it/30x5/014636?text=+"></td>'
    content += '<td>:wheelchair:<br/><img src="https://placehold.it/30x5/016c59?text=+"></td>'
    content += '<td>:computer:<br/><img src="https://placehold.it/30x5/02818a?text=+"></td>'
    content += '<td><sub>Server<br/><img src="https://placehold.it/30x5/fee391?text=+"></sub></td>'
    content += '<td><sub>ASN<br/><img src="https://placehold.it/30x5/ffffe5?text=+"></sub></td>'
    content += '<td>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</td>'
    content += '</tr>'

    for website in data[indication]:

        # what website?
        print('\n' + website + '\n------------------------------').upper()

        # set the figure size
        ax = plt.figure(figsize=(20,1), dpi=60)
        # set the font size
        matplotlib.rcParams.update({'font.size': 8})
        # qualitative color palette picker
        # http://colorbrewer2.org/#type=qualitative&scheme=Paired&n=10

        # plot code
        for date in data[indication][website]['dates']:
            if 'code' in data[indication][website]['dates'][date]:
                plt.axvline(x=datetime.datetime.strptime(str(date), '%Y%m%d'), color='#cc4c02')

        # plot https
        for date in data[indication][website]['dates']:
            if 'https' in data[indication][website]['dates'][date]:
                plt.axvline(x=datetime.datetime.strptime(str(date), '%Y%m%d'), color='#fe9929')

        # plot server
        for date in data[indication][website]['dates']:
            if 'server' in data[indication][website]['dates'][date]:
                plt.axvline(x=datetime.datetime.strptime(str(date), '%Y%m%d'), color='#fee391')

        # plot asn
        for date in data[indication][website]['dates']:
            if 'asn' in data[indication][website]['dates'][date]:
                plt.axvline(x=datetime.datetime.strptime(str(date), '%Y%m%d'), color='#ffffe5')

        # plot google_psi_mobile
        plot_list = []
        dates_datetime = []
        for date in data[indication][website]['dates']:
            if 'google_psi_mobile' in data[indication][website]['dates'][date]:
                plot_list.append(int(data[indication][website]['dates'][date]['google_psi_mobile']))
                dates_datetime.append(datetime.datetime.strptime(str(date), '%Y%m%d'))
        dates_float = matplotlib.dates.date2num(dates_datetime)
        plt.plot_date(dates_float, plot_list, linestyle='-', xdate=True, ydate=False, color='#014636')

        # plot google_psi_mobile_usability
        plot_list = []
        dates_datetime = []
        for date in data[indication][website]['dates']:
            if 'google_psi_mobile_usability' in data[indication][website]['dates'][date]:
                plot_list.append(int(data[indication][website]['dates'][date]['google_psi_mobile_usability']))
                dates_datetime.append(datetime.datetime.strptime(str(date), '%Y%m%d'))
        dates_float = matplotlib.dates.date2num(dates_datetime)
        plt.plot_date(dates_float, plot_list, linestyle='-', xdate=True, ydate=False, color='#016c59')

        # plot google_psi_desktop
        plot_list = []
        dates_datetime = []
        for date in data[indication][website]['dates']:
            if 'google_psi_desktop' in data[indication][website]['dates'][date]:
                plot_list.append(int(data[indication][website]['dates'][date]['google_psi_desktop']))
                dates_datetime.append(datetime.datetime.strptime(str(date), '%Y%m%d'))
        dates_float = matplotlib.dates.date2num(dates_datetime)
        plt.plot_date(dates_float, plot_list, linestyle='-', xdate=True, ydate=False, color='#02818a')

        # plot moz_links
        plot_list = []
        dates_datetime = []
        for date in data[indication][website]['dates']:
            if 'moz_links' in data[indication][website]['dates'][date]:
                plot_list.append(int(data[indication][website]['dates'][date]['moz_links']))
                dates_datetime.append(datetime.datetime.strptime(str(date), '%Y%m%d'))
        dates_float = matplotlib.dates.date2num(dates_datetime)
        plt.plot_date(dates_float, plot_list, linestyle='-', xdate=True, ydate=False, color='#C0C0C0')

        # plot moz_rank
        plot_list = []
        dates_datetime = []
        for date in data[indication][website]['dates']:
            if 'moz_rank' in data[indication][website]['dates'][date]:
                plot_list.append(float(data[indication][website]['dates'][date]['moz_rank']))
                dates_datetime.append(datetime.datetime.strptime(str(date), '%Y%m%d'))
        dates_float = matplotlib.dates.date2num(dates_datetime)
        plt.plot_date(dates_float, plot_list, linestyle='-', xdate=True, ydate=False, color='#FFDF00')

        # save the figure
        plt.savefig('data/' + website.replace("/","-") + '.png', bbox_inches='tight')
        plt.close('all')


        # get the most recent server
        code = ''
        for date in reversed(data[indication][website]['dates']):
            if 'code' in data[indication][website]['dates'][date]:
                code = data[indication][website]['dates'][date]['code']
                break

        # get the most recent https
        https = ''
        for date in reversed(data[indication][website]['dates']):
            if 'https' in data[indication][website]['dates'][date]:
                https = data[indication][website]['dates'][date]['https']
                if https == 'True':
                    https = ':white_check_mark:'
                else:
                    https = ':x:'
                break

        # get the most recent server
        server = ''
        for date in reversed(data[indication][website]['dates']):
            if 'server' in data[indication][website]['dates'][date]:
                server = data[indication][website]['dates'][date]['server']
                break

        # get the most recent asn
        asn = ''
        for date in reversed(data[indication][website]['dates']):
            if 'asn' in data[indication][website]['dates'][date]:
                asn = data[indication][website]['dates'][date]['asn']
                break

        # get the most recent google_psi_mobile
        google_psi_mobile = ''
        for date in reversed(data[indication][website]['dates']):
            if 'google_psi_mobile' in data[indication][website]['dates'][date]:
                google_psi_mobile = data[indication][website]['dates'][date]['google_psi_mobile']
                break

        # get the most recent google_psi_mobile_usability
        google_psi_mobile_usability = ''
        for date in reversed(data[indication][website]['dates']):
            if 'google_psi_mobile_usability' in data[indication][website]['dates'][date]:
                google_psi_mobile_usability = data[indication][website]['dates'][date]['google_psi_mobile_usability']
                break

        # get the most recent google_psi_desktop
        google_psi_desktop = ''
        for date in reversed(data[indication][website]['dates']):
            if 'google_psi_desktop' in data[indication][website]['dates'][date]:
                google_psi_desktop = data[indication][website]['dates'][date]['google_psi_desktop']
                break

        # get the most recent moz_links
        moz_links = ''
        for date in reversed(data[indication][website]['dates']):
            if 'moz_links' in data[indication][website]['dates'][date]:
                moz_links = data[indication][website]['dates'][date]['moz_links']
                break

        # get the most recent moz_rank
        moz_rank = ''
        for date in reversed(data[indication][website]['dates']):
            if 'moz_rank' in data[indication][website]['dates'][date]:
                moz_rank = data[indication][website]['dates'][date]['moz_rank']
                break

        content += '\n<tr>'
        content += '<td><sub><a href="http://{0}" target="_blank">{0}</a></sub> <br/> <sub>{1}</sub> <br/> <sub>{2}</sub></td>'.format( website , data[indication][website]['drug']['generic'] , data[indication][website]['drug']['company'])
        content += '<td><sub>{0}</sub></td>'.format( code )
        content += '<td><sub><a href="https://www.ssllabs.com/ssltest/analyze.html?d={0}" target="_blank">{1}</a></sub></td>'.format( website , https )
        content += '<td><sub>{0}</sub></td>'.format( moz_rank )
        content += '<td><sub>{0}</sub></td>'.format( moz_links )
        content += '<td><sub><a href="https://developers.google.com/speed/pagespeed/insights/?url={0}&tab=mobile" target="_blank">{1}</a></sub></td>'.format( website , google_psi_mobile )
        content += '<td><sub><a href="https://developers.google.com/speed/pagespeed/insights/?url={0}&tab=mobile" target="_blank">{1}</a></sub></td>'.format( website , google_psi_mobile_usability )
        content += '<td><sub><a href="https://developers.google.com/speed/pagespeed/insights/?url={0}&tab=desktop" target="_blank">{1}</a></sub></td>'.format( website , google_psi_desktop )
        content += '<td><sub>{0}</sub></td>'.format( server )
        content += '<td><sub>{0}</sub></td>'.format( asn )
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

| ![Charles](moai-charles.jpg) | Meet Charles, the moaiBOT. He scours websites daily, looking for changes.<br>Charles likes fishing and long walks on the beach. |
| -- | -- |

Additionally, the following the metrics are captured:

* **Regulatory code**: Gain insight into how often a website is updated
* **HTTPS**: Sadly, many website infrastructures do not provide HTTPS which [provides no data security](https://www.chromium.org/Home/chromium-security/marking-http-as-non-secure) to its visitors
* :trophy: [MozRank](https://moz.com/learn/seo/mozrank) quantifies link popularity and is Moz’s version of Google’s classic PageRank algorithm
* :link: Moz total number of links (juice-passing or not, internal or external) of the final redirected url (http://drug.com > https://www.drug.com)
* :iphone: Google PageSpeed Insights mobile speed score
* :wheelchair: Google PageSpeed Insights mobile usability score
* :computer: Google PageSpeed Insights desktop speed score
* **server**: The HTTP server header provides insight into infrastructure changes
* **ASN**: Autonomous System Number provides insight into data center moves

Looking for a website and workflow management platform that delivers a competitive edge? Give [Catapult](https://github.com/devopsgroup-io/catapult) a *shot*.

The below data is free, looking for a complete picture with valuable insights? Please contact us at info@devopsgroup.io to learn more.
{0}
'''.format(content))
f.close()
