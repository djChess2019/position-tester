# position-tester
Prepare a set of positions and see how well your chess engine of choice performs. 

#### Data Source
ICCF data: GM correspondence chess positions

#### Input
1. List of nets to test
2. Configuration file (JSON or YAML?)
   * Positions file to use
   * Filepath to engine
   * Filepath to weights
   * Engine settings (nodes, threads, minibatch-size, etc.)
3. Filename for results output
4. Filename for log output

#### Output
1. Results summary
2. Detailed log for each position
