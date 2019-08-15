import sys
import os
import re
from datetime import datetime

import numpy as np
import chess
import chess.engine
import json
import datetime
import logging
import time
logging.basicConfig(level=logging.CRITICAL)

def writeLog(logList):
    # uses the global open file positionLogFile
    for val in logList:
        positionLogFile.write(val + "\n")
    positionLogFile.flush()  # so it can be monitored during run


# ############### constants
class CONST(object):
    __slots__ = ()
    progressInterval = 1
    logBuffer = 1


CONST = CONST()

# ########### comand line params
# TODO: reorganize so all args are in one file - the only command line option is one settings file name.
# file with a simple list of networks to test, 1 per line. path taken from json
netsFileName = sys.argv[1]  # todo make this a list variable in Json
# configuration file for paths and Leela parameters
jsonFileName = sys.argv[2]  # todo make this optional use a default Position-Tester-PTsettings.json
# the output file will have a bare bones summary of parameters and success rate
outFileName = sys.argv[3]  # todo make this a list variable in Json
# the log file will contain a simple summary of failed problems
logFileName = sys.argv[4]  # todo make this a list variable in Json

# ############# globals - please note what function has edit
# set up command and paths from the json file, removing them as you go
# some commands are ok, even required in the .json but can't be in engine params

params = json.load(open(jsonFileName))
# positionResult
# built in runOnePosition() this is what will go to the log, it is read in runOnePositionSet;

class PvItem:
    def __init__(self, move: str, score: int):
        self.move = move
        self.score = score

    def __str__(self):
        return f"{self.move}, {self.score}"


class BestMoveChange:
    def __init__(self, nodes: int, time: float, move: str, score: int):
        self.nodes = nodes
        self.mv = move
        self.score = score
        self.time = time

    def __str__(self):
        return f"[{self.nodes}, {self.mv}, {self.time}, {self.score}]"


class LogOutput:

    def __init__(self, agree: int, iccfMoves: str, nodesUsed: int, positionId: str, turn: str,
                 pieces: int, networkName: str, probability: float, mpv: [PvItem],
                 bestMoveChangeList: [BestMoveChange]):
        self.agree = agree
        self.iccfMoves = iccfMoves
        self.nodesUsed: int = nodesUsed
        self.positionId: str = positionId
        self.turn: str = turn
        self.pieces: int = pieces
        self.networkName: str = networkName
        self.probability: float = probability
        self.mpv: [PvItem] = mpv

        self.bestMoveChangeList: [BestMoveChange] = bestMoveChangeList

    def __str__(self):

        listStr = ""
        for name, value in vars(self).items():
            x = type(value)
            if x == list:
                continue
            else:
                listStr += f", {str(value)}"  # it is intentional that strings will not be quoted.

        for i in self.mpv:
            listStr += f", {str(i)}"
        # add in the count of agreeChanges and an open list
        listStr += f", {str(len(self.bestMoveChangeList))}, ["

        # no agreement list
        if len(self.bestMoveChangeList) == 0:
            listStr += "[]"
        else:
            for i in self.bestMoveChangeList:
                if self.bestMoveChangeList.index(i) > 0:
                    listStr += f", "
                listStr += f"{str(i)}"

        # close the agree change list
        listStr += "]"

        return listStr[-(len(listStr) - 2):]  # the opening ", "

    def firstAgree(self):
        if len(self.bestMoveChangeList) == 0:
            return 0
        for bm in self.bestMoveChangeList:
            if bm.nodes > 0:
                return bm.nodes
        return 0

    def isAgreeAt(self, nodeCount):
        if len(self.bestMoveChangeList) == 0:
            return False
        for bm in self.bestMoveChangeList:
            if abs(bm.nodes) >= nodeCount:
                return bm.nodes > 0

        return False  # todo change this to return the index of bm found non 0 is agreeAt

    # if isAgreeAt is true then return the last prior agreement
    # I believe the average should go down for postions found by canidates, where found in all
    def agreePriorTo(self, nodeCount):
        if not self.isAgreeAt(nodeCount):
            return 0
        # Since it is an agree start accept the item of agreement in the list.


# required to be in .json but not part of engine params
epdPath = params["EPD"]
del params["EPD"]
enginePath = params["enginePath"]
del params["enginePath"]
if "lc0" in params:
    enginePath = params["lc0"]
    del params["lc0"]
if "lc0" in enginePath:
    isLeela = True
    # Leela specific options we want to change default for better testing
    if "SmartPruningFactor" not in params:
        params["SmartPruningFactor"] = 1
    if "Threads" not in params:
        params["Threads"] = 1
    params["backend"] = "cudnn-fp16"

else:
    isLeela = False

if "nodes" in params:
    maxNodes = params["nodes"]
    del params["nodes"]
    limitString = str(maxNodes) + " nodes"
else:
    if "tc" in params:
        tc = params["tc"]
        del params["tc"]
        limitString = str(tc) + " seconds"

    else:
        maxNodes = 100
        limitString = str(maxNodes) + " nodes"
# weight path gets combined with weight in runOnePositionSet
weights = []
if isLeela:
    weightPath = params["weights_path"]  # a required field for leela
    del params["weights_path"]
else:
    weightPath = ""

# earlyStop is no longer used.
# there is an agreement of 0.01 * maxNodes
if "earlyStop" in params:
    del params["earlyStop"]

#

countOfBigEvalDifference = 0  # changed in runOnePositionSet()
totalNodesForFirstFind = 0  # changed in RunOnePositionSet()
positionLogFile = open(logFileName, "a")  # only set here
writeHeaderLineToSummaryOutput: bool = not os.path.exists(outFileName)  # only set here
outFile = open(outFileName, "a")  # only Set here and left open

if writeHeaderLineToSummaryOutput:  # write a header if this is a new output file
    # TODO check outFile header line.
    outFile.write("network\treq_nodes\tavg_nodes\tagreed\ttotal\tpercent\tavg_1st_agree\n")
    outFile.flush()

# get the rest of the options in alphabetic order
# todo remove this file and use a json list
if isLeela:

    networkFile = open(netsFileName)
    for line in networkFile:
        if len(line) > 2 and not line.startswith("#"):
            network = line.strip()
            if not os.path.exists(weightPath + network):
                sys.stderr.write("weight file not found: " + weightPath + network + "\n")
                sys.exit(1)
            weights.append(network)
    networkFile.close()
    # add in the extra fixed params
    params["VerboseMoveStats"] = True
    params["HistoryFill"] = "always"


# using the global positionList fill it from the position file. Todo this seems like a waist of memory 100k??
def readPositions():
    global positionList
    epdf = open(epdPath)  # only set here left open
    epdfLines = epdf.readlines()
    epdf.close()
    positionList = []
    # todo make a class for positions
    for eline in epdfLines:
        if not eline.startswith("#"):
            positionList.append(eline)
    sys.stderr.write(f"\n {len(positionList)}  problems... ")


def fillAgreeList(board, info, iccf_moves, moveChangeList: [BestMoveChange]):
    engineMove = " " + board.san(info.get('pv')[0])
    agree = engineMove in iccf_moves
    nodesUsed = info.get('nodes')

    if len(moveChangeList) == 0:
        isMoveChange = True
    else:
        isMoveChange = moveChangeList[len(moveChangeList) - 1].mv != engineMove
    if isMoveChange:
        nodes2 = nodesUsed if agree else (nodesUsed * -1)
        if info['score'].white().is_mate():
            eval3 = 9999
        elif type(info['score']) == chess.engine.PovScore:
            eval3 = info.get("score").relative.cp
        else:
            eval3 = "9998"
        time = info['time']
        toAppend: BestMoveChange = BestMoveChange(nodes2, time, engineMove, eval3)
        moveChangeList.append(toAppend)
    # prevAgreement is really used, it is just in next loop iteration
    # todo agree and nodesUsed needed in parent now that I have a list?
    return agree, nodesUsed


def getProbability(verbose):
    # example "(P: 7.17%)"
    # find P don't include the %, [0] is first found.
    P = re.findall("P: (.*?)(?=%)", verbose)
    p1 = float(P[0].strip())
    probability = round(p1 / 100, 4)
    return probability


def runOnePosition(positionLine: str, engine: chess.engine.SimpleEngine):
    fen = positionLine.split("bm ")[0].strip()
    positionId = positionLine.split(";")[1].strip()
    iccf_moves = " " + str(re.search('bm (.*);', positionLine).group(1)) + " "  # spaces must surround moves

    board = chess.Board(fen)
    agreeList = []
    prevAgreement = False
    # infoForDebug = []
    # the detailedMoveInfo is available only when a limit is set AND then after it exits the loop.
    if "tc" in globals():
        limit = chess.engine.Limit(time=tc)
    else:
        limit = chess.engine.Limit(nodes=maxNodes)
    with engine.analysis(board, limit, multipv=3, info=chess.engine.INFO_ALL, game=positionId) as analysis:
        for info in analysis:

            # Unusual stop condition.
            isFirstPv: bool = info.get('multipv') == 1
            if isFirstPv:
                # disable this in production only used with debugger break points
                # infoForDebug.append(info)
                agree, nodesUsed = fillAgreeList(board, info, iccf_moves, agreeList)
                # no longer needed I use Limit now
                # if 'maxNodes' in globals() and nodesUsed > maxNodes:
                #    break

    turn = "W" if board.turn == chess.WHITE else "B"
    # I there are two paths to here, on through the analaysis loop, the other in engine.Limit
    # engine.Limit permists use of the Leela details,
    # it also requires setting some variables here also.
    agree, nodesUsed = fillAgreeList(board, analysis.info, iccf_moves, agreeList)
    agree2 = "1" if agree else "0"
    mpv = []
    for pv in analysis.multipv:
        if type(pv['score'].relative) == chess.engine.Mate:
            score = 9999
        else:
            score = str(pv['score'].relative.cp)

        move = board.san(pv['pv'][0])
        mpv.append([move, score])

    pieces = board.piece_map().__len__()

    # get the verbose-move-stats this is not yet finished
    # i decided I only want P for now
    verbose = analysis.inner.info.get('string')
    probability = getProbability(verbose) if verbose else 0

    # fill in mpv when it is short.
    # and will checking to see about the fill in just check for big eval also
    for x in range(3):
        global countOfBigEvalDifference
        try:
            if int(mpv[x][1]) > 300 and x == 0:
                countOfBigEvalDifference += 1
                # print(f"\n{countOfBigEvalDifference}. Big eval for {position_id}, {int(mpv[x][1])}")
                continue
            if x == 0 and abs(int(mpv[0][1]) - int(mpv[1][1])) > 200:
                # print()
                countOfBigEvalDifference += 1
                # print(f"{countOfBigEvalDifference}. Big difference between pv 1 and 2 for position_id:{position_id},"
                #    f" {mpv[0][1]} , {mpv[1][1]}")
        except IndexError:
            mpv.append([" ", "0"])
        continue
    outputMpv = [PvItem(mpv[0][0], mpv[0][1]),
                 PvItem(mpv[1][0], mpv[1][1]),
                 PvItem(mpv[2][0], mpv[2][1])]

    r = LogOutput(int(agree2), str.strip(iccf_moves), nodesUsed, positionId, turn, pieces,
                  weight, probability, outputMpv, agreeList)

    return r


# explain to user why a parm isn't valid,
# can only validate after engine is created.
def validateEngineParameters(engine):
    for opt in params:
        if opt not in engine.options:
            for o in engine.options:
                print(o)
            print(f"you used '{opt}; in you setting.json available options are above")
            exit()


# put headers in the log and on screen.
def sendPositionSetHeaders(startTime):
    positionLogFile.write(f"# engine:{enginePath},n# {limitString},\n# params:{params.__str__()},\n")
    positionLogFile.write(f"# epd:{epdPath},\n# {logFileName},\n# start Time {str(startTime)}\n")
    # writeLog(params)
    # writeLog(str(startTime)) tt

    sys.stderr.write(f" {enginePath}\n  nodes:{limitString}\n  weight:{weight}\n ")
    sys.stderr.write(json.dumps(params, separators=(', ', ": "), indent=5))
    sys.stderr.write("\n")
    sys.stderr.write(
        f"*** if you need to pause all instances runing just create a file named \'pause-Position-tester.txt\' \n ")


# run one pass through an EPD tactics file with specific parameters
# returns (percentAgree, total, nodesUsed)
# maxNodes global must be provided tc is not used
# all variables are global now
def runOnePositionSet():
    logLines = ['# agree, iccf_moves, nodesUsed, position_id, toPlay, \
pieces Count, weight, mpv 1 move, mpv 1 eval, \
mpv 2 move, mpv 2 eval,  mpv 3 move , mpv3 eval,\
probability (P), count MvChange, Mv Change List']
    global totalNodesForFirstFind
    totalNodesForFirstFind = 0
    engine = chess.engine.SimpleEngine.popen_uci(enginePath)
    validateEngineParameters(engine)
    engine.configure(params)
    # TODO use a more generic method. epdfLines = readAllLineFrom(epdFileName)  probably not on level of forEachNet
    right = 0
    total2 = 0
    nodesUsed = []

    for positionLine in positionList:

        # if positionLine == positionList[5]: #helpful to debug just 5 lines of position set
        #    break

        # check for a pause file
        while os.path.exists(".\\pause-Position-tester.txt"):
            sys.stderr.write("\rpaused delete pause-Position-tester.txt to continue:")
            time.sleep(60)


        # try:

        positionResult: LogOutput = runOnePosition(positionLine, engine)
        # # it is intentional to catch all exceptions and move to next line
        # # I do this so the rest of the positions can be worked even if one errors.
        # except IndexError:
        #     print(f"error in runOnePosition read position from screen output")
        #     continue

        if positionResult.agree == 1:
            right += 1
        if len(positionResult.bestMoveChangeList) > 0:  # count of finds
            totalNodesForFirstFind += positionResult.firstAgree()
        else:
            totalNodesForFirstFind += maxNodes * 2  # todo find formula, how long for future find on average
        nodesUsed.append(positionResult.nodesUsed)
        logLines.append(str(positionResult))

        if len(logLines) > CONST.logBuffer - 1:
            writeLog(logLines)
            logLines = []
        total2 += 1
        # I use right in the math, non sense when 0
        if total2 % CONST.progressInterval == 0 and right > 1:
            elapsedTime = datetime.datetime.now() - startTime
            problems = len(positionList)
            timePerProblem = elapsedTime / total2
            expectedEndTime = ((timePerProblem * problems) + startTime).isoformat(' ', 'minutes')
            percentAgree = str(round(right / total2 * 100, 2))
            # stop division by 0 when debugging and non are right.
            outv2 = ["\r" + str(right) + "/" + str(total2),
                     " Agree:" + percentAgree + "%",
                     "Expected end of this run: " + expectedEndTime,
                     "average nodes per move: " + "%.0f" % (np.average(nodesUsed)),
                     # now I am adding maxNodes*2 for never found so I divide by total
                     "average nodes first found of agreed: " + "%.0f" % (totalNodesForFirstFind / total2)
                     ]
            sys.stderr.write(", ".join(outv2))
            sys.stderr.flush()

    engine.quit()
    writeLog(logLines)  # make sure the last set is written
    sys.stderr.write("\n")
    return right, total2, nodesUsed


# ###############################################################################
# #########  main  ##############################################################
# ###############################################################################
def main():
    readPositions()
    if isLeela:
        runTot = len(weights)  # the weights list is made about line 120 in global . why?
        runNum = 1
        global weight
        global startTime

        for weight in weights:  # loop over network weights, running problem set for each
            startTime = datetime.datetime.now()

            appendix = limitString
            params["WeightsFile"] = weightPath + weight
            sendPositionSetHeaders(startTime)
            sys.stdout.write("\nRun " + str(runNum) + " of " + str(runTot) + ": " + weight + ", " + appendix + "\n")
            sys.stdout.flush()
            # run the test for this network
            agreed, total, nodesUsedList = runOnePositionSet()
            # stop error for testing when 0 agree
            if agreed == 0:
                agreed = 1
            outv = [weight, limitString, str(int(round(np.average(nodesUsedList)))), str(agreed), str(total),
                    "%.3f" % ((100.0 * agreed) / total), "%.3f" % (totalNodesForFirstFind / total)]
            outFile.write("\t".join(outv) + "\n")
            outFile.flush()
            sys.stdout.write("\n\n")
            runNum += 1
            positionLogFile.write(f"End Time:{datetime.datetime.now()}")
    else:
        startTime = datetime.datetime.now()
        weight = " "
        agreed, total, nodesUsedList = runOnePositionSet()
    positionLogFile.close()
    outFile.close()


if __name__ == "__main__":
    main()
