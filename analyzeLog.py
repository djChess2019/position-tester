import re


class PythonTesterLogItem:
    def __init__(self, line: str):
        splitIt = line.split(",")
        self.agree = int(splitIt[0])
        self.iccf = splitIt[1]
        self.nodesUsed = int(splitIt[2])
        self.positionId = int(splitIt[3])
        self.toMove = splitIt[4]
        multiPvs = re.findall('\".*?\"', str(splitIt[5:11]))
        self.multipv[0] = [multiPvs[1], int(multiPvs[2])]
        self.multipv[1] = [multiPvs[3], int(multiPvs[4])]
        self.multipv[2] = [multiPvs[5], int(multiPvs[6])]
        self.earlyFinds = splitIt[11]
        self.piecesCount = int(splitIt[12])
        self.network = int(splitIt[13])


inStr = '1, "Bd6", 160, 2, "W", [["Bd6", "108"], ["Bd6", "108"], ["Bd6", "108"]],[3], 17, 41800'
d = PythonTesterLogItem(inStr)
print(d)
