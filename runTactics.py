import sys
import re
import chess
import chess.engine
from ptParams import *
import json
import datetime

params = json.load(open(jsonFileName))
lc0_cmd = params["Lc0"]
del params["Lc0"]
weightPath = params["weights_path"]
del params["weights_path"]
#############################################################################
########### stuff for each run
#############################################################################
def movesToString(moveList):
	mls = []
	for m in moveList:
		mls.append(str(m))
	return " ".join(mls)	

def writeLog(logFile, logList):
	for val in logList:
		logFile.write(val + "\n")
	logFile.flush()  # so it can be monitored during run
	
# run one pass through an EPD tactics file with specific parameters
# returns (success, total, list of failures)
# either nodeNum or moveTime should be provided but not both
def runTactics(epdPath, logFile, lc0_cmd, optString, weightPath, weight, nodeNum):
	startTime = datetime.datetime.now()
	logLines = ["result; engine_move; iccf_move(s); nodes; problem_id; network; side; piece_count; evaluation"]
	#no options right now
	# lc0_cmd += " --weights=" + weightPath + weight + " --history-fill=always " + optString

	appendix = " nodes=" + str(nodeNum)
	logFile.write("#### " + lc0_cmd + appendix + "\n")
	sys.stderr.write(lc0_cmd + appendix + "\n")
	#engine = chess.uci.popen_engine(lc0_cmd)
	engine = chess.engine.SimpleEngine.popen_uci(lc0_cmd)
	#info_handler = chess.uci.InfoHandler()
	#engine.info_handlers.append(info_handler)  # there is an empty list of these on engine creation



	#engine.ucinewgame()

# this epdf file is now called position file and used fen not epd
# and it can't be here. This method is to run one positon!
# the engine options are set with configure()

	epdf = open(epdPath)
	epdfLines = epdf.readlines()
	epdf.close()
	epdfl = []
	for eline in epdfLines:
		if not eline.startswith("#"):
			epdfl.append(eline)
	sys.stderr.write("\n" + str(len(epdfl)) + " problems... ")
	right = 0; total = 0; nodesUsed = []
	for line in epdfl:
		fields = line.split(";")
		epdfield = fields[0].strip()
		#will use match to keep bm but for now just remove it
		epdfield = re.sub(' bm .*','',epdfield)
	

		#epd = board.set_epd(epdfield)
		board = chess.Board(epdfield)
		info = engine.analyse(board, chess.engine.Limit(nodes=100))
		move, pondermove = engine.go(nodes=nodeNum)  # Move objects
		pv = info_handler.info["pv"][1]
		mnodes = info_handler.info["nodes"] # mnodes is an integer
		nodesUsed.append(mnodes)
		best_moves = epd["bm"]
		bmstr = movesToString(best_moves)
		mscore = info_handler.info["score"][1].cp
		if mscore != None: evalstr = "%+.2f" % (mscore/100.0)
		else: evalstr = "no_score"
		if move in best_moves:
			right += 1
			logLines.append("; ".join(["1",str(move),bmstr,str(mnodes),idfield,weight,side,str(pieceNum),evalstr]))

		else:
			pv = info_handler.info["pv"][1]  # a list of the Move objects from the pv
			pvstrl = []
			for i in range(min(len(pv),6)):
				pvstrl.append(str(pv[i]))
			mvstr = " ".join(pvstrl)
			#mscore = info_handler.info["score"][1].cp
			if mscore != None:
				evalstr = "%+.2f" % (mscore/100.0)
				mvstr += " " + "%+.2f" % (mscore/100.0)  # the score in pawns with sign
			else: 
				evalstr = "no_score"
				mvstr += " no_score"
			logLines.append("; ".join(["0",str(move),bmstr,str(mnodes),idfield,weight,side,str(pieceNum),evalstr]))		

		if len(logLines) > logBufferSize-1:
			

			writeLog(logFile, logLines)
			logLines = []
		total += 1
				
		if  total % progressInterval == 0:
		
			elapsedTime = datetime.datetime.now() - startTime
			problems = len(epdfl)
			timePerProblem = elapsedTime/total
			expectedEndTime =  ((timePerProblem * problems ) + startTime).isoformat(' ','minutes')
			percentAgree = str(round(right/total*100,2))

			sys.stderr.write( "\r" + str(right) + "/" +str(total) + " Agree:" + percentAgree + "%  Expected end of this run:" + expectedEndTime + "            ")
			sys.stderr.flush()
			
	engine.quit()
	writeLog(logFile, logLines)  # make sure the last set is written
	sys.stderr.write("\n")
	return right, total, nodesUsed