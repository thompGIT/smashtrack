/******************************************************************************
 * debug
 *****************************************************************************/
var g_DEBUG = 0

function debug(msg) {
    if(g_DEBUG) {
        console.log(msg)
    }
}

/******************************************************************************
 * GLOBALS
 *****************************************************************************/
var TEMPLATE_PlayerInput = "\
	<td bgcolor='#5882FA'>\
		<div class=playerSelect>\
			<div class=playerSelectTitle>PLAYER_TITLE_CAPS:</div>\
			<div class=playerSelectCombo>\
				<select id=PLAYER_TITLE \
					class=comboPlayer \
					onchange='selChange_cb(this)'> \
				</select> \
			</div> \
		</div> \
	</td>"		

/******************************************************************************
 * UTILS
 *****************************************************************************/
function ajax(url) {
    var xmlhttp = new XMLHttpRequest()
    debug("AJAX: " + url)
    xmlhttp.open("GET", url, false)
    xmlhttp.send()
    var resp = xmlhttp.responseText
    debug("AJAX: " + resp)
    return resp
}

/* Hack to display proper time in javascript. Sucks, but it works. */
var TIMEHACK = (-1 * 1000 * 60 * 60 * 9)

/* Create a string from a Date object */
function dateToString(date) {
    return date.toUTCString()
}

/******************************************************************************
 * global vars
 *****************************************************************************/

/* overall */
var showElems = []

var numPlayers = 6

var playerElems   = []
var scoreElems    = []
var playerStats   = []

var playerNames    = []
var playerToRating = []
var playerToMu     = []
var playerToSigma  = []
var playerToT      = []

/* istats */
var elem_istatsPlayerChoice

/******************************************************************************
 * inner-mode functions
 *****************************************************************************/

/* called when the page loads */
function xtrackInit(x) {

    /* overall modes; play is the default */
    showElems.push(document.getElementById("play"))
    showElems.push(document.getElementById("stats"))
    showElems.push(document.getElementById("games"))
    showElems.push(document.getElementById("admin"))
    showPlay()

	// Play Screen - Create and initialize the player input rows
    for (i=1; i<=numPlayers; i++) {
        initializePlayerInput('PLAYER_INPUT_p'+i)
        playerElems.push(document.getElementById('p'+i))
        scoreElems.push(document.getElementById('p'+i+'_vp'))
    }

    // Hack to hide player inputs
    for (i=3; i<=6; i++) {
        document.getElementById('PLAYER_INPUT_p'+i).style.display = 'none'
    }

    /* init global player vars */
    refreshPlayerDataStore()

    /* populate player choice drop-downs */
    playerNames.sort()
    for(var i in playerElems) {
        playerElems[i].value = ''
        playerElems[i].innerHTML = '<option></option>'
        for(var j in playerNames) {
            playerElems[i].innerHTML += "<option>" + playerNames[j] + "</option>"
        }
    }
}

/* Play Screen - Create a player input box */
function initializePlayerInput(p) {			
	var playerTitle = p.replace('PLAYER_INPUT_','')	
	var html = TEMPLATE_PlayerInput
	html = html.replace(/PLAYER_TITLE_CAPS/g,playerTitle.toUpperCase())
	html = html.replace(/PLAYER_TITLE/g,playerTitle)	
	document.getElementById(p).innerHTML = html
}


function refreshPlayerDataStore() {
    var resp = ajax('cgi/jsIface.py?op=getplayers')
    var lines = resp.split("\n")
    for(var j in lines) {
        var m = lines[j].match(/^(.*),(.*),(.*),(.*),(.*)$/)

        if(m) {
            playerName                 = m[1]                        
            playerNames.push(playerName)
            playerToRating[playerName] = parseFloat(m[2])
            playerToMu[playerName]     = parseFloat(m[3])
            playerToSigma[playerName]  = parseFloat(m[4])
            playerToT[playerName]      = parseFloat(m[5])            
        }
    }
}

function hideAllBut(e) {
    for(var i in showElems) {
        if(showElems[i] == e) {
            showElems[i].style.display = 'block'
        }
        else {
            try { 
                showElems[i].style.display = 'none'
            } catch (err) { }            
        }
    }
}

function showPlay() {
    hideAllBut(document.getElementById('play'))
}

function showLeaderboard() {
    hideAllBut(document.getElementById('stats'))

    // each graph has a function dedicated to loading it...
    loadLeaderBoard()
    loadAllRatingsVsGamesGraph()
    loadAllRatingsHistoryGraph()
}

function showGamesList() {
    hideAllBut(document.getElementById('games'))
    loadGamesList()
}

function showAdmin() {
    hideAllBut(document.getElementById('admin'))
}

/******************************************************************************
 * PLAY MODE stuff
 *****************************************************************************/
function selChange_cb(elem) {

    for(var i=0; i<numPlayers; ++i) {
        if(elem != playerElems[i] && elem.value == playerElems[i].value) {
	        /* this works in chrome, firefox */
            playerElems[i].value = ""
            /* this works in kindle fire browser */
	        playerElems[i].options.selectedIndex = 0
        }
    }
}

function recordGame(elem) {

    /* milliseconds before next game records */
    var disabledDelay = 5*1000

    var p = ''
    var s = 0
    var players = []
    var scores  = []

    /* Load all the player names and scores */    
    var pCount = 0
    for(var i in playerElems) {
        if (playerElems[i].value == '') { 
            p = 'none' 
        } else {
            p = playerElems[i].value
            pCount += 1
        }

        // Assume the players are listed in order of finish position
        s = playerElems.length - i

        players.push(p)
        scores.push(s)
    }
       
    /* build the ajax request */
    var req = 'cgi/jsIface.py?op=recordGame'
    for (i in players) {
        req += '&p' + (parseInt(i)+1) + '='   + players[i] + '&p' + (parseInt(i)+1) + '_vp=' + scores[i]
    }
    req += '&hash=0'  

    /* do it! */
    if (pCount > 1) {
        ajax(req)
    } else {
        alert('At least 2 players required!')
        return
    }

    /* message */
    alert('Win for ' + players[0] + ' recorded!')
    location.reload()
}

/* Clear all active players and scores. */
function clearPlayers(elem)
{    
    for(var e in playerElems) {
        playerElems[e].value = ''
    }     
    for(var s in scoreElems) {
        scoreElems[s].value = ''
    }   
}

/******************************************************************************
 * OVERALL STATS MODE stuff
 *****************************************************************************/
function loadLeaderBoard() {
    document.getElementById("LeaderBoard").innerHTML = "loading..."

    rankedPlayers = playerNames
    rankedPlayers.sort(function(a,b){ return playerToRating[b]-playerToRating[a] })
    
    var html = ''
    html += '<table>'
    html += '<tr><th colspan=3>Leader Board!</th></tr>'

    var place = 1
    for(var i in rankedPlayers) {
        p = rankedPlayers[i]

        // Only add people who have played games to the leaderboard
        if(playerToSigma[p] > 8.0) { 
            continue
        }

        html += "<tr><td>" + place + ")</td><td align=right width=150px><font color=#64788B>" + p +  
        "</font></td><td align=right width=75px><b>" + playerToRating[p] + '</b></td><td align=center width=150px>(' + playerToMu[p] + '/' + playerToSigma[p] + ")</td></tr>\n"

        place++
    }
    html += '</center>'
    document.getElementById("LeaderBoard").innerHTML = html
}

function loadAllRatingsHistoryGraph() {
    /* prepare the user for delay */
    document.getElementById("AllRatingsHistoryGraph_status").innerHTML = "loading..."

    /* get to work */
    var playerList = []
    var playerToObject = {}

    /* each game offers a sample point */
    var resp = ajax("cgi/jsIface.py?op=getGames")
    var lines = resp.split("\n")
    for(var i in lines) {
        var data = lines[i].split(",")
        var t = parseInt(data[0])        
        var p1   = data[1]
        var p1_s = parseInt(data[2])
        var p1_r = parseFloat(data[3])
        var p2   = data[4]
        var p2_s = parseInt(data[5])
        var p2_r = parseFloat(data[6])
        var p3   = data[7]
        var p3_s = parseInt(data[8])
        var p3_r = parseFloat(data[9])
        var p4   = data[10]
        var p4_s = parseInt(data[11])
        var p4_r = parseFloat(data[12])
        var p5   = data[13]
        var p5_s = parseInt(data[14])
        var p5_r = parseFloat(data[15])
        var p6   = data[16]
        var p6_s = parseInt(data[17])
        var p6_r = parseFloat(data[18])        
        if(isNaN(t)) {
            continue
        }

        var players = [p1, p2, p3, p4, p5, p6]
        var ratings = [p1_r, p2_r, p3_r, p4_r, p5_r, p6_r]

        /* update each player's data from the game */
        for(var j in players) {
            var p = players[j]
            var r = ratings[j]

            /* create if not exist yet */
            if(playerToObject[p] == undefined) {
                playerList.push(p)
                playerToObject[p] = { name: p, data: [] }
            }

            /* append this one rating sample */
            /* recall that the 'datetime' type of xAxis in highcharts expects milliseconds */
            playerToObject[p]['data'].push([(t*1000)+TIMEHACK, r])
        }
    }

    /* finally, push the current ratings as the last sample point for each present player */
    tNow = (new Date()).getTime()
    for(var i in playerNames) {
        p = playerNames[i]

        if(playerToObject[p] == undefined) {
            continue
        }

        playerToObject[p]['data'].push([tNow, playerToRating[p]])
    }

    /* build the series as an array of player objects */
    var seriesData = []
    for(var i in playerList) {
        if (playerList[i] != "none") {
            seriesData.push(playerToObject[playerList[i]])
        }
    }

    /* finally, render the graph into this div */
    var chart = new Highcharts.Chart(
        {
            chart: {
                renderTo: document.getElementById("AllRatingsHistoryGraph"), 
                zoomType: 'xy', 
                type: 'line'
            },
            plotOptions: {
               series: {
                   marker: {
                       enabled: false,
                       states: {
                           hover: {
                               enabled: true
                           }
                       }
                   }
               }
            },
            title: {
                text: 'Player Rating vs. Time'
            },
            xAxis: {
                type: 'datetime',
                dateTimeLabelFormats: { // don't display the dummy year
                    month: '%e. %b',
                    year: '%b'
                }
            },
            yAxis: {
                title: {
                    text: 'Rating'
                },
                min: 0
            },
            tooltip: {
                formatter: function() {
                    return '<b>'+ this.series.name +'</b><br/>'+Highcharts.dateFormat('%e. %b', this.x) +': '+ this.y
                }
            },
            series: seriesData
        }
    )

    /* erase the "loading..." message */
    document.getElementById("AllRatingsHistoryGraph_status").innerHTML = ""
}

function loadAllRatingsVsGamesGraph() {
    /* prepare the user for delay */
    document.getElementById("AllRatingsVsGamesGraph_status").innerHTML = "loading..."

    /* get to work */
    var playerList = []
    var playerToObject = {}

    var resp = ajax("cgi/jsIface.py?op=getGames")
    var lines = resp.split("\n")
    for(var i in lines) {    
        var data = lines[i].split(",")
        var t = parseInt(data[0])        
        var p1   = data[1]
        var p1_s = parseInt(data[2])
        var p1_r = parseFloat(data[3])
        var p2   = data[4]
        var p2_s = parseInt(data[5])
        var p2_r = parseFloat(data[6])
        var p3   = data[7]
        var p3_s = parseInt(data[8])
        var p3_r = parseFloat(data[9])
        var p4   = data[10]
        var p4_s = parseInt(data[11])
        var p4_r = parseFloat(data[12])
        var p5   = data[13]
        var p5_s = parseInt(data[14])
        var p5_r = parseFloat(data[15])
        var p6   = data[16]
        var p6_s = parseInt(data[17])
        var p6_r = parseFloat(data[18])        
        if(isNaN(t)) {
            continue
        }

        var players = [p1, p2, p3, p4, p5, p6]
        var ratings = [p1_r, p2_r, p3_r, p4_r, p5_r, p6_r]
        
        /* update each player's data from the game */
        for(var i in players) {
            var p = players[i]
            var r = ratings[i]

            /* create if not exist yet */
            if(playerToObject[p] == undefined) {
                playerList.push(p)
                playerToObject[p] = { name: p, data: [], nGames: 0 }
            }

            /* append this one rating sample */
            var nGames = playerToObject[p]['nGames']
            playerToObject[p]['data'].push([nGames, r])
            playerToObject[p]['nGames']++
        }
    }

    /* build the series as an array of player objects */
    var seriesData = []
    for(var i in playerList) {
        playerToObject[playerList[i]]['nGames'] = undefined
        if (playerList[i] != "none") {
            seriesData.push(playerToObject[playerList[i]])
        }
    }

    /* finally, render the graph into this div */
    var chart = new Highcharts.Chart(
        {
            chart: {
                renderTo: document.getElementById("AllRatingsVsGamesGraph"), 
                zoomType: 'xy', 
                type: 'line'
            },
            plotOptions: {
               series: {
                   marker: {
                       enabled: false,
                       states: {
                           hover: {
                               enabled: true
                           }
                       }
                   }
               }
            },
            title: {
                text: 'Player Rating vs. Amount Games Played'
            },
            xAxis: {
                title: {
                    text: 'n\'th game'
                },
                min: 0
            },
            yAxis: {
                title: {
                    text: 'Rating'
                },
                min: 0
            },
            tooltip: {
                formatter: function() {
                    return '<b>'+ this.series.name +'</b><br/>'+Highcharts.dateFormat('%e. %b', this.x) +': '+ this.y
                }
            },
            series: seriesData
        }
    )

    /* erase the "loading..." message */
    document.getElementById("AllRatingsVsGamesGraph_status").innerHTML = ""
}

/******************************************************************************
 * GAMES LIST MODE
 *****************************************************************************/
function loadGamesList() {
    var date  = new Date()
    var resp  = ajax("cgi/jsIface.py?op=getGames")
    var lines = resp.split("\n")
    lines.reverse()

    var html = ''
    html += '<table cellpadding=0 cellspacing=8px>\n'
    html += '<tr>\n'
    html += '  <th style="text-align:center">Date</th>\n'
    html += '  <th style="text-align:center">Winner</th>\n'
    html += '  <th style="text-align:center">Loser</th>\n'
    html += '</tr>\n'

    for(var i in lines) {
        if(!lines[i]) {
            continue
        }

        var gameData = lines[i].split(",")
        var t = parseInt(gameData[0])
        var p1   = gameData[1]
        var p1_s = parseInt(gameData[2])
        var p1_r = parseFloat(gameData[3])
        var p2   = gameData[4]
        var p2_s = parseInt(gameData[5])
        var p2_r = parseFloat(gameData[6])
        var p3   = gameData[7]
        var p3_s = parseInt(gameData[8])
        var p3_r = parseFloat(gameData[9])
        var p4   = gameData[10]
        var p4_s = parseInt(gameData[11])
        var p4_r = parseFloat(gameData[12])
        var p5   = gameData[13]
        var p5_s = parseInt(gameData[14])
        var p5_r = parseFloat(gameData[15])
        var p6   = gameData[16]
        var p6_s = parseInt(gameData[17])
        var p6_r = parseFloat(gameData[18])        
        date.setTime((t*1000)+TIMEHACK)
        
        var players = [p1, p2, p3, p4, p5, p6]
        var ratings = [p1_r, p2_r, p3_r, p4_r, p5_r, p6_r]
        var scores  = [p1_s, p2_s, p3_s, p4_s, p5_s, p6_s]
        
        var DivLoser  = 'class=gameLogPlayerEntry'
        var DivWinner = 'class=gameLogPlayerEntryWin'
        var win       = scores.indexOf(Math.max.apply(window,scores))

        html += '<tr>\n'
        html += '  <td width=250px align=center>\n'
        html += dateToString(date) + "\n"
        html += '  </td>\n'
        for (var p in players) {        
            html += '  <td>\n'
            if (players[p] != 'none') {
                html += '    <div ' + ((scores[p]==scores[win]) ? DivWinner : DivLoser) + '><b>' + players[p] + '</b> <i>(' + ratings[p] + ')</i></div>\n'
            }
            html += '  </td>\n'
        }
        html += '  <td>\n'
        html += '    <input type=submit class=menuBtn value="Delete" onClick="deleteGame_cb(this, ' + t + ')">\n'
        html += '  </td>\n'
        html += '</tr>\n'
    }

    html += '</table>\n'

    document.getElementById("games").innerHTML = html
}

/******************************************************************************
 * MISC ADMIN
 *****************************************************************************/
function deleteGame_cb(e, gameId) {
    ajax("cgi/jsIface.py?op=deleteGame&t=" + gameId)
    e.disabled = 1
}

function addPlayer() {
	player = document.getElementById("addPlayerName").value;
	console.log('Adding Player: ' + player)
    ajax("cgi/jsIface.py?op=addPlayer&player=" + player)
}

function deletePlayer() {
	player = document.getElementById("deletePlayerName").value;
	console.log('Deleting Player: ' + player)
    ajax("cgi/jsIface.py?op=deletePlayer&player=" + player)
}

function recalcScores() {
    ajax("cgi/jsIface.py?op=recalculateScores")    
}
