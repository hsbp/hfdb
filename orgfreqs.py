#!/usr/bin/env python
# -*- coding: utf-8 -*-

from lxml.etree import tostring
from lxml.html.soupparser import fromstring
import requests, time, sys

urls=['http://amatorradiozas.hu/frekvencia-kiosztasok/bkv-mahart',
      'http://amatorradiozas.hu/frekvencia-kiosztasok/autopalyakezelo',
      'http://amatorradiozas.hu/frekvencia-kiosztasok/biztonsagi-szolgalatok',
      'http://amatorradiozas.hu/frekvencia-kiosztasok/fovarosi-kozterulet-felugyelet',
      'http://amatorradiozas.hu/frekvencia-kiosztasok/gaz-es-elektromos-muvek',
      'http://amatorradiozas.hu/frekvencia-kiosztasok/mav-volan-busz',
      'http://amatorradiozas.hu/frekvencia-kiosztasok/tuzoltosag',
      'http://amatorradiozas.hu/frekvencia-kiosztasok/taxik']

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

def parse_freqrange(freq, c1):
    if c1=='Khz':
        c1=1000
    elif c1=='Mhz':
        c1=1000000
    elif c1=='Ghz':
        c1=1000000000
    else:
        print 'bad mag', freq, mag
    try: exact = int(float(freq)*c1)
    except:
        print freq
        raise
    return exact,exact

for url in urls:
    print >>sys.stderr, 'fetching', url
    root=fetch(url)

    for node in root.xpath('//div[@class="postcontent"]/p'):
        txt=unws(text(node))
        if not txt[-2:]=='hz':
            continue
        freq, mag = txt.split()[-2:]
        txt = ' '.join(txt.split()[:-2])
        # data workarounds
        if freq[-1]=='-': freq = freq[:-1]
        if freq==u'háló': continue
        mi,mx = parse_freqrange(freq.replace(',','.'), mag)
        print (u"%s\t%s\t%s\t%s" % (mi,
                                        mx,
                                        'amatorradiozas.hu',
                                        txt)).encode('utf8')
