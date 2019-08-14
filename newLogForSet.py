# given an existing log and a set
# this will trim the log to only those lines where the positionID exists in the set.
# example command line
# newLogForSet.py mylog.log newset.txt
import sys
import os
import numpy

logfileN = sys.argv[1]
newSetN = sys.argv[2]
fileNotFound = False
if not os.path.exists(logfileN):
    print(f"log file:{logfileN} wasn't found")
    fileNotFound = True
if not os.path.exists(newSetN):
    print(f"log file:{newSetN} wasn't found")
    fileNotFound = True
if fileNotFound:
    exit(-1)

logfile = open(logfileN)
newSet = open(newSetN)
outfileN = logfileN.split("\\")[-1].split(".")[0]
outfileN = outfileN + "---" + newSetN.split("\\")[-1].split(".")[0] + ".log"
outfile = open(outfileN, "a")
newSetPositions = []
for line in newSet:
    if len(line) > 2 and not line.startswith("#"):
        id = line.split(";")[1]
        id = int(id.replace(" ", "").rstrip())
        newSetPositions.append(id)
newSet.close()
newSetPositions = numpy.sort(newSetPositions)
for line in logfile:
    if len(line) > 2 and not line.startswith("#"):
        positionID = int(line.split(",")[3])
        if newSetPositions[numpy.searchsorted(newSetPositions, positionID)] == positionID:
            outfile.write(line)
