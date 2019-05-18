import sys
import re
from typing import List

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
nodes = params["nodes"]
del params["nodes"]
############################################################
def runOnePosition(epd_field: string,
				   tcec_moves: string,
				   stop_first_found: bool,
				   found_three_times: bool,
				   engine: chess.engine.SimpleEngine) -> string:

    board = chess.Board(epd_field)
    count_found: int = 0
    info2 = []
    agree = False
    with engine.analysis(board, multipv=3, info=chess.engine.INFO_ALL) as analysis:
        for info in analysis:
            print(board.san(info['pv'][0]),info.get('score'), info.get("nodes", 0), info['time'])
            info2.append(info)
            # Unusual stop condition.
            is_first_pv:bool = info['multipv'] == 1
            if is_first_pv and " " + board.san(info['pv'][0]) in tcec_moves:
                if stop_first_found:
                    agree = True
                    break
                count_found += 1
                if found_three_times and count_found == 3:
                    agree = True
                    break
            if info.get("nodes", 0) > 400000:
                break
    turn = "W" if board.turn == chess.WHITE else "B"
    agree2 = "1" if agree else "0"
    mpv = []
    for info in analysis.multipv:
        score = str(info['score'].relative.cp)
        move = board.san(info['pv'][0])
        mpv.append([move, score])
    mpv2 = json.dumps(mpv)
    #print("agree, tcec_moves, nodes, positionId, toPlay, multiPv[move, eval cp]")
    nodes1 = int(info.get('nodes'))
    position_id = 7777
    return f'{agree2}, {str.strip(tcec_moves)}, {nodes1}, {position_id}, {turn}, {mpv2}'


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
# returns (success, total, averageNodes)
# always nodes, moveTime is not used, there isn't time control on positions.
def runTactics(epdPath1, logFile, lc0_cmd1, optString, weightPath, weight, nodeNum):
    startTime = datetime.datetime.now()
    logLines1 = ["result; engine_move; iccf_move(s); nodes; problem_id; network; side; piece_count; evaluation"]
    # no options right now
    # lc0_cmd += " --weights=" + weightPath + weight + " --history-fill=always " + optString

    appendix = " nodes=" + str(nodeNum)
    logFile.write("#### " + lc0_cmd1 + appendix + "\n")
    sys.stderr.write(lc0_cmd1 + appendix + "\n")

    engine = chess.engine.SimpleEngine.popen_uci(lc0_cmd1)


    epdf = open(epdPath1)
    epdfLines = epdf.readlines()
    epdf.close()
    epdfl = []
    for eline in epdfLines:
        if not eline.startswith("#"):
            epdfl.append(eline)
    sys.stderr.write("\n" + str(len(epdfl)) + " problems... ")
    right = 0
    total = 0

    for line in epdfl:
        fields: List[str] = line.split(";")
        epdField = fields[0].strip()
        # will use match to keep bm but for now just remove it
        epdField = re.sub(' bm .*', '', epdField)
        tcec_moves = str(re.search('bm (.*;)').group(1))
        engine = chess.engine.SimpleEngine.popen_uci(lc0_cmd1)
		stop_first = True
		found_three_times = False
		result = runOnePosition(epdField,
			tcec_moves,
			stop_first,
			found_three_times,
			engine)
        #		info = engine.analyse(board, chess.engine.Limit(nodes=100))
        if int(result.split(",")[0]) == 1 :
            right += 1
        logLines1.append(result)


        if len(logLines1) > logBufferSize - 1:
            writeLog(logFile, logLines1)
            logLines = []
        total += 1

        if total % progressInterval == 0:
            showProgress(epdfl, right, startTime, total)


def showProgress(epdfl, right, startTime, total):
	elapsedTime = datetime.datetime.now() - startTime
	problems = len(epdfl)
	timePerProblem = elapsedTime / total
	expectedEndTime = ((timePerProblem * problems) + startTime).isoformat(' ', 'minutes')
	percentAgree = str(round(right / total * 100, 2))
	sys.stderr.write("\r" + str(right) + "/" + str(
		total) + " Agree:" + percentAgree + "%  Expected end of this run:" + expectedEndTime + "            ")
	sys.stderr.flush()


engine.quit()
    writeLog(logFile, logLines)  # make sure the last set is written
    sys.stderr.write("\n")
    return right, total, nodesUsed

