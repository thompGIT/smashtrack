#!/usr/bin/python

import Shuffler

s = Shuffler.Shuffler('cards.db')

c, h = s.shuffleCards('Base','Cu+')

for card,ghash in zip(c,h):
    print str(ghash) + '\t' + card[0] + '\t' + card[1]
