import re
import json
import csv
from py_linq import Enumerable
from engineering_notation import EngNumber

fullPath = r"F:\leela\github\position-tester\ignored\Dan's testing\Log2.log"
my_collection = Enumerable()


class ChangeItem:
    def __init__(self, nodeCount, move, eval):
        self.nodeCount = int(nodeCount.strip("[").strip("]"))
        self.move = move
        self.eval = int(eval.strip("[").strip("]"))


class PositionTesterLogItem:
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
        if abs(lastEntry) <= targetNodeCount:
            return lastEntry > 0
        firstEntry = self.changeList[0]
        # targetNodeCount = 10; if 20 > 10 then it was first found later return False
        if abs(firstEntry) > targetNodeCount:
            return False
        tmpResult = False
        for nodeCount in self.changeList:
            if targetNodeCount >= abs(nodeCount):
                tmpResult = nodeCount > 0
            else:
                return tmpResult
        return False


def saveSlice(set, centered, count):
    # create name
    # example: "sliceOf-SF10_10M-1M-20k"

    fName = fullPath.split("\\")[-1].split(".")[0]
    name = f"sliceOf-{fName}-{centered},{count}"
    # handle exists
    # todo for now just overwrite
    # os.path.exists(weightPath + network):
    file = open(name, "w")
    file.write(json.dumps(set.select(lambda x: x.positionId).to_list()))
    file.close()


def changedInRange(item: PositionTesterLogItem, minNodes1: int, maxNodes1: int) -> bool:
    # last entry in change list is less than min nodes
    if minNodes1 > abs(item.changeList[-1]):
        return False
    # first entry in changeList > maxNodes
    if maxNodes1 < abs(item.changeList[0]):
        return False
    for nodeCount in item.changeList:

        if minNodes1 < abs(nodeCount) < maxNodes1:
            return True
    return False


def main():
    x = 1
    logSet = 0
    log = []
    global my_collection
    # theOpenFile = open(r"F:\leela\github\position-tester\logs\SF10_10M.log")
    theOpenFile = open(fullPath)
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
    my_collection = Enumerable(log)
    sumNodes = 0
    correct = 0
    print(my_collection.count())
    # try filtering out the easy finds < 100 that are always in agreement
    sets = []

    print(my_collection.first().__dict__)

    # sets are 2,4,6,8

    rows = []
    for i in range(35):
        rows.append([])

    rows[0].append("pieces")
    for pieces in range(7, 32):
        rows[pieces - 5].append(pieces)
    totalRow = 32 - 5 + 1
    rows[totalRow].append("Total")
    for setN in [2, 4, 6, 8]:
        # print the columns
        subset = my_collection.where(lambda x: x.logSet == setN)
        rows[0].append(subset.first().network)
        rows[0].append(subset.first().network)
        setAgree = subset.where(lambda x: x.agree == 1).count() / subset.count()
        for pieces in range(7, 32):
            piecesSet = subset.where(lambda x: x.pieces == pieces)

            piecesAgree = piecesSet.where(lambda x: x.agree == 1).count() / piecesSet.count()
            rows[pieces - 5].append(piecesSet.count())
            rows[pieces - 5].append(piecesAgree)

        rows[totalRow].append(setAgree)
    with open('jjosh.csv', "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(rows)


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
