import sys
import os
import re
import numpy as np
import chess
import chess.engine
import json
import datetime

#  TODO: this is the outline of how I feel it should work, program isn't structured to be like this yet.
#  these fileNames are contained in position-tester-settings.yaml
#  required files. 	1. an engine one setting for an engine is an optional single paramSetup
#  					2. for NN a network
#  					3. a position set
#  optional files. 	1. a list of nets
#  					2. a list of paramSetting files
#  					3. a list of engines.
#  the sample file "sample-position-tester-settings.yaml" will evolve with all settings notes and comments.
# for each engine
#     NOTE: an engine is exe but not the params
#     NOTE: for leela --history-fill=always is hard coded - no need for having it set in .json tc
#     NOTE tc is never used for any engine always nodes searched
# 	- for each param file (the param.json my have a network.path and/or network.list)
# 		NOTE: to test params auto create different param.files and add a paramFileList in position-tester-settings.json
#      - for each network (if NN). TODO: When missing the networkList file try exe. and query response to see what it found.
#  	      o send header to log and summary as needed
#         o for each position in file
#            + engine analized for xnodes and then sends the result to log
#         o send the sumary rusults

# as of May 16, 2019 these are up to avoid magic strings, but probably won't be changing.
progressInterval = 1
logBuffer = 10

# TODO: reorganize so all args are in one file - the only command line option is one settings file name.
# file with a simple list of networks to test, 1 per line. path taken from json
netsFileName = sys.argv[1]
# configuration file for paths and Leela parameters
jsonFileName = sys.argv[2]
# the output file will have a bare bones summary of parameters and success rate
outFileName = sys.argv[3]
# the log file will contain a simple summary of failed problems
logFileName = sys.argv[4]

positionTestLog = open(logFileName, "a")
appendingOut = os.path.exists(outFileName)
outFile = open(outFileName, "a")

# set up command and paths from the json file, removing them as you go
# some commands are ok, even required in the .json but can't be in engine params this will be fixed with yaml
params = json.load(open(jsonFileName))
epdPath = params["EPD"]
del params["EPD"]
lc0_cmd = params["Lc0"]
del params["Lc0"]
weightPath = params["weights_path"]
del params["weights_path"]
nodes = None
if "nodes" in params:
    maxNodes = params["nodes"]
    del params["nodes"]
else:
    maxNodes = 100
if "stop_first" not in params:
    stop_first = False
else:
    stop_first = params["stop_first"]
    del params["stop_first"]
if "found_three_times" not in params:
    found_three_times = False
else:
    found_three_times = params["found_three_times"]
    del params["found_three_times"]

if "tc" in params:
    del params["tc"]
if not appendingOut:  # write a header if this is a new output file
    # TODO correct outFile header line.
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
optionString = " ".join(optList)

weights = []
theOpenFile = open(netsFileName)
for line in theOpenFile:
    if len(line) > 2 and not line.startswith("#"):
        netw = line.strip()
        if not os.path.exists(weightPath + netw):
            sys.stderr.write("weight file not found: " + weightPath + netw + "\n")
            sys.exit(1)
        weights.append(netw)
theOpenFile.close()


#############################################################################
########### stuff for each run
#############################################################################
def movesToString(moveList):
    mls = []
    for m in moveList:
        mls.append(str(m))
    return " ".join(mls)


def writeLog(logFile2, logList):
    for val in logList:
        logFile2.write(val + "\n")
    logFile2.flush()  # so it can be monitored during run


def runOnePosition(epd_field: str,
                   maxNodes3,
                   position_id: str,
                   tcec_moves: str,
                   stop_first_found: bool,
                   found_three_times: bool,
                   engine: chess.engine.SimpleEngine):
    board = chess.Board(epd_field)
    count_found: int = 0
    agree = False
    with engine.analysis(board, multipv=3, info=chess.engine.INFO_ALL) as analysis:
        for info in analysis:

            # Unusual stop condition.
            is_first_pv: bool = info['multipv'] == 1
            agree = is_first_pv and " " + board.san(info['pv'][0]) in tcec_moves
            if agree:
                count_found += 1
            # if is_first_pv:
            #      print (info['multipv'], board.san(info['pv'][0]), tcec_moves,
            #      info.get('score'), info.get("nodes", 0), info['time'])
            #      atest = board.san(info['pv'][0])
            #      btest = tcec_moves
            if info.get("nodes", 0) > maxNodes3:
                break
            if agree and stop_first_found:
                break
            if found_three_times and count_found == 3:
                agree = True
                break

    turn = "W" if board.turn == chess.WHITE else "B"
    agree2 = "1" if agree else "0"
    mpv = []
    for info in analysis.multipv:
        score = str(info['score'].relative.cp)
        move = board.san(info['pv'][0])
        mpv.append([move, score])
    mpv2 = json.dumps(mpv)
    # TODO this is header print line
    #  print("agree, tcec_moves, nodesUsed, positionId, toPlay, multiPv[move, eval cp]")
    nodesUsed = int(info.get('nodes'))

    return f'{agree2}, {str.strip(tcec_moves)}, {nodesUsed}, {position_id}, {turn}, {mpv2}'


# run one pass through an EPD tactics file with specific parameters
# returns (success, total, list of failures)
# maxNodes must be provided tc is not used
def runTactics(epdFile,
               logFile1,
               lc0_cmd2,
               optString2,
               weightPath2,
               weight2):
    logLines = ["result; engine_move; iccf_move(s); nodes; problem_id; network; side; piece_count; evaluation"]
    appendix2 = " nodes=" + str(maxNodes)
    logFile1.write("#### " + lc0_cmd2 + appendix2 + "\n")
    sys.stderr.write(lc0_cmd2 + appendix2 + "\n")

    # TODO add options back in
    # it can't be in after file name like it was
    # options2 = " --weights=" + weightPath2 + weight2 + " --history-fill=always " + optString2
    engine = chess.engine.SimpleEngine.popen_uci(lc0_cmd2)
    for opt in params:
        if opt not in engine.options:
            print(f"you used '{opt}; in you setting.json available options are:")
            for o in engine.options:
                print(o)
            exit()
    params["WeightsFile"] = weightPath2 + weight2
    params["HistoryFill"] = "always"

    engine.configure(params)
    # TODO use a more generic method. epdfLines = readAllLineFrom(epdFileName)  probably not on level of forEachNet
    epdf = open(epdFile)
    epdfLines = epdf.readlines()
    epdf.close()
    epdfl = []
    for eline in epdfLines:
        if not eline.startswith("#"):
            epdfl.append(eline)
    sys.stderr.write("\n" + str(len(epdfl)) + " problems... ")
    right = 0
    total2 = 0
    nodesUsed = []

    for line2 in epdfl:
        epd_field = line2.split("bm ")[0].strip()
        positionId = line2.split(";")[1].strip()
        tcec_moves = " " + str(re.search('bm (.*);', line2).group(1)) + " "  # spaces must surround moves
        # TODO add ECO so it can be entered for each position output in log
        positionResult = runOnePosition(epd_field,
                                        maxNodes,
                                        positionId,
                                        tcec_moves,
                                        stop_first,
                                        found_three_times,
                                        engine)
        resultfields = positionResult.split(",")
        if int(resultfields[0]) == 1:
            right += 1

        nodesUsed.append(int(resultfields[2]))
        # if move in best_moves:
        # 	right += 1
        # 	logLines.append("; ".join(["1",str(move),bmstr,str(mnodes),idfield,weight2,side,str(pieceNum),evalstr]))
        #
        # else:
        # 	pv = info_handler.info["pv"][1]  # a list of the Move objects from the pv
        logLines.append(positionResult)

        if len(logLines) > logBuffer - 1:
            writeLog(logFile1, logLines)
            logLines = []
        total2 += 1

        if total2 % progressInterval == 0:
            elapsedTime = datetime.datetime.now() - startTime
            problems = len(epdfl)
            timePerProblem = elapsedTime / total2
            expectedEndTime = ((timePerProblem * problems) + startTime).isoformat(' ', 'minutes')
            percentAgree = str(round(right / total2 * 100, 2))
            outv2 = ["\r" + str(right) + "/" + str(total2),
                     " Agree:" + percentAgree + "%",
                     "Expected end of this run: " + expectedEndTime,
                     "mean nodes per move: " + str(int(round(np.mean(nodesUsed)))),
                     "stop_first: " + str(stop_first),
                     "found_three_times: " + str(found_three_times),
                     "maxNodes: " + str(maxNodes) + "                     "
                     ]
            sys.stderr.write(", ".join(outv2))
            sys.stderr.flush()

    engine.quit()
    writeLog(positionTestLog, logLines)  # make sure the last set is written
    sys.stderr.write("\n")
    return right, total2, nodesUsed


################################################################################
##########  main  ##############################################################
################################################################################
runTot = len(weights)
runNum = 1
for weight in weights:  # loop over network weights, running problem set for each
    startTime = datetime.datetime.now()
    appendix = str(maxNodes) + " nodes"

    sys.stdout.write("\nRun " + str(runNum) + " of " + str(runTot) + ": " + weight + ", " + appendix + "\n")
    sys.stdout.flush()
    # run the test for this network
    agreed, total, nodesUsedList = runTactics(
        epdPath,
        positionTestLog,
        lc0_cmd,
        optionString,
        weightPath,
        weight
    )
    outv = [weight, str(maxNodes), str(int(round(np.average(nodesUsedList)))), str(agreed), str(total),
            "%.3f" % ((100.0 * agreed) / total)]
    outFile.write("\t".join(outv) + "\n")
    outFile.flush()
    sys.stdout.write("\n\n")
    runNum += 1

positionTestLog.close()
outFile.close()
