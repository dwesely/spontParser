# -*- coding: utf-8 -*-
"""
Created on Tue Jul 19 20:53:29 2016

Parses xml from spontaneanation wiki pages to pull out episode titles and guest names
Source data: http://spontaneanation.wikia.com/wiki/Special:Export

Export pages of "spontaneanation episodes" category as SPONTANEANATION+Wikia-episodes.xml

Output files contain wikimedia formatted table of guests, and csv table of
running appearance counts by episode.

@author: Wesely
"""

import re
import requests
#from BeautifulSoup import BeautifulStoneSoup
from sys import version

VERBOSE = True

def onlyTheBest():
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
        self.number        = float(number)
        self.title         = title
        self.guests        = set([])
        self.question      = ''
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
        
    def get_max_episode_gap(self):
        """Go through the list of episodes and find the biggest break"""
        if len(self.episodes) < 2:
            return -1
        episode_list = sorted([episode.number for episode in self.episodes])
        return max([(j-i,i,j) for i, j in zip(episode_list[:-1], episode_list[1:])] )
        

def get_Guest_Object(name,link):
    if name not in Guest.guests_dict:
        guestObj = Guest(name,link)
    else:
        guestObj = Guest.guests_dict.get(name)
    return guestObj

def get(pages=[], category = False, curonly=True):
    #http://stackoverflow.com/questions/14512372/exporting-wikipedia-with-python
    link = "http://spontaneanation.wikia.com/wiki/Special:Export?action=submit"
    params = {}
    if pages:
        params["pages"] = "\n".join(pages)
    if category:
        params["addcat"] = 1
        params["catname"] = category

    if curonly:
        params["curonly"] = 1

    headers = {"User-Agent":"Wiki Downloader -- Python %s, contact: @danwesely on twitter" % version}
    r = requests.post(link, headers=headers, data=params)
    return r.text

def getToEdit(pages=[], category = False, curonly=True):
    #http://stackoverflow.com/questions/14512372/exporting-wikipedia-with-python
    link = "http://spontaneanation.wikia.com/wiki/Category:Spontaneanation_Guests?action=edit&section=1"
    params = {}
    if pages:
        params["pages"] = "\n".join(pages)
    if category:
        params["addcat"] = 1
        params["catname"] = category

    if curonly:
        params["curonly"] = 1

    headers = {"User-Agent":"BeepBopBoop, I'm a robot -- Python %s, contact: @danwesely on twitter" % version}
    r = requests.post(link, headers=headers, data=params)
    return r.text


def main():

    episodeList = []
    
    #set output file for new wiki download
    xmlFilename = 'SPONTANEANATION+Wikia-episodes.xml'
    
    #get new episode list
    exportPages = get(category="Spontaneanation Episodes")
    savePages = False
    pageList = []
    for line in exportPages.split("\n"):
        print(line)
        if savePages and '<' not in line:
            pageList.append(line.strip(' \n\t\r'))
        elif '<textarea name="pages" cols="40" rows="10">' in line:
            savePages = True
        elif savePages:
            #the last page has </textarea> next to it, strip and save
            pageList.append(re.findall(r'^[^<]+',line)[0])
            break
        
    #get new episode xml
    episodePages = get(pages=pageList)
    with open(xmlFilename,'w') as newDownload:
        print(episodePages)
        newDownload.write(episodePages.encode('utf-8'))
    
    #Open file for results summary
    homefile = open('spont_wiki_home.txt','w')
    statsfile = open('spont_wiki_stats.csv','w')
    
    #Compile regex
    episodeTitleRegex = re.compile(r'''
        ^.*Ep.\s*               # Bullet
        (\d+.?\d*)              # Episode number
        \s*-\s*                 # Separator
        [[]+([^\]|]+)           # Episode title
        ''', re.VERBOSE)
    
    #Parse wiki file
    episodesfile = open(xmlFilename,'r+')
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
                if VERBOSE:
                    print(line)
            elif episodePageFound and 'Episode List' in line and '==' in line:
                    episodeListFound = True
                    if VERBOSE:
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
                #Get the episode title
                title = parseEpisodeTitle(line)
                thisEpisode = get_Episode_Object(0,cleanTitleString(title))
                if VERBOSE:
                    if thisEpisode:
                        print('This episode: #{} {}'.format(thisEpisode.number, thisEpisode.title))
                    else:
                        print(line)
            elif line.startswith("      <comment"):
                continue
            elif thisEpisode and '|question]] was' in line:
                #Save the episode's question
                thisQuestion = re.sub(r'.*question]] was ','',line).strip("&quot;'.")
                thisEpisode.question = thisQuestion
            elif 'Guests/Improvisors' in line:
                #Time to start parsing guests
                guestListFound = True
            elif guestListFound and '*' in line:
                #This is a listed guest
                myname = cleanNameString(line)
                if re.match('[\[]',myname):
                    mylink = myname
                    myname = cleanNameString(re.search(r'[[]+([^\|\]]*)',myname).group(1).strip(' \t\n\r'))
                else:
                    mylink = '[[{}]]'.format(myname)
                print('This guest: {}, {}'.format(myname, mylink))
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
    for guest in sorted(Guest.guests_dict.values(), key=lambda x: len(x.episodes), reverse=True):
        sortedList = sorted(guest.episodes, key=lambda x: x.number)
        if len(guest.episodes)>1:
            homefile.write('\n|-\n| {} || [[{}|{}]] || [[{}|{}]] || {:.0f}'.format(guest.link,sortedList[0].title,sortedList[0].number,sortedList[-1].title,sortedList[-1].number,len(sortedList)))
        elif sortedList:
            homefile.write('\n|-\n| {} || [[{}|{}]] || [[{}|{}]] || {:.0f}'.format(guest.link,sortedList[0].title,sortedList[0].number,sortedList[0].title,sortedList[0].number,1))
        elif VERBOSE:
            print(guest.name)
        if VERBOSE:
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
    
    print('Printing wiki stats...')
    statsfile.write('\n\nList of Episode Volume Per Guest as A Function of Episode\nEpisode')
    for guest in Guest.guests_dict.values():
        statsfile.write(',{}'.format(guest.name))
    for episode in sorted(Episode.episodes_dict.values(), key=lambda x: x.number):
        statsfile.write('\n{:.1f}'.format(episode.number))
        for guest in Guest.guests_dict.values():
            guestEpisodesSoFar = sum(guestisode.number <= episode.number for guestisode in guest.episodes)
            statsfile.write(',{:.1f}'.format(guestEpisodesSoFar))
    
    statsfile.write('\nMax Episodes Between Guesting:')
    for guest in Guest.guests_dict.values():
        guestEpisodeMaxGap = guest.get_max_episode_gap()
        statsfile.write(','+'{}'.format(guestEpisodeMaxGap).replace(',',';'))
    #TODO: Average episodes between guesting
    #statsfile.write('\nAvg Episodes Between Guesting:')
    
    episodesfile.close()
    homefile.close()
    statsfile.close()
    
    print('Special thanks: {}'.format(onlyTheBest()))
    
    print('Complete.')

if __name__ == '__main__':
    main()
