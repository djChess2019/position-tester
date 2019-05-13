# file with a simple list of networks to test, 1 per line. path taken from json
netsFileName = "sampleNetworkList.txt"
# configuration file for paths and Leela parameters
jsonFileName = "sampleJsonFile.json"
# the output file will have a bare bones summary of parameters and success rate
outFileName = "sampleResults.txt"
# the log file will contain a simple summary of failed problems
logFileName = "sample.log"
#do you even want a progress indicator
noisy = True
progressInterval = 5
#how often to write out the the log file
logBuffer = 1000
# NOTE: --history-fill=always is hard coded - no need for having it set in .json
# this was a json file, now I'm just setting this up in python.
