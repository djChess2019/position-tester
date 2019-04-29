import sys
import os
import numpy as np
import chess
import chess.uci
import json

# TODO make proper options
# TODO should add target file to log

# NOTE: --history-fill=always is hard coded - no need for having it set in .json

noisy = True
progressInterval = 1000
logBuffer = 1000

# file with a simple list of networks to test, 1 per line. path taken from json
netsFileName = sys.argv[1]
# configuration file for paths and Leela parameters
jsonFileName = sys.argv[2]
# the output file will have a bare bones summary of parameters and success rate
outFileName = sys.argv[3]
# the log file will contain a simple summary of failed problems
logFileName = sys.argv[4]

logFile = open(logFileName, "a")
appendingOut = os.path.exists(outFileName)
outFile = open(outFileName,"a")


# set up command and paths from the json file, removing them as you go
params = json.load(open(jsonFileName))
epdPath = params["EPD"]
del params["EPD"] 
lc0_cmd = params["Lc0"]
del params["Lc0"]
weightPath = params["weights_path"]
del params["weights_path"]
nodes = None
if "nodes" in params:
	nodes = params["nodes"]
	del params["nodes"]
else:
	time = params["time"]
	del params["time"]

if not appendingOut:  # write a header if this is a new output file
	if nodes == None:
		outFile.write("network\tmsec\tavg_nodes\tagreed\ttotal\tpercent\n")
	else:
		outFile.write("network\treq_nodes\tavg_nodes\tagreed\ttotal\tpercent\n")
	outFile.flush()
		
# get the rest of the options in lexicograph order
pkeys = sorted(list(params.keys()))
optList = []
for pkey in pkeys:
	if params[pkey] == "":
		optList.append("--" + pkey)
	else:
		optList.append("--" + pkey + "=" + str(params[pkey]))
optString = " ".join(optList)

weights = []
of = open(netsFileName)
for line in of:
	if len(line) > 2 and not line.startswith("#"):
		netw = line.strip()
		if not os.path.exists(weightPath + netw):
			sys.stderr.write("weight file not found: " + weightPath + netw + "\n")
			sys.exit(1)
		weights.append(netw)
of.close()

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
def runTactics(epdFile, logFile, lc0_cmd, optString, weightPath, weight, nodeNum=None, moveTime=None):
	logLines = ["result; engine_move; iccf_move(s); nodes; problem_id; network; side; piece_count; evaluation"]
	lc0_cmd += " --weights=" + weightPath + weight + " --history-fill=always " + optString
	if nodeNum == None:
		appendix = " msec=" + str(time)
	else:
		appendix = " nodes=" + str(nodeNum)
	logFile.write("#### " + lc0_cmd + appendix + "\n")
	sys.stderr.write(lc0_cmd + appendix + "\n")
	engine = chess.uci.popen_engine(lc0_cmd)
	info_handler = chess.uci.InfoHandler()
	engine.info_handlers.append(info_handler)  # there is an empty list of these on engine creation
	board = chess.Board()
	engine.ucinewgame()
	epdf = open(epdFile)
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
		epdfield = fields[0]
		side = fields[0].split()[1]
		idfield = fields[1].strip()
		epd = board.set_epd(epdfield)
		engine.ucinewgame()
		engine.position(board)
		pieceNum = len(board.piece_map())
		if nodeNum == None:
			move, pondermove = engine.go(movetime=moveTime)
		else:
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
			logLines.append("; ".join(["agree",str(move),bmstr,str(mnodes),idfield,weight,side,str(pieceNum),evalstr]))
		else:
			pv = info_handler.info["pv"][1]  # a list of the Move objects from the pv
			pvstrl = []
			for i in range(min(len(pv),6)):
				pvstrl.append(str(pv[i]))
			mvstr = " ".join(pvstrl)
			if mscore != None:
				evalstr = "%+.2f" % (mscore/100.0)
				mvstr += " " + "%+.2f" % (mscore/100.0)  # the score in pawns with sign
			else: 
				evalstr = "no_score"
				mvstr += " no_score"			
			logLines.append("; ".join(["disagree",str(move),bmstr,str(mnodes),idfield,weight,side,str(pieceNum),evalstr]))		
		
		if len(logLines) > logBuffer-1:
			writeLog(logFile, logLines)
			logLines = []
		total += 1
				
		if noisy and total % progressInterval == 0:
			sys.stderr.write(str(right) + "/" + str(total) + " ")
			sys.stderr.flush()
			
	engine.quit()
	writeLog(logFile, logLines)  # make sure the last set is written
	sys.stderr.write("\n")
	return right, total, nodesUsed

################################################################################
##########  main  ##############################################################
################################################################################
runTot = len(weights)
runNum = 1
for weight in weights:  # loop over network weights, running problem set for each
	if nodes == None:
		appendix = str(time) + " msec"
	else:
		appendix = str(nodes) + " nodes"
	sys.stdout.write("\nRun " + str(runNum) + " of " + str(runTot) + ": " + weight + ", " + appendix + "\n")
	sys.stdout.flush()
	if nodes == None:
		agreed, total, nodesUsed = runTactics(epdPath, logFile, lc0_cmd, optString, weightPath, weight, moveTime=time)		
		outv = [weight,str(time), str(int(round(np.mean(nodesUsed)))), str(agreed),str(total),"%.3f" % ((100.0*agreed)/total)]		
	else:
		agreed, total, nodesUsed = runTactics(epdPath, logFile, lc0_cmd, optString, weightPath, weight, nodeNum=nodes)		
		outv = [weight,str(nodes), str(int(round(np.mean(nodesUsed)))), str(agreed),str(total),"%.3f" % ((100.0*agreed)/total)]
	outFile.write("\t".join(outv) + "\n")
	outFile.flush()
	sys.stdout.write("\n\n")
	runNum += 1

logFile.close()
outFile.close()
