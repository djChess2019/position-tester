import sys
import os
import numpy as np
import json
from runTactics import *
# TODO make proper options6
# TODO add nodes counter to log
# TODO should add target file to log

# NOTE: --history-fill=always is hard coded - no need for having it set in .json
params = json.load(open(jsonFileName))


logFile = open(logFileName, "a")
appendingOut = os.path.exists(outFileName)
outFile = open(outFileName,"a")


# set up command and paths from the json file, removing them as you go
params = json.load(open(jsonFileName))
weightPath = params["weights_path"]


del params["Lc0"]
nodes = None
if "nodes" in params:
	nodes = params["nodes"]
	del params["nodes"]
else:
	
	time = params["time"]
	del params["time"]

if not appendingOut:  # write a header if this is a new output file
	if nodes == None:
		outFile.write("network\tmsec\tavg_nodes\tagreed\ttotal\tpercent\n")
	else:
		outFile.write("network\treq_nodes\tavg_nodes\tagreed\ttotal\tpercent\n")
	outFile.flush()
		
# get the rest of the options in lexicograph order
pkeys = sorted(list(params.keys()))
optList = []
for pkey in pkeys:
	if params[pkey] == "":
		optList.append("--" + pkey)
	else: 
		optList.append("--" + pkey + "=" + str(params[pkey]))
optString = " ".join(optList)

weights = []
of = open(netsFileName)
for line in of:
	if len(line) > 2 and not line.startswith("#"):
		netw = line.strip()
		if not os.path.exists(weightPath + netw):
			sys.stderr.write("weight file not found: " + weightPath + netw + "\n")
			sys.exit(1)
		weights.append(netw)
of.close()



################################################################################
##########  main  ##############################################################
################################################################################
runTot = len(weights)
runNum = 1
for weight in weights:  # loop over network weights, running problem set for each
	
	if nodes == None:
		appendix = str(time) + " msec"
	else:
		appendix = str(nodes) + " nodes"

	sys.stdout.write("\nRun " + str(runNum) + " of " + str(runTot) + ": " + weight + ", " + appendix + "\n")
	sys.stdout.flush()
	agreed, total, nodesUsed = runTactics(epdPath, logFile, lc0_cmd, optString, weightPath, weight, nodeNum=nodes)		
	outv = [weight,str(nodes), str(int(round(np.mean(nodesUsed)))), str(agreed),str(total),"%.3f" % ((100.0*agreed)/total)]
	outFile.write("\t".join(outv) + "\n")
	outFile.flush()
	sys.stdout.write("\n\n")
	runNum += 1

logFile.close()
outFile.close()
