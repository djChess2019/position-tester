import sys
import os
import re
import numpy as np
import chess
import chess.engine
import json
import datetime
import logging

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
logBuffer = 1
logging.basicConfig(level=logging.CRITICAL)
countOfBigEvalDifference = 0
totalNodesForFirstFind = 0
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
if "earlyStop" not in params:
    earlyStop = 1
else:
    earlyStop = params["earlyStop"]
    del params["earlyStop"]
if "tc" in params:
    del params["tc"]
if not appendingOut:  # write a header if this is a new output file
    # TODO correct outFile header line.
    outFile.write("network\treq_nodes\tavg_nodes\tagreed\ttotal\tpercent\tavg_1st_agree\n")
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


def writeLog(logFile2, logList):
    for val in logList:
        logFile2.write(val + "\n")
    logFile2.flush()  # so it can be monitored during run


def fillAgreeList(board, info, iccf_moves, agreeList, prevAgreement):
    agree = " " + board.san(info.get('pv')[0]) in iccf_moves

    nodesUsed = info.get('nodes')
    agreedLikePrevious = agree == prevAgreement
    if not agreedLikePrevious:
        toAppend = nodesUsed if agree else (nodesUsed * -1)
        agreeList.append(toAppend)
    # prevAgreement is really used, it is just in next loop iteration
    prevAgreement = agree
    return agree, prevAgreement

def runOnePosition(epd_field: str,
                   position_id: str,
                   iccf_moves: str,
                   engine: chess.engine.SimpleEngine):
    global countOfBigEvalDifference
    board = chess.Board(epd_field)

    agree = False
    agreeList = []
    prevAgreement = False
    infoForDebug = []
    # the detailedMoveInfo is available only when a limit is set AND then after it exits the loop.
    limit = chess.engine.Limit(nodes=maxNodes)
    with engine.analysis(board, limit, multipv=3, info=chess.engine.INFO_ALL, game=position_id) as analysis:
        for info in analysis:

            # Unusual stop condition.
            isFirstPv: bool = info.get('multipv') == 1
            if isFirstPv:
                # disable this in production only used with debugger break points
                # infoForDebug.append(info)
                agree, prevAgreement = fillAgreeList(board, info, iccf_moves, agreeList, prevAgreement)


    turn = "W" if board.turn == chess.WHITE else "B"
    # I there are two paths to here, on through the analaysis loop, the other in engine.Limit
    # engine.Limit permists use of the Leela details,
    # it also requires setting some variables here also.
    agree, prevAgreement = fillAgreeList(board, analysis.info, iccf_moves, agreeList, prevAgreement)
    agree2 = "1" if agree else "0"
    mpv = []
    for pv in analysis.multipv:
        score = str(pv['score'].relative.cp)
        move = board.san(pv['pv'][0])
        mpv.append([move, score])

    pieces = board.piece_map().__len__()

    # get the verbose-move-stats this is not yet finished
    # i decided I only want P for now
    v = analysis.inner.info.get('string')
    probability = 0
    if v:
        # values inside of quotes
        verbose = re.findall(r"\(.*?\)", v)
        verbose.pop(0)
        # example "(P: 7.17%)"
        # in verbose[1] find P don't include the %, [0] is first found.
        probability = round(float(re.findall("P: (.*?)(?=%)", verbose[1])[0].strip()) / 100, 4)
    # fill in mpv when it is short.
    # and will checking to see about the fill in just check for big eval also
    for x in range(3):
        try:
            if int(mpv[x][1]) > 300 and x == 0:
                countOfBigEvalDifference += 1
                print(f"\n{countOfBigEvalDifference}. Big eval for {position_id}, {int(mpv[x][1])}")
                continue
            if x == 0 and abs(int(mpv[0][1]) - int(mpv[1][1])) > 200:
                print()
                countOfBigEvalDifference += 1
                print(f"{countOfBigEvalDifference}. Big difference between pv 1 and 2 for position_id:{position_id},"
                      f" {mpv[0][1]} , {mpv[1][1]}")
        except IndexError:
            mpv.append([" ", "0"])
        continue

    r = [int(agree2),
         str.strip(iccf_moves),
         nodesUsed,
         int(position_id),
         turn,
         pieces,
         weight,
         mpv[0][0],
         int(mpv[0][1]),
         mpv[1][0],
         int(mpv[1][1]),
         mpv[2][0],
         int(mpv[2][1]),
         probability,
         agreeList.__len__(),
         agreeList
         ]

    return r


# def enginePlay(engine, board, iccfMoves, positionId):
#     result = engine.play(board, chess.engine.Limit(nodes=maxNodes), info=chess.engine.INFO_ALL)
#     agree3 = " " + board.san(result.info.get('pv')[0]) in iccfMoves
#     nodesUsed = result.info.get('nodes')
#     turn = "W" if board.turn == chess.WHITE else "B"
#     pieces = board.piece_map().__len__()
#     verbose = result.info.get("string")
#     agree4 = "1" if agree3 else "0"
#     return f'{agree4}, {str.strip(iccfMoves)}, {nodesUsed}, {positionId}, \
#     {turn},  {pieces}, {weight}, {verbose} '


# run one pass through an EPD tactics file with specific parameters
# returns (success, total, list of failures)
# maxNodes must be provided tc is not used
def runTactics(epdFile,
               logFile1,
               lc0_cmd2,
               weightPath2,
               weight2
               ):
    logLines = ['#### agree, iccf_moves, nodesUsed, position_id, toPlay, pieces Count, weight, mpv 1 move, mpv 1 eval',
                '#### mpv 2 move, mpv 2 eval,  mpv 3 move ; mpv3 eval, probability (P), count of agree List, agree List']
    global countOfBigEvalDifference
    countOfBigEvalDifference = 0
    global totalNodesForFirstFind
    totalNodesForFirstFind = 0
    #    logLines = ["result; iccfMove(s); nodes used; position_id; toPlay; pvList; piece_count; agreementNodesList"]

    engine = chess.engine.SimpleEngine.popen_uci(lc0_cmd2)
    for opt in params:
        if opt not in engine.options:
            for o in engine.options:
                print(o)
            print(f"you used '{opt}; in you setting.json available options are above")

    # add in the extra fixed params
    params["VerboseMoveStats"] = True
    params["WeightsFile"] = weightPath2 + weight2
    params["HistoryFill"] = "always"

    # put headers in the log and on screen.
    appendix2 = f" nodes= {str(maxNodes)} weight= {weight} earlyStop {earlyStop}"
    logFile1.write("#### " + lc0_cmd2 + appendix2 + "\n")
    sys.stderr.write(f"{lc0_cmd2}\n  nodes:{maxNodes}\n  weight:{weight}\n  earlyStop:{earlyStop}")
    logFile1.write(f"#### {json.dumps(params)}\n")
    sys.stderr.write(json.dumps(params, separators=(', ', ": "), indent=5))

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

        # if line2 == epdfl[5]: #helpful to debug just 5 lines of position set
        #    break

        positionId = line2.split(";")[1].strip()
        iccf_moves = " " + str(re.search('bm (.*);', line2).group(1)) + " "  # spaces must surround moves
        board = chess.Board(epd_field)
        # positionResult = enginePlay(engine, board, iccf_moves, positionId)

        # ---------------- RUN POSITION ---------------
        # noinspection PyBroadException
        try:
            positionResult = runOnePosition(epd_field,
                                            positionId,
                                            iccf_moves,
                                            engine)
        # it is intentional to catch all exceptions and move to next line
        except:
            print("error in runOnePosition for positionID: {positionID}")
            continue

        if positionResult[0] == 1:
            right += 1
        if positionResult[14]:  # count of finds
            totalNodesForFirstFind += positionResult[15][0]
        nodesUsed.append(positionResult[2])
        logLines.append(json.dumps(positionResult))

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
            # stop division by 0 when debugging and non are right.
            if right == 0:
                right = 1
            outv2 = ["\r" + str(right) + "/" + str(total2),
                     " Agree:" + percentAgree + "%",
                     "Expected end of this run: " + expectedEndTime,
                     "average nodes per move: " + "%.0f" % (np.average(nodesUsed)),
                     "average nodes first found of agreed: " + "%.0f" % (totalNodesForFirstFind / right)
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
        weightPath,
        weight
    )
    # stop error for testing when 0 agree
    if agreed == 0:
        agreed = 1
    outv = [weight, str(maxNodes), str(int(round(np.average(nodesUsedList)))), str(agreed), str(total),
            "%.3f" % ((100.0 * agreed) / total), "%.3f" % (totalNodesForFirstFind / agreed)]
    outFile.write("\t".join(outv) + "\n")
    outFile.flush()
    sys.stdout.write("\n\n")
    runNum += 1

positionTestLog.close()
outFile.close()
