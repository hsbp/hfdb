#!/usr/bin/env python

import sys

dbfile='frekik.tsv'
db = []
with open(dbfile,'r') as fd:
    db = [line.split('\t') for line in fd]

mags={'k':1000, 'M': 1000000, 'G': 1000000000}

f=sys.argv[1]
if f[-1] in mags:
    f=int(float(f[:-1])*mags[f[-1]])
else:
    f=int(f)

i=0
while i<len(db): # and int(db[i][0])<=f:
    if int(db[i][0])<=f<=int(db[i][1]):
        if db[i][2]=='nmhh':
            if len(db[i])>4:
                print db[i][2], db[i][3], db[i][5]
            else:
                print db[i][2], db[i][3]
        if db[i][2]=='hamwiki':
            print db[i][2], db[i][3]
    i+=1
