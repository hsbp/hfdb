#!/usr/bin/env python
# -*- coding: utf-8 -*-

from lxml.etree import tostring
from lxml.html.soupparser import fromstring
import requests, time, sys

urls=[('http://wiki.ham.hu/index.php?title=2200_m%C3%A9ter', 1000,3),
      ('http://wiki.ham.hu/index.php?title=160_m%C3%A9ter', 1000, 3),
      ('http://wiki.ham.hu/index.php?title=80_m%C3%A9ter', 1000, 3),
      ('http://wiki.ham.hu/index.php?title=40_m%C3%A9ter', 1000, 3),
      ('http://wiki.ham.hu/index.php?title=30_m%C3%A9ter', 1000, 3),
      ('http://wiki.ham.hu/index.php?title=20_m%C3%A9ter', 1000, 3),
      ('http://wiki.ham.hu/index.php?title=17_m%C3%A9ter', 1000, 3),
      ('http://wiki.ham.hu/index.php?title=15_m%C3%A9ter', 1000, 3),
      ('http://wiki.ham.hu/index.php?title=12_m%C3%A9ter', 1000, 3),
      ('http://wiki.ham.hu/index.php?title=10_m%C3%A9ter', 1000, 3),
      ('http://wiki.ham.hu/index.php?title=6_m%C3%A9ter', 1000000, 4),
      ('http://wiki.ham.hu/index.php?title=4_m%C3%A9ter', 1000000, 4),
      ('http://wiki.ham.hu/index.php?title=2_m%C3%A9ter', 1000000, 4),
      ("http://wiki.ham.hu/index.php?title=70_cm", 1000000, 4),
      ('http://wiki.ham.hu/index.php?title=23_cm', 1000000, 4),
]

PROXIES = {'http': 'http://localhost:8123/'}
HEADERS =  { 'User-agent': 'hunfreqdb/0.1' }

def fetch_raw(url, retries=5, ignore=[], params=None):
    try:
        if params:
            r=requests.POST(url, params=params, proxies=PROXIES, headers=HEADERS)
        else:
            r=requests.get(url, proxies=PROXIES, headers=HEADERS)
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout), e:
        if e == requests.exceptions.Timeout:
            print >>sys.stderr, 'timeout'
            retries = min(retries, 1)
        if retries>0:
            print >>sys.stderr, 'wait', 4*(6-retries), 'sec and retry'
            time.sleep(4*(6-retries))
            f=fetch_raw(url, retries-1, ignore=ignore, params=params)
        else:
            raise ValueError("failed to fetch %s" % url)
    if r.status_code >= 400 and r.status_code not in [504, 502]+ignore:
        print >>sys.stderr, "[!] %d %s" % (r.status_code, url)
        r.raise_for_status()
    return r.text

def fetch(url, retries=5, ignore=[], params=None):
    f = fetch_raw(url, retries, ignore, params)
    return fromstring(f)

def unws(txt, spc=u' '):
    return spc.join(txt.split())

def text(node):
    return unws(''.join(node.xpath('.//text()')))

def parse_freqrange(frange, c1):
    exact=None
    frange=frange.replace(u'–',u'-')
    try:
        bot,top = frange.split('-',1)
    except:
        #print frange.encode('utf8')
        try: exact = int(float(frange)*c1)
        except:
            print frange
            raise
    if exact:
        return exact,exact
    else:
        return int(float(bot)*c1), int(float(top)*c1)

for url, c1, cols in urls:
    print >>sys.stderr, 'fetching', url
    root=fetch(url)

    mx0=0
    table = root.xpath('//table//th[contains(text(),"Frekvencia")]/ancestor::table')[0]
    #print tostring(table)
    for node in table.xpath('.//tr'):
        tds=node.xpath('.//td')
        if len(tds)!=cols: continue
        frange=unws(text(tds[0]),'').replace(',','.')
        mi,mx = parse_freqrange(frange,c1)
        if mi!=mx0 and mx0!=0:
            print "%s\t%s\t%s" % (mx0, mi, 'empty')
        mx0=mx
        print (u"%s\t%s\t%s\t%s\t%s" % (mi,
                                        mx,
                                        'hamwiki',
                                        unws(text(tds[cols-1])),
                                        u'\t'.join([unws(text(tds[i])) for i in xrange(1,cols-1)]))).encode('utf8')
