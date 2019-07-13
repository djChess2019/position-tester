class PositionTesterLogItem:

    def __init__(self, line1: str, logNu: int):
        inputList = line1.strip('\n').split(", ")
        self.agree = int(inputList[0])
        self.iccf = str(inputList[1])
        self.nodesUsed = int(inputList[2])
        self.positionId = int(inputList[3])
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

    def _cmp_key(self):
        # net = int(re.sub('[^0-9]', '', self.network))
        tup = (self.positionId, self.network)
        return tup

    def __hash__(self):
        return hash(self._cmp_key())

    def __eq__(self, other):
        return self._cmp_key() == other._cmp_key()

    def __lt__(self, other):
        return self._cmp_key() < other._cmp_key()

    def isAgreedAt(self, targetNodeCount: int) -> bool:
        # must retest with this logItem format.
        return 1

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
