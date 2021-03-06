#------------------------------------------------------------------------------
# DbSqlite.py
# Database module that uses SQLite for storage.
#------------------------------------------------------------------------------

import sqlite3
import string
import time
import os
import trueskill
from trueskill import Rating, TrueSkill

dbFile      = 'xtrack.db'

# TrueSkill environment variables
BASE_RATING   =   0.0
BASE_MU       =  25.0
BASE_SIGMA    = BASE_MU / 3.0
BASE_TAU      = 0.0833334           # Dynamic factor; Speed at which rankings vary (Isotropic uses SIGMA/100)
BASE_BETA     = 4.1666667           # How skills-based is the game (Isotripic uses 25)
BASE_DRAWPROB = 0.1                 # Percentage of draw matches

class DbSqlite():

    #--------------------------------------------------------------------------
    # database maintenance
    #--------------------------------------------------------------------------
    SCHEMA_GAMES = [
            ['time',     'REAL PRIMARY KEY'],  # Timestamp in epoch seconds
            ['P1',       'TEXT'],    # Player 1
            ['P1Rating', 'REAL'],    # Player 1 Rating - Global
            ['P1Score',  'REAL'],    # Player 1 Score
            ['P2',       'TEXT'],    # Player 2
            ['P2Rating', 'REAL'],    # Player 2 Rating - Global
            ['P2Score',  'REAL'],    # Player 2 Score
            ['P3',       'TEXT'],    # Player 3
            ['P3Rating', 'REAL'],    # Player 3 Rating - Global
            ['P3Score',  'REAL'],    # Player 3 Score
            ['P4',       'TEXT'],    # Player 4
            ['P4Rating', 'REAL'],    # Player 4 Rating - Global
            ['P4Score',  'REAL'],    # Player 4 Score
            ['P5',       'TEXT'],    # Player 5
            ['P5Rating', 'REAL'],    # Player 5 Rating - Global
            ['P5Score',  'REAL'],    # Player 5 Score
            ['P6',       'TEXT'],    # Player 6
            ['P6Rating', 'REAL'],    # Player 6 Rating - Global
            ['P6Score',  'REAL'],    # Player 6 Score
            ['hash',     'TEXT']]    # Game hash
    SCHEMA_PLAYERS = [
            ['name',  'TEXT PRIMARY KEY'],  # Player Name
            ['rating','REAL'],              # Rating
            ['mu',    'REAL'],              # Mu
            ['sigma', 'REAL'],              # Sigma
            ['time',  'REAL']]              # Timestamp of last game played
    SCHEMA_MISC = [
            ['setting',  'TEXT PRIMARY KEY'],
            ['value',    'TEXT']]           # Misc settings

    # Database configuration and initialization ------------------------------
    def createDatabase(self):
        print '\tDropping old tables'
        cmd = 'drop table if exists games'
        self.c.execute(cmd);
        cmd = 'drop table if exists players'
        self.c.execute(cmd);
        cmd = 'drop table if exists misc'
        self.c.execute(cmd);

        print '\tCreating new tables'
        cmd = 'CREATE TABLE games (' + ','.join(map(lambda x: ' '.join(x), self.SCHEMA_GAMES)) + ')'
        self.c.execute(cmd)
        cmd = 'CREATE TABLE players (' + ','.join(map(lambda x: ' '.join(x), self.SCHEMA_PLAYERS)) + ')'
        self.c.execute(cmd);
        cmd = 'CREATE TABLE misc (' + ','.join(map(lambda x: ' '.join(x), self.SCHEMA_MISC)) + ')'
        self.c.execute(cmd);

        self.conn.commit()

    # Clear the database of all entries (Yikes!)
    def clear(self):
        self.createDatabase()

    #--------------------------------------------------------------------------
    # player related
    #--------------------------------------------------------------------------
    
    # return list of players
    def getPlayerList(self):
        self.c.execute('SELECT name from players')
        try:
            return zip(*self.c.fetchall())[0]
        except:
            return ''
        
    # get the player's rating
    def getPlayerRating(self, name):
        self.c.execute('SELECT rating from players WHERE name=?', (name,))
        try:
            mu    = self.getPlayerMu(name)
            sigma = self.getPlayerSigma(name)
            return mu - (3.0 * sigma)
        except:
            return -200

    # get the player's mu
    def getPlayerMu(self, name):
        self.c.execute('SELECT mu from players WHERE name=?', (name,))        
        return self.c.fetchone()[0]
        
    # get the player's sigma
    def getPlayerSigma(self, name):
        self.c.execute('SELECT sigma from players WHERE name=?', (name,))
        sigma = self.c.fetchone()[0]
        return sigma

    # get the player's T (last time played)
    def getPlayerT(self, name):
        self.c.execute('SELECT time from players WHERE name=?', (name,))
        return self.c.fetchone()[0]

    # return a list [rating, mu, sigma, time]
    def getPlayerStats(self, name):
        rating = self.getPlayerRating(name)
        mu     = self.getPlayerMu(name)
        sigma  = self.getPlayerSigma(name)
        t      = self.getPlayerT(name)
        stats  = (rating, mu, sigma, t)
        return stats

    # add a new player to the system
    def addPlayer(self, name, rating=BASE_RATING, mu=BASE_MU, sigma=BASE_SIGMA, t=0):
        self.c.execute('INSERT into players values(?,?,?,?,?)', (name, rating, mu, sigma, t))
        self.conn.commit()
        
    # remove a player form the system
    def deletePlayer(self, name):
        self.c.execute('DELETE from players where name=?', (name,));
        self.conn.commit();
        
    # set a player's rating
    def setPlayerRating(self, name, r):
        self.c.execute('UPDATE players SET rating=?', (r,))
        self.conn.commit()

    # set a player's mu
    def setPlayerMu(self, name, mu):
        self.c.execute('UPDATE players SET mu=?', (mu,))
        self.conn.commit()
        
    # set a player's sigma
    def setPlayerSigma(self, name, sigma):
        self.c.execute('UPDATE players SET sigma=?', (sigma,))
        self.conn.commit()

    # set a player's stats (rating, mu, sigma, time)
    def setPlayerStats(self, name, listStats):
        self.c.execute('UPDATE players SET rating=?, mu=?, sigma=? ,time=? WHERE name=?',
                (listStats[0], listStats[1], listStats[2], listStats[3], name)
            )
        self.conn.commit()
           
    #--------------------------------------------------------------------------
    # game related
    #--------------------------------------------------------------------------
    
    # return list of games
    def getGames(self, since=0):
        sql =  'SELECT ' \
             + 'time' \
             + ',P1,P1Score,P1Rating' \
             + ',P2,P2Score,P2Rating' \
             + ',P3,P3Score,P3Rating' \
             + ',P4,P4Score,P4Rating' \
             + ',P5,P5Score,P5Rating' \
             + ',P6,P6Score,P6Rating' \
             + ',hash'                \
             + ' FROM games WHERE time>(?) order by time';
        self.c.execute(sql, (since,))
        games = []
        for x in self.c.fetchall():
            games.append([ x[0],
                           x[1],  x[2],  x[3],   \
                           x[4],  x[5],  x[6],   \
                           x[7],  x[8],  x[9],   \
                           x[10], x[11], x[12],  \
                           x[13], x[14], x[15],  \
                           x[16], x[17], x[18],  \
                           x[19]])
        return games

    # retrieve all games that had player involved in it
    def getGamesByPlayer(self, name, since=0):
        self.c.execute('SELECT * from games WHERE' +
            ' p1=? or p2=? or p3=? or p4=? or p5=? or p6=?' +
            ' and time>(?)' +
            ' ORDER by time',
            (name, name, name, name, name, name, name, name, since)
        )
        games = []
        for x in self.c.fetchall():
            games.append({'t':x[0], \
                          'p1':str(x[1]),  'p1_r':x[2],  \
                          'p2':str(x[3]),  'p2_r':x[4],  \
                          'p3':str(x[5]),  'p3_r':x[6],  \
                          'p4':str(x[7]),  'p4_r':x[8],  \
                          'p5':str(x[9]),  'p5_r':x[10], \
                          'p6':str(x[11]), 'p6_r':x[12]})

        return games
            
    # retrieve the number of first place finishes per player
    def getPlayerWinCount(self):
        self.c.execute('SELECT time,P1,P1Score,P2,P2Score,P3,P3Score,P4,P4Score,P5,P5Score,P6,P6Score from games order by time')
        scores  = []
        players = []
        wins    = []
        for x in self.c.fetchall():
            scores.append([x[2],x[4],x[6],x[8],x[10],x[12]])
            players.append([x[1],x[3],x[5],x[7],x[9],x[11]])                          
        games = zip(scores,players)
        
        for g in games:
            results_raw = zip(g[0],g[1])
            results = filter(lambda a: a[1] != 'none', results_raw)
            results.sort(reverse=True)
            print results

    # retrieve record of a single player versus a single opponent
    def getPvPRecord(self, p1, p2):
        self.c.execute('SELECT COUNT(*) from games WHERE p1=? and p2=?', (p1, p2))
        wins = self.c.fetchone()[0]
        self.c.execute('SELECT COUNT(*) from games WHERE p1=? and p2=?', (p2, p1))
        losses = self.c.fetchone()[0]
        return (wins, losses)
            
    # delete a game
    def deleteGame(self, t):
        self.c.execute('DELETE from games where time=?', (t,));
        self.conn.commit();

    # record a game
    def recordGame(self, players, scores, gameHash='', t=0):
    
        # Remove all non-players, and sort based on score (hi to low)
        results_raw = zip(scores,players)
        results = filter(lambda a: a[1] != 'none', results_raw)
        results.sort(reverse=True)
        
        # Rate the game using ONLY ONE of the available scoring techniques
        self.rateGameTrueSkill1v1(results)     # TrueSkill - 1v1 Sub-Games 
                
        # Create the query
        sql  = 'INSERT OR REPLACE into games values(?,?,?,?,?, ?,?,?,?,?, ?,?,?,?,?, ?,?,?,?,?)'
        timestamp = time.mktime(time.gmtime())
        if (t != 0):
            timestamp = t
                
        # Store the game        
        self.c.execute(sql,
                (timestamp, 
                players[0], self.getPlayerRating(players[0]), scores[0], 
                players[1], self.getPlayerRating(players[1]), scores[1], 
                players[2], self.getPlayerRating(players[2]), scores[2], 
                players[3], self.getPlayerRating(players[3]), scores[3], 
                players[4], self.getPlayerRating(players[4]), scores[4], 
                players[5], self.getPlayerRating(players[5]), scores[5],
                str(gameHash))
            )
        self.conn.commit()
                    
    # Scoring Technique - TrueSkill
    #   Each game is rated as a FFA of 1 person teams.
    def rateGameTrueSkill1v1(self, results):
           
        # Establish TrueSkill environment
        env = TrueSkill()

        # Rate the FFA game
        rating_groups = []
        for i in range(0,len(results)):
            mu    = self.getPlayerMu(results[i][1])
            sigma = self.getPlayerSigma(results[i][1])
            rating = env.create_rating(mu, sigma)
            rating_groups.append((rating,))            
        rated_rating_groups = env.rate(rating_groups)

        # Record the results in the database
        for i in range(0,len(rated_rating_groups)):
            mu     = rated_rating_groups[i][0].mu
            sigma  = rated_rating_groups[i][0].sigma
            rating = mu - (3 * sigma)
            self.setPlayerStats(results[i][1], [rating, mu, sigma, 0])
           
                        
    # recalculate all scores in the games history database
    def recalculateScores(self):
        
        # Get a list of all the games
        gamesToScore = []
        games = self.getGames()
        for game in games:
            players = []
            scores  = []
            for i in range(0,6):
                players.append(game[1+(i*3)+0])
                scores.append( game[1+(i*3)+1])
            gamehash = game[19]
            gamesToScore.append([int(game[0]),players,scores,gamehash])
              
        # Delete the old entries from the database
        self.c.execute('DELETE from games');
        self.conn.commit();
        
        # reset player ratings
        players = self.getPlayerList()
        for p in players:
            self.setPlayerStats(p, [BASE_RATING, BASE_MU, BASE_SIGMA, time.mktime(time.gmtime())])
                    
        # Re-process the stored games
        for g in gamesToScore:
            self.recordGame(g[1],g[2],g[3],g[0])        
          
    #--------------------------------------------------------------------------
    # DbSqlite::Init
    #--------------------------------------------------------------------------
    def __init__(self):
        # Determine if the database already exists
        createDB = 1
        if ( os.path.exists(dbFile) ):
            createDB = 0

        # Connect to players / games database
        self.conn = sqlite3.connect(dbFile)
        self.c = self.conn.cursor()
        
        # If players / games database did not already exist, create it from scratch
        if ( createDB ):
            print '\tInitializing new database...'
            self.createDatabase()
