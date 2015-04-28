import sqlite3
import string
import time
import os
import trueskill
from trueskill import Rating,TrueSkill

dbFile      = 'domtrack.db'
cardsDbFile = 'cards.db'

BASE_RATING   =   0.0

SIGMA_DEGRADE_RATE_PER_HOUR = 0.1 / 24.0    # Rate of sigma degrade (or loss of confidense in rating)

# TrueSkill environment variables
BASE_MU       =  25.0
BASE_SIGMA    = BASE_MU / 3.0
BASE_TAU      = 0.0833334           # Dynamic factor; Speed at which rankings vary (Isotropic uses SIGMA/100)
BASE_BETA     = 4.1666667           # How skills-based is the game (Isotripic uses 25)
BASE_DRAWPROB = 0.1                 # Percentage of draw matches




env = TrueSkill()

# Database stub
playerStats = [ (BASE_MU, BASE_SIGMA),
                (BASE_MU, BASE_SIGMA),
                (BASE_MU, BASE_SIGMA),
                (BASE_MU, BASE_SIGMA) ]

# Game 1
scores  = [32,6,4,5]
players = ['Taylor G.', 'Jack R.', 'Eric L.', 'James T.']

# Remove all non-players, and sort based on score (hi to low)
results_raw = zip(scores,players)
results = filter(lambda a: a[1] != 'none', results_raw)
results.sort(reverse=True)

rating_groups = []
for i in range(0,len(results)):
    rating_groups.append((env.create_rating(playerStats[i][0],playerStats[i][1]),))    
rated_rating_groups = env.rate(rating_groups)

for i in range(0,len(rated_rating_groups)):
    print results[i][1] + ': ' + str(rated_rating_groups[i][0].mu) + ', ' + str(rated_rating_groups[i][0].sigma)

