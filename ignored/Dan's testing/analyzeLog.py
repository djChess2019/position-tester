import re
import json
from py_linq import Enumerable
from engineering_notation import EngNumber

fullPath = r"F:\leela\github\position-tester\logs\SuFiNet_113k_100kn.log"
my_collection = Enumerable()


class PositionTesterLogItem:
    def __init__(self, line1: str, logNu: int):
        inputList = json.loads(line1)
        self.agree, self.iccf, self.nodesUsed, \
        self.positionId, self.toMove, self.pieces, \
        self.network, = inputList[0:7]
        self.pvs = [inputList[7:9], inputList[9:11], inputList[11:13]]

        self.changeCount = inputList[14]
        self.changeList = inputList[15]
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

    for setNumber in range(2, logSet + 1):
        sets.append(my_collection.where(lambda x: x.logSet == setNumber))
        # set2 = list(filter(lambda y: 300 > y.nodesUsed > 20 , thisSet))
    # center on 3000 nodes
    # make a selection centered on 3k
    # force agree % to match that of the set selected from remove from farthrest abs() from center.
    # repeat for each set union of unique positions choose those positions with most entries
    # combine and see how many active non repeating positions there are. If to many do it again repeating with smaller offset.

    print(my_collection.first().__dict__)

    # q = my_collection.where(lambda y: y.changeCount > 0 ).select(lambda x: (x.positionId, x.changeList[-1]))
    q = my_collection.where(lambda y: y.changeCount > 0)  # get rid of never found positions
    totalCount = my_collection.count()
    # as stockfish multiplier set to 1 it makes a way for no code changes
    # sfx = 1000
    sfx = 1
    for goalPositionCount in [2000, 5000, 10000, 20000]:
        print("node/move center, exact pos count, offset, %using slice, %for all 113k at targetNodes + offset")
        offset = 100 * sfx
        CenteredOn = 10 * sfx
        # for node counts
        for CenteredOn in range(2000 * sfx, 8000 * sfx, 500 * sfx):

            while True:
                minNodes = CenteredOn - offset
                maxNodes = CenteredOn + offset
                sliceSet = q.where(lambda positionLogItem: changedInRange(positionLogItem, minNodes, maxNodes))
                countPs = sliceSet.count()
                # print(f"{CenteredOn}, {countPs}, {offset}")
                if countPs > goalPositionCount:
                    agreeCount = sliceSet.where(
                        lambda x: x.isAgreedAt(CenteredOn + offset)).count()

                    agreeOn113kset = my_collection.where(
                        lambda x: x.isAgreedAt(CenteredOn + offset)).count()
                    outLine = (f'{EngNumber(CenteredOn)}, {EngNumber(countPs)}, {EngNumber(offset)},'
                               f' {round(agreeCount / countPs, 5)}, '
                               f'{round(agreeOn113kset / totalCount, 5)}')
                    print(outLine)
                    # saveSlice(sliceSet, CenteredOn, countPs)
                    break
                offset += 10 * sfx
                if offset > 12000 * sfx:
                    break


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
