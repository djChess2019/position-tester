import re
import json
from py_linq import Enumerable


class PythonTesterLogItem:
    def __init__(self, line1: str, logNu: int):
        lst = json.loads(line1)
        self.agree, self.iccf, self.nodesUsed, \
        self.positionId, self.toMove, self.pieces, \
        self.network, = lst[0:7]
        self.pvs = [lst[7:9], lst[9:11], lst[11:13]]

        self.changeCount = lst[14]
        self.changeList = lst[15]
        self.logSet = logNu


def changedInRange(item: PythonTesterLogItem, minNodes1: int, maxNodes1: int) -> bool:
    # last entry in change list is less than min nodes
    if minNodes >= abs(item.changeList[-1]):
        return False
    # first entry in changeList > maxNodes
    if maxNodes <= abs(item.changeList[0]):
        return False
    for nodeCount in item.changeList:

        if minNodes1 < abs(nodeCount) < maxNodes1:
            return True
    return False


def isAgreedAt(item: PythonTesterLogItem, targetNodeCount: int) -> bool:
    if item.changeCount == 0:
        return False
    lastEntry = item.changeList[-1]
    # example entries [ 20, -100]
    # targetNodeCount = 300; if |-100| < 300 return (-100 > 0)  so return false
    if abs(lastEntry) < targetNodeCount:
        return lastEntry > 0
    firstEntry = item.changeList[-1]
    # targetNodeCount = 10; if 20 > 10 then it was first found later return False
    if abs(firstEntry) > targetNodeCount:
        return False
    tmpResult = False
    for nodeCount in item.changeList:
        if targetNodeCount <= abs(nodeCount):
            tmpResult = nodeCount > 0
        else:
            return tmpResult
    return False


x = 1
logSet = 0
log = []
# theOpenFile = open(r"F:\leela\github\position-tester\logs\SF10_10M.log")
theOpenFile = open(r"F:\leela\github\position-tester\logs\SuFiNet_10k.log")
for line in theOpenFile:
    if line.startswith("#"):
        logSet += 1
        print(logSet)
        continue
    if line.startswith("result, logSet"):
        continue
    if len(line) > 2:
        x += 1
        log.append(PythonTesterLogItem(line, logSet))
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
for goalPositionCount in [20000, 10000, 5000, 1000]:
    print("node/move center, exact pos count, offset, %using slice, %for all 113k at targetNodes + offset")
    offset = 10
    CenteredOn = 500
    while CenteredOn < 6000:

        while True:
            minNodes = CenteredOn - offset
            maxNodes = CenteredOn + offset
            k3Set = q.where(lambda positionLogItem: changedInRange(positionLogItem, minNodes, maxNodes))
            countPs = k3Set.count()

            if countPs > goalPositionCount:
                agreeCount = k3Set.where(
                    lambda positionLogItem: isAgreedAt(positionLogItem, CenteredOn + offset)).count()
                agreeOn113kset = my_collection.where(
                    lambda positionLogItem: isAgreedAt(positionLogItem, CenteredOn + offset)).count()
                print(f"{CenteredOn}, {countPs}, {offset}, {round(agreeCount / countPs, 5)}, {round(
                    agreeOn113kset / totalCount, 5)}")
                break
            offset += 10
            if offset > 6000:
                break
        CenteredOn += 500

print(len(sets))
