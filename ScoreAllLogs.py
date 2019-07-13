# given a json param file name (optional)
# load and score all logs in a directory
# You may give a position set list
# and a node count.
# Sample JSON
# {
#   "positionSet":"../position-sets/testSet1",
#   "nodes":3000,
# }
import os
import re
import json
import csv
import copy
# many programs here depend on common functions
import sys

# --------------- 3rd party libraries -------------------
#   http://www.grantjenks.com/docs/sortedcontainers/
from sortedcontainers import SortedSet
#   https://viralogic.github.io/py-enumerable/
from py_linq import Enumerable
#   when working with AB this is needed
#   https://pypi.org/project/engineering-notation/
from engineering_notation import EngNumber

# ------- local imports

sys.path.append('/classesAndUtil')
sys.path.append(os.path.join(sys.path[0], 'bin'))
from PositionTesterLogItemClass2 import PositionTesterLogItem
from ChangeItemClass import ChangeItem

# --------------------------------------------------------------
# use files from your personal directory ignored in a github commit.
ScoreAllLogsDir = r"..\ignored\ScoreAllLogs"


def getParams():
    global params
    # I dislike command line args!!!
    if len(sys.arg) > 0:
        # assume you want to use the ignored directory above
        jsonFileName = ScoreAllLogsDir + sys.argv[1]
        if not sys.exist(jsonFileName):
            jsonFileName = sys.argv[1]
            if not os.path.exists(jsonFileName):
                print(f"json file, '{jsonFileName}' wasn't found. ")
                exit(-1)
    else:
        jsonFileName = ScoreAllLogsDir + "\settings.json"
        if not os.path.exists(jsonFileName):
            print(f"json file, '{jsonFileName}' wasn't found. ")
            exit(-1)

    params = json.load(open(jsonFileName))


def validateParams():
    pass


def main():
    getParams()
    x = 1

    allLog = SortedSet()
    errorNo = 0
    for line in theOpenFile:
        if line.startswith("#"):
            continue
        if line.startswith("result, logSet"):
            continue
        if len(line) > 20:
            x += 1
            if x % 10000 == 0:
                print(f'{int(x / 1000):,}')
            try:
                p: PositionTesterLogItem = PositionTesterLogItem(line, 1)
                if not allLog.__contains__(p):
                    allLog.add(p)
                else:
                    t4 = 1

            except Exception as e:

                print(f'error {errorNo}:{e}')
                errorNo += 1

    theOpenFile.close()
    agList = []
    # remove duplicates

    # for each position id,
    #     remove duplicates
    #     build a list of (positionId, number of networks that found it, sum of all agrees all nets)
    for k in range(1, 200000):
        l = list(allLog.irange_key(k, k))
        if len(l) > 0:
            # if your going to save the entire list or compare other features then do a clean up.
            for item in l:
                agList.append((k, enu.count(), enu.sum(lambda x: x.agree)))
                print(agList[-1])

    with open('ur frequencyEasy20k.csv', 'w') as out:
        csv_out = csv.writer(out)
        csv_out.writerow(['positionID', 'count', 'agree'])
        for row in agList:
            csv_out.writerow(row)
    groups = Enumerable(agList).group_by(key_names=['id', 'count', 'agree'], key=lambda x: x[2])

    countList = []
    for g in groups:
        countList.append((g.count(), g.first()[2]))

    with open('countlist.csv', 'w') as out:
        csv_out = csv.writer(out)
        csv_out.writerow(['howManyPositions', 'AgreeCount'])
        for row in countList:
            csv_out.writerow(row)

    tmp55 = 1


def selectionExamples():
    chosenAt1K = my_collection.where(lambda x: x.isAgreedAt(EngNumber('1k')) == True)
    chosenAt1kButFinalLostAfter6k = chosenAt1K.where(lambda x: x.changeList[-1] > EngNumber('6k'))
    foundOnce = my_collection.where(lambda x: x.changeCount > 0)
    policyAgree = foundOnce.where(lambda x: x.changeList[1] <= 6)
    totalCount = my_collection.count()
    percentAgreedOnce = foundOnce.count() / totalCount
    policyLoses = policyAgree.where(lambda x: x.changeCount > 1)
    policyLostBetween10and50 = policyAgree.where(lambda x: Enumerable(x.changeList).any(lambda z: -10 >= z >= -50))


# ############################## Run ##############################
if __name__ == "__main__":
    main()
