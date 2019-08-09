import re
import json
import shutil
import sys
import os
import csv
from py_linq import Enumerable
from engineering_notation import EngNumber
from pathlib import Path
from pprint import pprint
import zipfile

# the program expects a directory with one or more zipped logs.
if len(sys.argv) == 1:
    print("\n\n **** A directory name where zipped logs are found is required *****")
    exit()
directoryName = sys.argv[1]
my_collection = Enumerable()


class ChangeItem:
    def __init__(self, nodeCount, move, eval):
        self.nodeCount = int(nodeCount.strip("[").strip("]"))
        self.move = move
        self.eval = int(eval.strip("[").strip("]"))


class PositionTesterLogItem:
    # this section probably works for 610
    # def __init__(self, line1: str, logNu: int):
    #     inputList = json.loads(line1)
    #     self.agree, self.iccf, self.nodesUsed, \
    #     self.positionId, self.toMove, self.pieces, \
    #     self.network, = inputList[0:7]
    #     self.pvs = [inputList[7:9], inputList[9:11], inputList[11:13]]
    #
    #     self.changeCount = inputList[14]
    #     self.changeList = inputList[15]
    #     self.logSet = logNu

    def __init__(self, line1: str, logNu: int):
        inputList = line1.strip('\n').split(", ")
        self.agree = int(inputList[0])
        self.iccf = str(inputList[1])
        self.nodesUsed = int(inputList[2])
        self.positionId = str(inputList[3])
        self.toMove = str(inputList[4])
        self.pieces = int(inputList[5])
        self.network = str(inputList[6])
        self.pvs = [[float(inputList[7]), str(inputList[8])], \
                    [float(inputList[9]), str(inputList[10])], \
                    [float(inputList[11]), str(inputList[12])]]
        self.probability = int(inputList[13])
        self.changeCount = int(inputList[14])
        index = 15
        self.changeList = []
        for x in range(self.changeCount):
            # nodeCount, move, eval
            self.changeList.append(ChangeItem(inputList[index], inputList[index + 1], inputList[index + 2]))
            index += 3

        self.logSet = logNu

    def isAgreedAt(self, targetNodeCount: int) -> bool:
        """

        :rtype: object
        """
        if self.changeCount == 0:
            return False
        lastEntry = self.changeList[-1]
        # example entries [ 20, -100]
        # targetNodeCount = 300; if |-100| < 300 return (-100 > 0)  so return false
        if abs(lastEntry.nodeCount) <= targetNodeCount:
            # agree is when lastEntry.nodeCount not a negative
            return lastEntry.nodeCount > 0
        firstEntry = self.changeList[0]
        # targetNodeCount = 10; if 20 > 10 then it was first found later return False
        if abs(firstEntry.nodeCount) > targetNodeCount:
            return False
        tmpResult = False
        for item in self.changeList:
            nodeCount = item.nodeCount
            if targetNodeCount >= abs(nodeCount):
                tmpResult = nodeCount > 0
            else:
                return tmpResult
        return False


# def saveSlice(set, centered, count):
#     # create name
#     # example: "sliceOf-SF10_10M-1M-20k"
#
#     fName = fullPath.split("\\")[-1].split(".")[0]
#     name = f"sliceOf-{fName}-{centered},{count}"
#     # handle exists
#     #  for now just overwrite
#     # os.path.exists(weightPath + network):
#     file = open(name, "w")
#     file.write(json.dumps(set.select(lambda x: x.positionId).to_list()))
#     file.close()
# this method was written for 610
# def changedInRange(item: PositionTesterLogItem, minNodes1: int, maxNodes1: int) -> bool:
#     # last entry in change list is less than min nodes
#     if minNodes1 > abs(item.changeList[-1]):
#         return False
#     # first entry in changeList > maxNodes
#     if maxNodes1 < abs(item.changeList[0]):
#         return False
#     for nodeCount in item.changeList:
#
#         if minNodes1 < abs(nodeCount) < maxNodes1:
#             return True
#     return False
#

def getFilesIntoCollection():
    temporaryDirectory = r"./tmpSplitLogs"
    if os.path.exists(temporaryDirectory):
        shutil.rmtree(temporaryDirectory)
    zippedDir = directoryName
    zippedList = Path(zippedDir).glob('*.zip')
    for zipped in zippedList:
        with zipfile.ZipFile(zipped, 'r') as zip_ref:
            zip_ref.extractall(temporaryDirectory)

    x = 1
    logSet = 0
    log = []

    # theOpenFile = open(r"F:\leela\github\position-tester\logs\SF10_10M.log")

    logList = Path(temporaryDirectory).glob('*.log')
    for file in logList:
        theOpenFile = open(file)
        for line in theOpenFile:
            if line.startswith("#"):
                logSet += 1
                print(logSet)
                continue
            if line.startswith("result, logSet"):
                continue
            if len(line) > 2:
                x += 1
                log.append(PositionTesterLogItem(line, logSet))
        theOpenFile.close()
    global my_collection
    my_collection = Enumerable(log)


def netField(x):
    return x.network


def main():
    getFilesIntoCollection()
    sumNodes = 0
    correct = 0
    print(my_collection.count())
    # try filtering out the easy finds < 100 that are always in agreement

    sets = my_collection.distinct(netField).select(netField).to_list()
    header = []
    for setName in sets:
        maxNodesUsed = my_collection.select(lambda x: x.nodesUsed).max()
        set = my_collection.where(lambda x: x.network == setName)
        if set.count() == 0:
            continue
        row = []
        # strip long network name down to just the number
        if "weights_" in setName:
            setName = re.search("[0-9]{3,}", setName).group(0)

        row.append(setName)
        checkAgreedAtNodes = 64
        agreeAtCount = 0
        while maxNodesUsed > checkAgreedAtNodes:
            if len(header) == 0 or checkAgreedAtNodes > header[-1]:
                header.append(checkAgreedAtNodes)
            agreeAtCount = set.where(lambda x: x.isAgreedAt(checkAgreedAtNodes) == True).count()
            row.append('{:.{prec}f}'.format(agreeAtCount / set.count() * 100, prec=2))
            checkAgreedAtNodes *= 2
        # is in 2nd but not in 1
        in2ndset = set.where(lambda x: x.pvs[1][1] in x.iccf)
        in2nd = in2ndset.count() - in2ndset.where(lambda x: x.pvs[0][1] in x.iccf).count()
        top2 = agreeAtCount + in2nd
        row.append('{:.{prec}f}'.format(top2 / set.count() * 100, prec=2))
        # is in 3rd but not in 1 or 2
        in3rdset = set.where(lambda x: x.pvs[2][1] in x.iccf)
        in3rd = in3rdset.count() - in3rdset.where(lambda x: x.pvs[0][1] in x.iccf).count()
        in3rd -= in3rdset.where(lambda x: x.pvs[1][1] in x.iccf).count()

        top3 = (agreeAtCount + in2nd + in3rd) / set.count() * 100
        row.append('{:.{prec}f}'.format(top3, prec=2))
        print(re.sub("[\[\]\']", '', row.__str__()))
        # prepend network at end so that I am able to compare and pick bigest test even if not same size

    header.insert(0, "net")
    header.append("top2")
    header.append("top3")
    print(re.sub("[\[\]\']", '', header.__str__()))
    # print(my_collection.first().__dict__)


def selectionExamples():
    chosenAt1K = my_collection.where(lambda x: x.isAgreedAt(EngNumber('1k')) == True)
    chosenAt1kButFinalLostAfter6k = chosenAt1K.where(lambda x: x.changeList[-1] > EngNumber('6k'))
    foundOnce = my_collection.where(lambda x: x.changeCount > 0)
    policyAgree = foundOnce.where(lambda x: x.changeList[1] <= 6)
    totalCount = my_collection.count()
    percentAgreedOnce = foundOnce.count() / totalCount
    policyLoses = policyAgree.where(lambda x: x.changeCount > 1)
    policyLostBetween10and50 = policyAgree.where(lambda x: Enumerable(x.changeList).any(lambda z: -10 >= z >= -50))


if __name__ == "__main__":
    main()
