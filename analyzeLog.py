import re


class PythonTesterLogItem:
    def __init__(self, line: str, logSet):
        splitIt = line.split(",")
        self.agree = int(splitIt[0])
        self.iccf = splitIt[1]
        self.nodesUsed = int(splitIt[2])
        self.positionId = int(splitIt[3])
        self.toMove = splitIt[4]
        # multiPvs = re.findall('\".*?\"', str(splitIt[5:11]))
        # self.multipv = []
        # self.multipv.append([multiPvs[0].strip('"'), int(multiPvs[1].strip('"'))])
        # self.multipv.append([multiPvs[2].strip('"'), int(multiPvs[3].strip('"'))])
        # self.multipv.append([multiPvs[4].strip('"'), int(multiPvs[5].strip('"'))])
        self.logSet = logSet


x = 1
logSet = 0
log = []
theOpenFile = open(r"F:\leela\logs\SuFiCandidates\SuFiCandidates.log")
for line in theOpenFile:
    if line.startswith("#"):
        logSet += 1

        continue
    if line.startswith("result"):
        continue
    if len(line) > 2:
        x += 1
        log.append(PythonTesterLogItem(line, logSet))
theOpenFile.close()
sumNodes = 0
correct = 0
# try filtering out the easy finds < 100 that are always in agreement
for setNumber in range(2, logSet + 1):

    set3 = list(filter(lambda y: y.logSet == setNumber, log))
    # set2 = list(filter(lambda y: 300 > y.nodesUsed > 20 , set3))

    for i in set3:
        sumNodes += i.nodesUsed
        if i.nodesUsed < 6400:
            correct += i.agree
    print(sumNodes / correct, correct / 5000)
    sumNodes = 0
    correct = 0
