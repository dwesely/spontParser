# -*- coding: utf-8 -*-
"""
Created on Tue Jul 19 20:53:29 2016

Parses xml from spontaneanation wiki pages to pull out episode titles and guest names
Source data: http://spontaneanation.wikia.com/wiki/Special:Export

Export pages of "spontaneanation episodes" category as SPONTANEANATION+Wikia-episodes.xml

@author: Wesely
"""

import re

VERBOSE = False

def simplyTheBest():
    return 'Eban Schletter'

def cleanNameString(str):
    # Correct minor formatting issues with name strings
    cleanedStr = str.replace('*','').replace('&quot;','"').replace(', Jr',' Jr.').replace(', Sr',' Sr.').replace('r.','r').replace(' ,',',').strip(' \t\n\r')
    if VERBOSE and str != cleanedStr:
        print('({}) -> ({})'.format(str,cleanedStr))
    return cleanedStr

def cleanTitleString(str):
    # Correct minor formatting issues with title strings
    cleanedStr = str.replace('\xe2\x80\x99',"'")
    return cleanedStr

def parseEpisodeTitle(str):
    return re.search(r'(?<=\>)[^<]*',str).group(0)

class Episode:
    episodes_dict = {}
    def __init__(self, number, title):
        self.number        = int(number)
        self.title         = title
        self.guests        = set([])
        self.link          = '[[{}]]'.format(title)
        Episode.episodes_dict[title] = self

def get_Episode_Object(number,title):
    if title not in Episode.episodes_dict:
        episodeObj = Episode(number,title)
    else:
        episodeObj = Episode.episodes_dict.get(title)
    return episodeObj

class Guest:
    guests_dict = {}
    def __init__(self, name, link):
        self.name          = name
        self.episodes      = set([])
        if link:
            self.link      = link
        else:
            self.link      = '[[{}]]'.format(name)
        Guest.guests_dict[name] = self

def get_Guest_Object(name,link):
    if name not in Guest.guests_dict:
        guestObj = Guest(name,link)
    else:
        guestObj = Guest.guests_dict.get(name)
    return guestObj

episodeList = []
guestList   = []

#Open file for results summary
homefile = open('spont_wiki_home.txt','w')

#Compile regex
textWithParens     = re.compile(r'(?:[^,(]|\([^)]*\))+')

episodeTitleRegex = re.compile(r'''
    ^.*Ep.\s*               # Bullet
    (\d+)                   # Episode number
    \s*-\s*                 # Separator
    [[]+([^\]|]+)           # Episode title
    ''', re.VERBOSE)

#Parse wiki file
episodesfile = open('SPONTANEANATION+Wikia-episodes.xml','r+')
print('Parsing episode list...')
allpages = re.split(r'<page>',episodesfile.read())
episodePageFound = False
episodeListFound = False
for page in allpages:
    alllines = re.split(r'\n',page)
    for line in alllines:
        thisEpisode = None
        if '<title>Episodes</title>' in line:
            episodePageFound = True
            print(line)
        elif episodePageFound and 'Episode List' in line and '==' in line:
                episodeListFound = True
                print(line)
        elif episodeListFound:
            if '*' in line:
                matches = re.search(episodeTitleRegex,line)
                if matches:
                    thisEpisode = Episode(matches.group(1),cleanTitleString(matches.group(2)))
                    if thisEpisode:
                        episodeList.append(thisEpisode)
                elif line:
                    break
episodesfile.close()

missingEpisodeList = []

episodesfile = open('SPONTANEANATION+Wikia-episodes.xml','r+')
print('Parsing guest list...')
allpages = re.split(r'<page>',episodesfile.read())
for page in allpages:
    title          = ''
    guest          = ''
    myname         = ''
    mylink         = ''
    thisGuest      = None
    thisEpisode    = None
    guestListFound = False
    
    alllines = re.split(r'\n',page)
    for line in alllines:
        thisGuest = None
        if '<title>' in line and 'Episode List' not in line:
            title = parseEpisodeTitle(line)
            thisEpisode = get_Episode_Object(0,cleanTitleString(title))
            if thisEpisode:
                print('This episode:',thisEpisode.number, thisEpisode.title)
            else:
                print(line)
        elif line.startswith("      <comment"):
            continue
        elif 'Guests/Improvisors' in line:
            guestListFound = True
        elif guestListFound and '*' in line:
            myname = cleanNameString(line)
            if re.match('[\[]',myname):
                mylink = myname
                myname = cleanNameString(re.search(r'[[]+([^\|\]]*)',myname).group(1).strip(' \t\n\r'))
            else:
                mylink = '[[{}]]'.format(myname)
            print('This guest:', myname, mylink)
            thisGuest = get_Guest_Object(myname, mylink)
            if thisEpisode and thisGuest:
                thisEpisode.guests.add(thisGuest)
                thisGuest.episodes.add(thisEpisode)
            if thisEpisode.number == 0:
                missingEpisodeList.append(thisEpisode.title)
        elif guestListFound and line:
            #No longer the guest list, skip the rest
            guestListFound = False
            continue

homefile.write('\n==== Table of Guest Appearances ====\n{| border="1" class="wikitable sortable"\n!  Guest\n!  Earliest episode\n!  Latest Episode\n!  Total Episode Count')
for guest in Guest.guests_dict.values():
    sortedList = sorted(guest.episodes, key=lambda x: x.number)
    if len(guest.episodes)>1:
        homefile.write('\n|-\n| {} || [[{}|{}]] || [[{}|{}]] || {:.0f}'.format(guest.link,sortedList[0].title,sortedList[0].number,sortedList[-1].title,sortedList[-1].number,len(sortedList)))
    elif sortedList:
        homefile.write('\n|-\n| {} || [[{}|{}]] || [[{}|{}]] || {:.0f}'.format(guest.link,sortedList[0].title,sortedList[0].number,sortedList[0].title,sortedList[0].number,1))
    else:
        print(guest.name)
    print('Guest name: {}'.format(guest.link))
    for episode in sortedList:
        print('  -Episode #{}: {}'.format(episode.number,episode.title))
homefile.write('\n|}')

if missingEpisodeList:
    print('Missing the following episodes:')
    for episode in missingEpisodeList:
        print(episode)

print('*{} episodes identified.'.format(len(Episode.episodes_dict.values())))
print('*{} guests identified.'.format(len(Guest.guests_dict.values())))

episodesfile.close()
homefile.close()

print('Special thanks: {}'.format(simplyTheBest()))

print('Complete.')