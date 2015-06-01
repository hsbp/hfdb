#!/usr/bin/env python
# -*- coding: utf-8 -*-

# forras
# 2/2013. (I. 7.) NMHH rendelet a polgári célra használható frekvenciasávok felhasználási szabályainak megállapításáról2/2013. (I. 7.) NMHH rendelet

from lxml.etree import tostring
from lxml.html.soupparser import fromstring
import requests, time, sys

lex_url='http://net.jogtar.hu/jr/gen/hjegy_doc.cgi?docid=A1300002.NMH'

PROXIES = {} #{'http': 'http://localhost:8123/'}
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

def parse_freqrange(frange):
    if frange=='9kHzalatt':
        bot, top = 0, 9000
    else:
        try:
            bot,top = frange.split('-',1)
        except:
            print frange
            raise
        metric=top[-3]
        if metric=='k':
            metric=1000
        elif metric=='M':
            metric=1000000
        elif metric=='G':
            metric=1000000000
        bot=int(float(bot.replace(',','.'))*metric)
        top=int(float(top[:-3].replace(',','.'))*metric)
    return (bot,top)

#root=fetch(lex_url)
with open('xml','r') as fd:
    raw=fd.read()
    root = fromstring(raw)
    del raw

node = (root.xpath('//a[@name="pr168"]/following-sibling::p') or [None])[0]
mx0=0
frex={}
band=None
while node:
    table=node.xpath('table')
    if not table: continue
    if len(table)>1:
        print >>sys.stderr, "more than 1 table"
        continue
    table=table[0]

    trs=len(table.xpath('.//tr'))
    if trs!=1:
        print >>sys.stderr, "more than 1 tr:", trs

    tds=table.xpath('.//td')
    if len(tds)==2:
        frange=unws(text(tds[1]),'')
        if frange:
            mi,mx=parse_freqrange(frange)
            if mi!=mx0:
                print "%s\t%s\t%s" % (mx0, mi, 'empty')
                #frex.append((mx0,mi,'empty'))
                #print >>sys.stderr, 'gap between', mx0, mi
            mx0=mx
            band=mi,mx
    if len(tds)==6:
        #frex.append(band+[text(tds[i]) for i in xrange(1,6)])
        print (u"%s\t%s\t%s" % (band[0],band[1], u'\t'.join([unws(text(tds[i])) for i in xrange(1,6)]))).encode('utf8')
    if unws(text(tds[0]),'')=='3407': break
    node = node.xpath('./following-sibling::p')[0]
