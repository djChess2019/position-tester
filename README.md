# position-tester
Test your chess engines against different sets of positions for a cheap measure of relative strength.

### Data Source
ICCF data: GM correspondence chess positions

### Prerequisites
1. Python and a couple libraries
2. Chess engine(s) and weights files (if applicable)

### Position Testing files
1. position-tester.py (Python program)
2. Position set (text file with FENs)
3. Configuration file (JSON file with engine path and settings)
4. Networks list (text file with the list of nets to test)

### Program Input Syntax
```
python position-tester.py NetworksList.txt ConfigurationSettings.json OutputSummary.txt OuputLog.log
```

### Output
1. Results summary
2. Detailed log for each position

### Sample NetworksList.txt
```
weights_run1_11248.pb.gz
weights_run1_22154.pb.gz
weights_run2_32930.pb.gz
weights_run1_42482.pb.gz
weights_run2_50778.pb.gz
```

### Sample ConfigurationSettings.json
The parameters `EPD` and `enginePath` are mandatory as is `weights_path` for NN engines. Other parameters are optional.
```
{
	"EPD" : "PositionSet.txt",
	"enginePath" : "C:/Users/Computer/Downloads/lc0-v0.21.2-windows-cuda/lc0.exe",
	"weights_path" : "C:/Users/Computer/Downloads/lc0-v0.21.2-windows-cuda/",
	"threads" : 2,
	"minibatchsize" : 256,
	"backend" : "cudnn-fp16",
	"nodes" : 10000
}
```

### Sample Position Set file
```
1b1n2B1/3k3p/p4pp1/1p6/1B6/P6P/1P3PP1/5K2 b - - bm Nc6 ; 61485
1B1q1rk1/pQ2pp1p/4bbp1/3p4/3P4/2r1P1P1/P4PBP/R4RK1 w - - bm Rfb1 ; 8
1b1qr1k1/1p1b1pp1/5n1p/1PP1p3/3p4/3P1NP1/r2B1PBP/1R1QR1K1 w - - bm Qc1 ; 14
1b1qr1k1/1p1r2p1/p2pbp1p/P3nN2/2P1P1P1/1PB4P/5QB1/R4R1K b - - bm Bc7 ; 61490
1b1qr1k1/1p3pp1/5n1p/1PP2b2/3pP3/1R3NP1/r2B1PBP/2Q1R1K1 b - - bm Bxe4 ; 61492
1b1r1rk1/1b3p2/8/Ppp1q1pp/4P3/P2B2N1/2Q2PPP/3R1R1K w - - bm Qe2 ; 27
1b1r1rk1/pb1nqp2/2p4p/1p2p1pn/3PP3/P2B1NB1/1PQ1NPPP/3R1RK1 w - - bm b4 ; 28
1b1r2k1/1b2q2p/p5p1/2p2p2/B1P5/1Q3P1P/PP2NRP1/6K1 w - - bm Kf1 ; 30
1b1r2k1/1b5p/p5p1/2p2p2/B1P4q/5P1P/PP2NRP1/3Q2K1 w - - bm Qb3 ; 32
1b1r2k1/1p5p/3q2pB/Qp1pNp2/P4P2/4n2P/6P1/1R5K b - - bm Nc4 ; 61512
1b1r2k1/1p5p/3q2pB/Qp1pNp2/P4P2/4n2P/6P1/3R3K w - - bm Rb1 ; 45
1b1r2k1/1p5p/3q2pB/Qp1pNp2/P4P2/7P/2n3P1/R6K w - - bm Rd1 ; 47
1B1R4/7k/5pp1/p4r2/Pb3P1p/1B4nP/7K/8 w - - bm Rd7+ ; 66
[...]
```

### Sample Output Summary
```
network		req_nodes	avg_nodes	agreed	total	percent	avg_1st_agree
weights_run1_11248.pb.gz	100	110	38356	80075	47.900	10.331
weights_run1_22154.pb.gz	100	110	34040	80075	42.510	9.927
weights_run2_32930.pb.gz	100	110	38653	80075	48.271	10.990
weights_run1_42482.pb.gz	100	110	40092	80075	50.068	11.292
weights_run2_50778.pb.gz	100	111	34253	80075	42.776	12.240
```

### Sample Ouput Log
```
#### agree, iccf_moves, nodesUsed, position_id, toPlay,                  pieces Count, weight, mpv 1 move, mpv 1 eval
#### mpv 2 move, mpv 2 eval,  mpv 3 move ; mpv3 eval                 probability (P), count of agree List, agree List
1, gxf4, 10006, 349, W, 28, weights_run2_32930.pb.gz, 0.1507, gxf4, 38, Bh3, 32, Rd6, -17, 2, [[-3,  Bh3, 52], [7,  gxf4, 54]]
1, Nc4, 10045, 629, W, 28, weights_run2_32930.pb.gz, 0.1901, Nc4, 23, fxe5, -28, Kh2, -115, 3, [[4,  Nc4, 17], [-9,  Kh2, -53], [22,  Nc4, 2]]
1, Bf4, 10154, 894, W, 28, weights_run2_32930.pb.gz, 0.29, Bf4, 48, Bd3, 48, Re1, 40, 1, [[2,  Bf4, 55]]
1, Rac1, 10022, 1382, W, 28, weights_run2_32930.pb.gz, 0.1614, Rac1, 43, a3, 24, Nd4, 21, 3, [[3,  Rac1, 32], [-6,  a3, 35], [11,  Rac1, 30]]
1, d5, 10021, 1458, W, 28, weights_run2_32930.pb.gz, 0.153, d5, 33, Re1, 26, h4, 12, 1, [[3,  d5, 49]]
0, Ne3, 10302, 2620, W, 28, weights_run2_32930.pb.gz, 0.0934, Bd1, 71, Ne3, 66, Nc3, 62, 7, [[-4,  Bd1, 47], [141,  Ne3, 62], [-211,  Bd1, 69], [325,  Ne3, 61], [-9376,  Bd1, 71], [9833,  Ne3, 66], [-10302,  Bd1, 71]]
1, Nde3, 10251, 2724, W, 28, weights_run2_32930.pb.gz, 0.2795, Nde3, 229, Qf2, 212, Nf2, 160, 1, [[2,  Nde3, 254]]
[...]
```
