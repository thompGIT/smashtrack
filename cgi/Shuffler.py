#------------------------------------------------------------------------------
# Shuffler.py
#------------------------------------------------------------------------------

import sqlite3
import os
import sys

class Shuffler():
                   
    #--------------------------------------------------------------------------                                     
    # Shuffler::hashToCards
    #   Create a set of kingdom cards from a hash
    #--------------------------------------------------------------------------
    def hashToCards(self, cHash):
        cards = []
        for i in range(0, len(cHash) / 2):
            cardId = int(cHash[i*2]+cHash[i*2+1],16)
            try:
                self.cards_c.execute('SELECT Expansion,Title,Cost_P,id FROM cards WHERE id=' + str(cardId))
            except sqlite3.Error, e:
                print 'Error %s:' % e.args[0]            
            for x in self.cards_c.fetchall():
                cards.append([ x[0], x[1], x[2], x[3] ])
        return cards
                
    #--------------------------------------------------------------------------   
    # Shuffler::shuffleCards
    #   Shuffle card, return a kingdom hash.
    #
    #   (in) setsString: Comma delimeted string of kingdoms to choose from.
    #--------------------------------------------------------------------------   
    def shuffleCards(self, setsString, options = ''):
		                
        # Tokenize the sets string
        sets = setsString.split(',')		
        
        # Disallowed card titles
        excludedCards = ['Platinum','Colony',               # Prosperity
                         'Potion',                          # Alchemy
                         'Spoils','Madman','Mercenary']     # Dark Ages
                         
        # Disallowed card types
        excludedTypes = ['Ruin','Shelter','Prize']
        
        # Disallowed card types - Optional
        if (options.find('Cu-') >= 0):
            excludedTypes.append('Requires_Curses')
		
        # Grab the raw cards from the database
        sql  = 'SELECT Expansion,Title,Cost_P,id FROM cards WHERE'
        
        # Exclude cards by type
        for c in excludedTypes:
            sql += ' (' + c + ' = 0) and '        
        sql += ' (Knight  = 0 or Title = \'Sir Martin\') '         # Knights are special as they are part of the supply, but only use one
        
        # Exclude cards by title
        for c in excludedCards:                                    
            sql += ' and Title != \'' + c + '\''        
        sql += ' and ('
        
        # Include specified expansions
        for s in sets:                                             
            sql += ' Expansion = \'' + s + '\' or'
        sql = sql[:-2]
        sql += ') ORDER BY RANDOM() LIMIT 10'        		
        self.cards_c.execute(sql)
		
        # Clean up the results
        cards = []
        for x in self.cards_c.fetchall():
            cards.append([ x[0], x[1], x[2], x[3] ])
            	    
        # Add Colonies and Platnum if the first card chosen randomly was from Prosperity
        if cards[0][0] == 'Prosperity':
            cards.append(['Prosperity','Colony',0,116])
            cards.append(['Prosperity','Platinum',0,115])
                
        # Add Shelters if the first card chosen randomly was from Dark Ages
        if cards[0][0] == 'Dark Ages':
            cards.append(['Dark Ages','Shelters*',0,169])
		
        # Add Potions if Alchemy expansion is in play
        for card in cards:
            if card[2] == 1:
                cards.append(['Alchemy','Potion',0,87])
                break
		
        # Add Prizes if Tournament is in play
        for card in cards:
            if card[1] == 'Tournament':
                cards.append(['Cornucopia','Prizes*',0,117])
                break
                
        # Add Knights if Sir Martin is in play
        for card in cards:
            if card[1] == 'Sir Martin':
                cards.append(['Dark Ages','Knights*',0,191])
                break
		
        # Add Spoils if Marauder, Bandit Camp, or Pillage are in play
        for card in cards:
            if card[1] == 'Marauder' or card[1] == 'Bandit Camp' or card[1] == 'Pillage':
                cards.append(['Dark Ages','Spoils',0,167])
                break
                
        # Add Madman if Hermit is in play
        for card in cards:
            if card[1] == 'Hermit':
                cards.append(['Dark Ages','Madman',0,162])
                break
		
        # Add Mercenary if Urchin is in play
        for card in cards:
            if card[1] == 'Urchin':
                cards.append(['Dark Ages','Mercenary',0,181])
                break
                
        # Add Ruins if Marauder, Cultist, or Death Cart is in play
        for card in cards:
            if card[1] == 'Marauder' or card[1] == 'Cultist' or card[1] == 'Death Cart':
                cards.append(['Dark Ages','Ruins*',0,161])
                break
                
        # Sort the results to group by expansion
        cards.sort()
		        		          
        # Calculate the kingdom hash value
        # - The hash is a series of ascii hex bytes representing cards in the kingdom
        kingdomHash = ''
        for card in cards:
            kingdomHash += '{:02x}'.format(int(card[3]))
            
        # Store the kingdom 
#        self.c.execute('INSERT OR REPLACE INTO misc VALUES (?,?)', ('lasthash',kingdomHash,));
#        self.conn.commit();
                        		        		          
        return (cards,kingdomHash)
		
    #--------------------------------------------------------------------------
    # Shuffler::__init__
    #--------------------------------------------------------------------------
    def __init__(self, cardsDb):
        
        # Make sure the cards database exists
        if ( not os.path.exists(cardsDb) ):
            print 'Error: Unable to locate cards database [%s]' % cardsDb
            sys.exit(1)
        
        # Connect to the cards database
        try:
            self.cards_conn = sqlite3.connect(cardsDb)
            self.cards_c = self.cards_conn.cursor()
            
        except sqlite3.Error, e:
            print 'Error %s:' % e.args[0]
            sys.exit(1)
            
    #--------------------------------------------------------------------------
    # Shuffler::__del__
    #--------------------------------------------------------------------------
    def __del__(self):
        # Close the cards database
        try:
            self.cards_conn.close()
        except sqlite3.Error, e:
            print 'Error %s:' % e.args[0]
            sys.exit(1)
