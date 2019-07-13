class ChangeItem:
    def __init__(self, nodeCount, move, eval):
        # the strip is here so that the line input can be split(",") leaving list
        self.nodeCount = int(nodeCount.strip("[").strip("]"))
        self.move = move
        self.eval = int(eval.strip("[").strip("]"))
