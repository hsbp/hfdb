#!/usr/bin/env python

import requests, time, sys, json, re
from lxml.html.soupparser import fromstring
from datetime import date, timedelta

PROXIES = {'http': 'http://localhost:8123/'}
HEADERS =  { 'User-agent': 'Mozilla Firefox/37.7' }

def fetch(url, retries=5, ignore=[], params=None):
    try:
        if params:
            r=requests.POST(url, params=params, proxies=PROXIES, headers=HEADERS)
        else:
            r=requests.get(url, proxies=PROXIES, headers=HEADERS)
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout), e:
        if e == requests.exceptions.Timeout:
            retries = min(retries, 1)
        if retries>0:
            time.sleep(4*(6-retries))
            f=fetch_raw(url, retries-1, ignore=ignore, params=params)
        else:
            raise ValueError("failed to fetch %s" % url)
    if r.status_code >= 400 and r.status_code not in [504, 502]+ignore:
        logger.warn("[!] %d %s" % (r.status_code, url))
        r.raise_for_status()
    return r.text

def getdevkey(calendarid):
    root=fromstring(fetch('https://www.google.com/calendar/embed?showTitle=0&showNav=0&showDate=1&showPrint=1&showTabs=1&showCalendars=0&mode=AGENDA&height=300&wkst=2&bgcolor=%%23ffffff&src=%s&color=%%23182C57&ctz=Etc%%2FGMT' % calendarid))
    s = root.xpath('//script')[2].xpath('.//text()')[0]
    if s.startswith("function _onload() {window._init(") and s.endswith(");}"):
        return json.loads(s[33:-3])['developerKey']
    raise ValueError("could not load developerKey")

def getentries(calandarid, devkey, days=30):
    start = date.today().isoformat()
    end = (date.today() + timedelta(days=days)).isoformat()
    url='https://clients6.google.com/calendar/v3/calendars/%s/events?calendarId=%s&singleEvents=true&timeZone=UTC%%2FGMT&maxAttendees=1&maxResults=250&sanitizeHtml=true&timeMin=%sT00%%3A00%%3A00Z&timeMax=%sT00%%3A00%%3A00Z&key=%s' % (calendarid, calendarid, start, end, devkey)
    while True:
        resp = json.loads(fetch(url))
        for sched in resp['items']:
            sched.update({'tz': resp['timeZone'], 'updated': resp['updated']})
            yield sched
        if not 'nextPageToken' in resp:
            break
        url = 'https://clients6.google.com/calendar/v3/calendars/%s/events?calendarId=%s&singleEvents=true&timeZone=UTC%%2FGMT&maxAttendees=1&maxResults=250&sanitizeHtml=true&timeMin=%sT00%%3A00%%3A00Z&timeMax=%sT00%%3A00%%3A00Z&key=%s&pageToken=%s' % (calendarid, calendarid, start, end, devkey, resp['nextPageToken'])

freqre = re.compile(r'(.*?) ([0-9]*kHz)(?:(?: and/or|,) ([0-9]*kHz))* ([^ ]*)(?: (.*))?')
def tsv(calid, dkey):
    for f in ['start', 'name', 'freq', 'altfreq', 'mode', 'comment', 'end', 'created',
              'updated', 'creator', 'sequence', 'id']:
        print "%s\t" % f,
    print
    for sched in getentries(calendarid, devkey):
        for f in ['start', 'summary', 'end', 'created',
                  'updated', 'creator', 'sequence', 'id']:
            if f in ['start', 'end']:
                print "%s\t" % sched[f]['dateTime'],
            elif f == 'creator':
                print "%s\t" % sched[f]['displayName'],
            elif f == 'summary':
                m = freqre.match(sched[f])
                if m:
                    station = {}
                    for i, f1 in enumerate(['id', 'freq', 'altfreq', 'mode', 'rest']):
                        if m.group(i+1):
                            print "%s\t" %m.group(i+1),
                        else:
                            print "\t",
                else:
                    print >>sys.stderr, 'dropping', line.strip()
            else:
                print "%s\t" % sched[f],
        print

calendarid = 'ul6joarfkgroeho84vpieeaakk%40group.calendar.google.com'
devkey = getdevkey(calendarid)
tsv(calendarid, devkey)
